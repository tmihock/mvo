import pandas as pd
import numpy as np
import yfinance as yf
from functools import cached_property, lru_cache
from fetch_data import fetch_data
from fredapi import Fred
from typing import List

class PortfolioData():
	def __init__(self, tickers: List[str], start: str, end: str, risk_free_rate=None):
		self.tickers = tickers
		self.start = start
		self.end = end 
		self.risk_free_rate = fred_risk_free_rate() if risk_free_rate is None else risk_free_rate # 0 is falsy :(

	@cached_property
	def prices(self) -> pd.DataFrame:
		return fetch_data(self.tickers, self.start, self.end)

	@cached_property
	def log_returns(self) -> pd.DataFrame:
		return np.log(self.prices / self.prices.shift(1)).dropna() 

	@cached_property
	def annualized_covariance(self) -> np.ndarray:
		return self.log_returns.cov() * 252

	@cached_property
	def mean_returns(self) :
		return self.log_returns.mean() * 252




@lru_cache()
def fred_risk_free_rate():
	"""
	Fetches the latest 10-year Treasury yield from FRED as the risk-free rate.

	Returns:
		float: Annualized risk-free rate (decimal)
	"""
	fred = Fred(api_key='cfedb04650930f3f51d12e1c0f11e5e0')
	ten_year_treasury_rate = fred.get_series_latest_release('DGS10') / 100 # As percentage

	return ten_year_treasury_rate.iloc[-1] 