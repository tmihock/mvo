# Calculations for portfolio optimization
#
# Tristan Mihocko

# Assumes 252 trading days in a year
#
# Tristan Mihocko
import csv
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from scipy.optimize import minimize
from matplotlib import pyplot as plt
from fredapi import Fred
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass(frozen=True)
class OptimalPortfolio: 
	tickers: List[str]
	optimal_weights: np.ndarray
	optimal_portfolio_return: float
	optimal_portfolio_volatility: float
	optimal_sharpe_ratio: float

	def __str__(self):
		s = "Optimized Weights:\n"
		for ticker, weight in zip(self.tickers, self.optimal_weights):
			s += f"{ticker}:\t{weight:.4f}\n"
      
		s += f"\nExpected Annual Return:\t{self.optimal_portfolio_return:.2%}\n"
		s += f"Expected Volatility:\t{self.optimal_portfolio_volatility:.2%}\n"
		s += f"Expected Sharpe Ratio:\t{self.optimal_sharpe_ratio:.4f}\n"
		return s

def get_optimal_weights(tickers, *, start, end):
    
	adjusted_close_prices = pd.DataFrame()
 
	for ticker in tickers:
		data = yf.download(ticker, start=start, end=end, auto_adjust=False)
		adjusted_close_prices[ticker] = data['Adj Close']

	log_returns = np.log(adjusted_close_prices / adjusted_close_prices.shift(1)).dropna() # Lognormal returns make MVO cleaner
 
	covariance_matrix = log_returns.cov() * 252 # Annualized covariance matrix
 
 	#i=1∑(N​wi)​=1 
	constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1}) # Weights must sum to 1 (net exposure not gross exposure)
 
	bounds = [(0, 1) for _ in range(len(tickers))] # 0, 1 to disallow shorting
 
	initial_weights = np.array(len(tickers) * [1 / len(tickers)]) # Equal weight start
	

	optimized_results = minimize(neg_sharpe_ratio, initial_weights, args=(log_returns, covariance_matrix, fred_risk_free_rate()), 
                              method='SLSQP', constraints=constraints, bounds=bounds)
	
	optimal_weights = optimized_results.x
 
	return OptimalPortfolio(
    	tickers=tickers,
		optimal_weights=optimal_weights,
		optimal_portfolio_return=expected_returns(optimal_weights, log_returns),
		optimal_portfolio_volatility=portfolio_risk(optimal_weights, covariance_matrix),
		optimal_sharpe_ratio=sharpe_ratio(optimal_weights, log_returns, covariance_matrix, fred_risk_free_rate())
	)
	

# Use federal reserve API to get calculate risk free rate
def fred_risk_free_rate():
	fred = Fred(api_key='cfedb04650930f3f51d12e1c0f11e5e0')
	ten_year_treasury_rate = fred.get_series_latest_release('DGS10') / 100 # As percentage

	return ten_year_treasury_rate.iloc[-1] # Get last value
 
# AKA standard deviation
# Risk = σp = w⊤Σw
def portfolio_risk(weights, cov_matrix):
	return np.sqrt(weights.T @ cov_matrix @ weights)
 
# Based on historical data over time frame 
def expected_returns(weights, log_returns):
    return np.sum(log_returns.mean() * weights) * 252 # Annualized expected return
    
def sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate):
    return (expected_returns(weights, log_returns) - risk_free_rate) / portfolio_risk(weights, cov_matrix)

# No maximize function in scipy, so minimize negative sharpe ratio
def neg_sharpe_ratio(weights, log_returns, covariance_matrix, risk_free_rate):
	return -sharpe_ratio(weights, log_returns, covariance_matrix, risk_free_rate)
 
