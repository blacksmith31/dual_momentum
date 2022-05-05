import csv
from typing import Callable, List, Tuple
import atexit
from numpy import True_
# import json
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import tda
from tda.client import Client
import time
import os
import btalib
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

# TDA client params
API_KEY = os.environ.get("tda_api_key")
REDIRECT_URI = "https://localhost"
TOKEN_PATH = "token.json"

"""
Reference for Period types and periods

class PriceHistory:
    class PeriodType(Enum):
        DAY = 'day'
        MONTH = 'month'
        YEAR = 'year'
        YEAR_TO_DATE = 'ytd'

    class Period(Enum):
        # Daily
        ONE_DAY = 1
        TWO_DAYS = 2
        THREE_DAYS = 3
        FOUR_DAYS = 4
        FIVE_DAYS = 5
        TEN_DAYS = 10

        # Monthly
        ONE_MONTH = 1
        TWO_MONTHS = 2
        THREE_MONTHS = 3
        SIX_MONTHS = 6

        # Year
        ONE_YEAR = 1
        TWO_YEARS = 2
        THREE_YEARS = 3
        FIVE_YEARS = 5
        TEN_YEARS = 10
        FIFTEEN_YEARS = 15
        TWENTY_YEARS = 20

        # Year to date
        YEAR_TO_DATE = 1
"""

def read_stock_list(path: str) -> List:
    # data = []
    with open(path, 'r') as f:
        reader = csv.reader(f)
        # for row in reader:
        #     data.append(row[0])
        data = [row[0] for row in reader]
    return data

def make_webdriver():
    # Import selenium here because it's slow to import
    from selenium import webdriver

    driver = webdriver.Firefox()
    atexit.register(lambda: driver.quit())
    return driver

client = tda.auth.easy_client(
    API_KEY,
    REDIRECT_URI,
    TOKEN_PATH,
    make_webdriver)

def download_symbols_data(symbols: List, path: str, period_type: Client.PriceHistory.PeriodType, timeperiod: Client.PriceHistory.Period, client: Client=client):
    filelist = os.listdir(path)
    
    for symb in symbols:
        hist_exists = False
        for filename in filelist:
            if symb in filename:
                hist_exists = True
                break
        if not hist_exists:
            resp = client.get_price_history(symb,
                    period_type=period_type,
                    period=timeperiod,
                    frequency_type=Client.PriceHistory.FrequencyType.DAILY,
                    frequency=Client.PriceHistory.Frequency.DAILY)
            if resp.status_code == 200:
                history = resp.json()
                hist = pd.json_normalize(history["candles"])
                hist.columns = ["Open", "High", "Low", "Close", "Volume", "Date"]
                hist["Date"] = pd.to_datetime(hist["Date"], unit='ms')
                hist.set_index("Date", inplace=True)
                hist.sort_values(by="Date", ascending=True, inplace=True)
                file_path = path + symb + '.csv'
                hist.to_csv(path_or_buf=file_path)
                print("History File for %s saved" % symb)
            else:
                print("Bad response: %d - for symbol %s" % (resp.status_code, symb))
            time.sleep(1)
        else:
            print("File for symbol %s exists, not updated" % symb)

def download_symbol_data(symbol: str, path: str, period_type: str, timeperiod: int, client: Client=client):

    resp = client.get_price_history(symbol,
            period_type=period_type,
            period=timeperiod,
            frequency_type=Client.PriceHistory.FrequencyType.DAILY,
            frequency=Client.PriceHistory.Frequency.DAILY)
    if resp.status_code == 200:
        history = resp.json()
        hist = pd.json_normalize(history["candles"])
        hist.columns = ["Open", "High", "Low", "Close", "Volume", "Date"]
        hist["Date"] = pd.to_datetime(hist["Date"], unit='ms')
        hist.set_index("Date", inplace=True)
        hist.sort_values(by="Date", ascending=True, inplace=True)
        file_path = path + symbol + '.csv'
        hist.to_csv(path_or_buf=file_path)
        print(f"History File for {symbol} saved")
    else:
        print(f"Bad response: {resp.status_code} - for symbol {symbol}")

