from datetime import datetime, timedelta
from tda.client import Client
import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import btalib

class Strategy:

    def __init__(self, config: dict, client: Client) -> None:
        self.period_type = config["strategy"]["period_type"]
        self.period = config["strategy"]["period"]
        self.ema = config["strategy"]["ema"]
        self.roc = config["strategy"]["roc"]
        self.cutoff = config["strategy"]["cutoff"]
        self.top_n = config["strategy"]["top_n"]
        self.client = client
        self.start_date = self._get_start_date()

    def get_symbol_score(self, symbol: str) -> float:
        hist_data = self.download_data_since(symbol)
        if not hist_data.empty:
            indicated_data = self.apply_indicators(symbol, hist_data)
            last_row = indicated_data.tail(1)
            score = round(float(last_row["roc"]), 1)
        else:
            score = 0
        return score

    def download_data_since(self, symbol: str) -> pd.DataFrame:
        resp = self.client.get_price_history_every_day(symbol, start_datetime=self.start_date)
        if resp.status_code == 200:
            history = resp.json()
            hist = pd.json_normalize(history["candles"])
            try:
                hist.columns = ["Open", "High", "Low", "Close", "Volume", "Date"]
                hist["Date"] = pd.to_datetime(hist["Date"], unit='ms')
                hist.set_index("Date", inplace=True)
                hist.sort_values(by="Date", ascending=True, inplace=True)
            except ValueError as e:
                print(f"Symbol {symbol} failed")
                print(e)
                # return None
            
            return hist
        else:
            print(f"Bad response: {resp.status_code} - for symbol {symbol}")
            return None

    def apply_indicators(self, symbol: str, hist_data: pd.DataFrame) -> pd.DataFrame:
        try:
            ema = btalib.ema(hist_data, period=self.ema)
            ema_col = ema.df["ema"]
            hist_data = hist_data.join(ema_col)
        except:
            print(f"EMA fail on symbol: {symbol}")
            raise
        # Generate and attach SROC indicator, this is the ROC indicator applied to the EMA
        # Formula is = (ema[0] - ema[lookback]) / (ema[lookback]) * 100
        try:
            sroc = btalib.roc(hist_data.ema, period=self.roc)
            hist_data = hist_data.join(sroc.df["roc"])
        except:
            print(f"SROC fail on symbol: {symbol}")
            raise
        return hist_data

    def _get_start_date(self):
        hist_days = (self.ema + self.roc) * 2
        hist_start = datetime.today() - timedelta(days=hist_days)
        return hist_start