import csv
from typing import List
import json
import atexit
import os
import tda
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

# create tda client
client = tda.auth.easy_client(
    API_KEY,
    REDIRECT_URI,
    TOKEN_PATH,
    make_webdriver)

# Get config as dict
with open("config.json", 'r') as j:
    cfg = json.load(j)

# create strategy instance
strategy = Strategy(cfg, client)

# iterate over symbol list
# - strategy: get score
# - create symbol dataclass obj
# - save to list
symbol_file = cfg["symbol_file"]
symbol_list = read_stock_list(symbol_file)

for sym in symbol_list[:10]:
    score = strategy.get_symbol_score(sym)
    print(f"{sym} score of {score}")
# sort list by score
# strategy: get top n symbols