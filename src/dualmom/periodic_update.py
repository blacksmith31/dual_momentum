""""
read in config file
    symbols list file path
    recent data save folder
    ema period
    roc period
    cutoff value
    max_rows to keep
download days since per config
calc indicators
racknstack 1 row
top_20 for rack
update top_20 history file
get +/-
send email?
"""

import json
import datetime
from tabulate import tabulate
from utils import stock_tools as st
import utils.gmail_tool as gt

with open("../../config.json", 'r') as j:
    cfg = json.load(j)

symbol_file = cfg["symbol_file"]
hist_path = cfg["data_folder"]
period_type = cfg["strategy"]["period_type"]
period = cfg["strategy"]["period"]
ema = cfg["strategy"]["ema"]
roc = cfg["strategy"]["roc"]
cutoff = cfg["strategy"]["cutoff"]
top_n = cfg["strategy"]["top_n"]
count = cfg["state"]["count"]

symb_count = count * 100

hist_days = (ema + roc) * 2
hist_start = datetime.datetime.today() - datetime.timedelta(days=hist_days)

def main():
    symbols = st.read_stock_list(symbol_file)
    symbols = symbols[:symb_count]
    nominal_col_count = len(symbols)

    # for symbol in symbols:
    #     # print(f"symbol: {symbol}")
    #     st.download_symbol_data_since(symbol, hist_start, save_path=hist_path)

    st.apply_sroc_indicators(hist_path, ema, roc, symbols)

    today = str(datetime.datetime.today().date())

    rack_series = st.periodic_rack_n_stack(hist_path, "roc", symbols)
    sorted_rack = st.sort_rack(rack_series)
    loggable_fullr = st.format_sorted_rack(sorted_rack, today)
    # st.update_record(loggable_fullr, "periodic_data/rack_hist.csv", 20, nominal_col_count)

    previous_df = st.read_saved("../../periodic_data/previous.csv", top_n)
    # print(previous_df)
    prev_html = previous_df.to_html()

    previous_df_mod = previous_df.droplevel(level=0)
    prev_symb_list = previous_df_mod.loc["symbol"].to_list()
    print("Previous:")
    print(prev_symb_list)

    top_filter = st.filter_vals_max(rack_series, 20, cutoff)
    loggable_topr = st.format_sorted_rack(top_filter, today)
    # print(loggable_topr)
    st.update_record(loggable_topr, "../../periodic_data/previous.csv", 1, top_n)
    curr_html = loggable_topr.to_html()

    curr_df_mod = loggable_topr.droplevel(level=0)
    curr_symb_list = curr_df_mod.loc["symbol"].tolist()
    print("Current:")
    print(curr_symb_list)
    drop_symbs = [symb for symb in prev_symb_list if symb not in curr_symb_list]
    print("Drop:")
    print(drop_symbs)
    drop_html = tabulate([drop_symbs], tablefmt='html')
    add_symbs = [symb for symb in curr_symb_list if symb not in prev_symb_list]
    print("Add:")
    print(add_symbs)
    add_html = tabulate([add_symbs], tablefmt='html')

    html = "<h1>Current</h1>" + prev_html + "<br><h2>Drop</h2><br>" + drop_html + "<br><h2>Add</h2><br>" + add_html + "<br><h1>New</h1><br>" + curr_html
    subject = f"Dual Momentum Update - {today}"
    gt.send_mail(subject, html)

    with open("test_table.html", 'w') as h:
        h.write(html)

if __name__ == "__main__":
    main()