def download_symbol_data_since(symbol: str, recent_date, client: Client=client, save_path=None):

    resp = client.get_price_history_every_day(symbol, start_datetime=recent_date)

    if resp.status_code == 200:
        history = resp.json()
        hist = pd.json_normalize(history["candles"])
        hist.columns = ["Open", "High", "Low", "Close", "Volume", "Date"]
        hist["Date"] = pd.to_datetime(hist["Date"], unit='ms')
        hist.set_index("Date", inplace=True)
        hist.sort_values(by="Date", ascending=True, inplace=True)
        if save_path:
            filepath = f"{save_path}{symbol}.csv"
            hist.to_csv(path_or_buf=filepath)
        time.sleep(1)
        return hist
    else:
        print(f"Bad response: {resp.status_code} - for symbol {symbol}")
    

def apply_sroc_indicators(path: str, ema_period: int, roc_lookback: int, include_symbs: List):
    
    filelist = os.listdir(path)
    for name in include_symbs:
        file = f"{name}.csv"
        f = os.path.join(path, file)
        # name = file.split('.')[0]
        if os.path.isfile(f): # and not file.startswith('.') and name in include_symbs:
            # read in csv
            symb_hist = pd.read_csv(f, index_col="Date")
            # filter columns to remove any existing indicators
            symb_hist = symb_hist.filter(items=["Open", "High", "Low", "Close", "Volume"])
 
            # generate and attach EMA indicator
            try:
                ema = btalib.ema(symb_hist, period=ema_period)
                ema_col = ema.df["ema"]
                symb_hist = symb_hist.join(ema_col)
            except:
                print(f"EMA fail on symbol: {name}")
                raise
            # Generate and attach SROC indicator, this is the ROC indicator applied to the EMA
            # Formula is = (ema[0] - ema[lookback]) / (ema[lookback]) * 100
            sroc = btalib.roc(symb_hist.ema, period=roc_lookback)
            symb_hist = symb_hist.join(sroc.df["roc"])
            ind_file_path = path + file
            symb_hist.to_csv(path_or_buf=ind_file_path)

def rack_n_stack(path: str, ind_colname: str, include_symbs: List, suffix: str):
    filelist = os.listdir(path)
    for index, name in enumerate(include_symbs):
        file = f"{name}.csv"
        f = os.path.join(path, file)
        # name = file.split('.')[0]
 
        if os.path.isfile(f):
            if index == 0:
                rack_df = pd.read_csv(f)[["Date", ind_colname]]
            else:
                symb_df = pd.read_csv(f)[["Date", ind_colname]]
                rack_df = pd.merge_ordered(rack_df, symb_df, on="Date")
            rack_df = rack_df.rename(columns={ind_colname:name})
    rack_df.set_index("Date", inplace=True)
    rack_df.to_csv(f"backtest_data/rack{suffix}")
    return rack_df

def periodic_rack_n_stack(path: str, ind_colname: str, include_symbs: List):
    filelist = os.listdir(path)
    rack_dict = {}
    for file in filelist:
        f = os.path.join(path, file)
        name = file.split('.')[0]
        if os.path.isfile(f) and not file.startswith('.') and name in include_symbs:
            symb_df = pd.read_csv(f)[["Date", ind_colname]].tail(1)
            rack_dict[name] = round(float(symb_df[ind_colname]), 1)
    rack_series = pd.Series(rack_dict)
    return rack_series

def sort_rack(s: pd.Series) -> pd.Series:
    sort_vals = s.sort_values(ascending=False)
    return sort_vals

def filter_vals_cutoff(s: pd.Series, top_n: int, ind_valuecutoff: int):
    filter_vals = s.where(lambda x: x > ind_valuecutoff).dropna()
    return filter_vals

def filter_vals_max_bt(s: pd.Series, top_n: int, ind_valuecutoff: int):
    """
    FilterFunction used in the pandas apply method to get the symbol names for the top indicator values
    Args:
        s (pandas.Series): row series from the racknstack dataframe
        top_n (int): number of symbols to consider in the top
        ind_valuemin (int): min value of the indicator to be allowed in the top
    """
    index = ["top{}".format(i) for i in range(1, top_n+1)]
    sort_vals = s.sort_values(ascending=False)
    symbs = pd.Series(data=list(i if v>ind_valuecutoff else None for i, v in sort_vals.iteritems())[:top_n], index=index, name="symbol")
    return symbs

def filter_vals_max(s: pd.Series, top_n: int, ind_valuecutoff: int):
    sort_vals = s.sort_values(ascending=False).head(top_n).where(lambda x: x > ind_valuecutoff).dropna()
    return sort_vals

