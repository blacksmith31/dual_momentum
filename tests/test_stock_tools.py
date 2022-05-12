import pytest
import json
import utils.stock_tools as st

with open("config.json", 'r') as j:
    cfg = json.load(j)

symbol_file = cfg["symbol_file"]
hist_path = cfg["data_folder"]
period_type = cfg["period_type"]
period = cfg["period"]
ema = cfg["ema"]
roc = cfg["roc"]
cutoff = cfg["cutoff"]
top_n = cfg["top_n"]
count = cfg["state"]["count"]

def test_read_stock_list_type():
    assert(type(st.read_stock_list(symbol_file)) == list)
