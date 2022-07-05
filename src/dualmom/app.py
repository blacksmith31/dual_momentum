import csv
from typing import List
import json
import atexit
import os
import tda
import time
from dotenv import load_dotenv

from utils.strategy import Strategy
from utils.symbol import Symbol

load_dotenv()

# TDA client params
API_KEY = os.environ.get("tda_api_key")
REDIRECT_URI = "https://localhost"
TOKEN_PATH = "token.json"

# HELPER FUNCTIONS

def make_webdriver():
    # Import selenium here because it's slow to import
    from selenium import webdriver

    driver = webdriver.Firefox()
    atexit.register(lambda: driver.quit())
    return driver

def read_stock_list(path: str) -> List:
    # data = []
    with open(path, 'r') as f:
        reader = csv.reader(f)
        # for row in reader:
        #     data.append(row[0])
        data = [row[0] for row in reader]
    return data

def main():

# create tda client
    client = tda.auth.easy_client(
                                    API_KEY,
                                    REDIRECT_URI,
                                    TOKEN_PATH,
                                    make_webdriver)

    # Get config as dict
    with open("config.json", 'r') as j:
        cfg = json.load(j)

    strat_cfg = cfg['strategy']
    # create strategy instance
    strategy = Strategy(strat_cfg, client)

    # iterate over symbol list
    # - strategy: get score
    # - create symbol dataclass obj
    # - save to list
    symbol_file = cfg["symbol_file"]
    symbol_list = read_stock_list(symbol_file)

    symbol_count = cfg["state"]["count"]
    sym_dtypes = []
    for sym in symbol_list[:symbol_count]:
        score = strategy.get_symbol_score(sym)
        sym_dtypes.append(Symbol(sym, score))
        time.sleep(0.5)

    sym_dtypes.sort(key=lambda x: x.score, reverse=True)

    print(sym_dtypes)
    # sort list by score
    # strategy: get top n symbols

if __name__ == "__main__":
    main()
    