def get_symb_selection(df: pd.DataFrame, filter_func: Callable, top_n: int, ind_valuecutoff: int):
    """
    returns a df with a column for each place in the Top n, with the values for each date equal to the symbols that meet the criteria
    """
    df = df.apply(filter_func, axis=1, top_n=top_n, ind_valuecutoff=ind_valuecutoff).reset_index()
    df.set_index("Date", inplace=True)
    return df

def get_symb_selection_csv(path: str, filter_func: Callable, top_n: int, ind_valuecutoff: int, suffix: str):
    """
    returns a df with a column for each place in the Top n, with the values for each date equal to the symbols that meet the criteria
    """
    df = pd.read_csv(path, index_col="Date")
    df = df.apply(filter_func, axis=1, top_n=top_n, ind_valuecutoff=ind_valuecutoff).reset_index()
    df.set_index("Date", inplace=True)
    filename = f"backtest_data/symb_select_top{top_n}{suffix}" 
    df.to_csv(path_or_buf=filename)
    return df

def get_backtest_allocations(path: str, allocation: float, ind_valuecutoff: int, suffix: str, symbols: list):
    in_top = {}
    df = pd.read_csv(path, index_col="Date", keep_default_na=False)

    for index, row in df.iterrows():
        for name in row:
            if name and name not in in_top and name in symbols:
                # print(f"Name: {name}")
                in_top[name] = [int(name in list(row))*allocation for index, row in df.iterrows()]
        # break

    in_top["Date"] = [index for index, row in df.iterrows()]
    in_top_df = pd.DataFrame(in_top)
    in_top_df["Date"] = pd.to_datetime(in_top_df["Date"])

    # Filter to only the first of the month
    # in_top_df = in_top_df[in_top_df["Date"].dt.day == 1]
    # Filter to only the first of the month
    in_top_df = in_top_df.groupby(pd.DatetimeIndex(in_top_df.Date).to_period('M')).nth(0)
    # trim datetimes to dates only
    in_top_df["Date"] = in_top_df["Date"].dt.date
    in_top_df.set_index("Date", inplace=True)
    
    # add a column for the balance asset when asset allocations sum to less than 100%
    in_top_df["VBMFX"] = round(100 - in_top_df.sum(axis=1), 1) # VBMFX, FBNDX Alternate
    in_top_df = in_top_df.astype(str) + '%'
    # print(in_top_df.head(70))
    filename = f"backtest_data/allocations{suffix}"
    in_top_df.to_csv(path_or_buf=filename)
    return in_top_df

def update_top_table(new_df: pd.DataFrame):
    filelist = os.listdir("periodic_data/")
    if "top_n.csv" not in filelist:
        new_df.to_csv("periodic_data/top_n.csv", index_label=("Date", "Label"))
    else:
        old_df = pd.read_csv("periodic_data/top_n.csv", index_col="IDX")
        frames = [old_df, new_df]
        keys = ["OLD", "NEW"]
        updated = pd.concat(frames)#, keys=keys) # ignore_index=True, 
        updated.to_csv(f"periodic_data/top_n.csv", index_label="IDX")


def merge_symbol_value(top_series: pd.Series, value_series: pd.Series, date: str):
    merged = pd.merge(top_series, value_series, left_on="symbol", right_index=True)
    merged = merged.transpose(copy=True)
    merged.index.name = "Label"
    date_series = pd.Series([date, date], name="Date", index=["symbol", "value"])
    # merged = pd.concat([date_series, merged], axis=1)
    # update_top_table(merged)
    return merged


def format_sorted_rack(s: pd.Series, date):
    """
    transpse and reindex the soreted rack-n-stack series for logging or presentation
    """
    df = s.reset_index().T
    df["date"] = [date, date]
    df["label"] = ["symbol", "value"]
    df = df.set_index(["date", "label"])
    df = df.rename_axis(index={'date': None, 'label': None})
    return df

def update_record(df: pd.DataFrame, path: str, keep_recs: int, nominal_col_count: int):
    keep_rows = keep_recs * 2
    try:
        record = pd.read_csv(path, header=0, names=list(range(nominal_col_count)))
        record = pd.concat([record, df], names=["date", "label"]).tail(keep_rows)
    except FileNotFoundError:
        record = df
    
    record.to_csv(path, index_label=["date", "label"])

def read_saved(path: str, nominal_col_count):
    df = pd.read_csv(path, header=0, names=list(range(nominal_col_count)))
    return df