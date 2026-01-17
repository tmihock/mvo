from functools import lru_cache
from fredapi import Fred
import pandas as pd
import yfinance as yf
from typing import Tuple

@lru_cache()
def fetch_data(tickers: Tuple[str], start: str, end: str) -> pd.DataFrame:
	"""
    Downloads historical adjusted close prices for a list of tickers.

    Args:
        tickers (Tuple[str]): Asset tickers
        start (str): Start date (YYYY-MM-DD)
        end (str): End date (YYYY-MM-DD)

    Returns:
        pd.DataFrame: DataFrame of adjusted close prices (columns = tickers)
    """
	prices = pd.DataFrame()
	for ticker in tickers:
		data = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
		prices[ticker] = data['Adj Close']
	return prices