from datetime import datetime, timedelta
from tda.client import Client
import pandas as pd
import btalib

class Strategy:

    def __init__(self, config: dict, client: Client) -> None:
        self.period_type = config["period_type"]
        self.period = config["period"]
        self.ema = config["ema"]
        self.roc = config["roc"]
        self.cutoff = config["cutoff"]
        self.top_n = config["top_n"]
        self.client = client

    def get_symbol_score(self, symbol: str) -> float:
        hist_data = self.download_data_since(symbol)
        indicated_data = self.apply_indicators(hist_data)
        last_row = indicated_data.tail(1)
        score = round(float(last_row["roc"]), 1)
        return score

    def download_data_since(self, symbol: str) -> pd.DataFrame:
        recent_date = self._get_start_date()
        resp = self.client.get_price_history_every_day(symbol, start_datetime=recent_date)
        if resp.status_code == 200:
            history = resp.json()
            hist = pd.json_normalize(history["candles"])
            try:
                hist.columns = ["Open", "High", "Low", "Close", "Volume", "Date"]
            except ValueError as e:
                print(f"Symbol {symbol} failed")
                print(e)
                return
            hist["Date"] = pd.to_datetime(hist["Date"], unit='ms')
            hist.set_index("Date", inplace=True)
            hist.sort_values(by="Date", ascending=True, inplace=True)
            return hist
        else:
            print(f"Bad response: {resp.status_code} - for symbol {symbol}")

    def apply_indicators(self, symbol: str, hist_data: pd.DataFrame) -> pd.DataFrame:
        try:
            ema = btalib.ema(hist_data, period=self.ema)
            ema_col = ema.df["ema"]
            symb_hist = symb_hist.join(ema_col)
        except:
            print(f"EMA fail on symbol: {symbol}")
            raise
        # Generate and attach SROC indicator, this is the ROC indicator applied to the EMA
        # Formula is = (ema[0] - ema[lookback]) / (ema[lookback]) * 100
        try:
            sroc = btalib.roc(symb_hist.ema, period=self.roc)
            symb_hist = symb_hist.join(sroc.df["roc"])
        except:
            print(f"SROC fail on symbol: {symbol}")
            raise
        

    def _get_start_date(self):
        hist_days = (self.ema + self.roc) * 2
        hist_start = datetime.today() - timedelta(days=hist_days)
        return hist_start