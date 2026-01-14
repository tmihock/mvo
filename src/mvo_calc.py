# Calculations for portfolio optimization
#
# Tristan Mihocko

# Assumes 252 trading days in a year
#
# Tristan Mihocko
import yfinance as yf
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from fredapi import Fred
from dataclasses import dataclass
from typing import List, Tuple, Optional
import functools

default_bounds = (0, .5)

@dataclass(frozen=True)
class Portfolio: 
	"""
	Stores details of an optimized portfolio.

	Attributes:
		tickers (Tuple[str]): List of asset tickers
		weights (np.ndarray): Portfolio weights (sum to 1)
		exp_return (float): Expected portfolio return (annualized)
		exp_volatility (float): Portfolio risk (annualized standard deviation)
		sharpe_ratio (float): Portfolio Sharpe ratio
	"""
	tickers: Tuple[str]
	weights: np.ndarray
	exp_return: float
	exp_volatility: float
	exp_sharpe_ratio: float

	def __str__(self):
		s = ""
		for ticker, weight in zip(self.tickers, self.weights):
			s += f"{ticker}:\t{weight:.4f}\n"
      
		s += f"\nExpected Annual Return:\t{self.exp_return:.2%}\n"
		s += f"Expected Volatility:\t{self.exp_volatility:.2%}\n"
		s += f"Expected Sharpe Ratio:\t{self.exp_sharpe_ratio:.4f}\n"
		return s

# -------------------------
# Data/input 
# -------------------------

@functools.lru_cache()
def download_data(tickers: Tuple[str], start: str, end: str) -> pd.DataFrame:
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

def calc_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
	"""
	Calculates log returns from price data.

	Args:
		prices (pd.DataFrame): Historic adjusted close prices from yfinance

	Returns:
		pd.DataFrame: Daily log returns
	"""	
	return np.log(prices / prices.shift(1)).dropna() 

def annualized_covariance(log_returns: pd.DataFrame) -> pd.DataFrame:
	"""
	Computes the annualized covariance matrix from log returns.

	Args:
		log_returns (pd.DataFrame): Daily log returns

	Returns:
		pd.DataFrame: Annualized covariance matrix
	"""
	return log_returns.cov() * 252 # Annualized covariance matrix

# -------------------------
# Portfolio metrics
# -------------------------

def portfolio_risk(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
	"""
	Calculates portfolio standard deviation (risk).

	Args:
		weights (np.ndarray): Portfolio weights
		cov_matrix (np.ndarray): Covariance matrix of asset returns

	Returns:
		float: Portfolio volatility (annualized)
	"""
	return np.sqrt(weights.T @ cov_matrix @ weights)
 
def expected_returns(weights: np.ndarray, log_returns: pd.DataFrame) -> float:
	"""
	Calculates portfolio expected return.

	Args:
		weights (np.ndarray): Portfolio weights
		log_returns (pd.DataFrame): Daily log returns

	Returns:
		float: Portfolio expected return (annualized)
	"""
	return np.sum(log_returns.mean() * weights) * 252 # Annualized expected return
    
def sharpe_ratio(weights: np.ndarray, log_returns: pd.DataFrame, cov_matrix: np.ndarray, risk_free_rate: float) -> float:
	"""
	Computes the portfolio Sharpe ratio.

	Args:
		weights (np.ndarray): Portfolio weights
		log_returns (pd.DataFrame): Daily log returns
		cov_matrix (np.ndarray): Covariance matrix
		risk_free_rate (float): Annualized risk-free rate

	Returns:
		float: Portfolio Sharpe ratio
	"""
	return (expected_returns(weights, log_returns) - risk_free_rate) / portfolio_risk(weights, cov_matrix)

def neg_sharpe_ratio(weights: np.ndarray, log_returns: pd.DataFrame, cov_matrix: np.ndarray, risk_free_rate: float) -> float:
	"""
	Negative Sharpe ratio, used for minimization in optimization.

	Args:
		weights (np.ndarray): Portfolio weights
		log_returns (pd.DataFrame): Daily log returns
		cov_matrix (np.ndarray): Covariance matrix
		risk_free_rate (float): Annualized risk-free rate

	Returns:
		float: -sharpe_ratio()
	"""
	return -sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate)
	
# -------------------------
# Optimization functions
# -------------------------

def optimize_max_sharpe(log_returns: pd.DataFrame, cov_matrix: pd.DataFrame, risk_free_rate: float, bounds: Optional[List[Tuple[float,float]]]=None) -> np.ndarray:
	"""
	Computes portfolio weights that maximize the Sharpe ratio.

	Args:
		log_returns (pd.DataFrame): Daily log returns
		cov_matrix (pd.DataFrame): Covariance matrix
		risk_free_rate (float): Annualized risk-free rate
		bounds (List[Tuple[float,float]], optional): Weight bounds per asset

	Returns:
		np.ndarray: Optimal portfolio weights
	"""   
	n = log_returns.shape[1]
	if bounds is None:
		bounds = [default_bounds for _ in range(n)]  # default: no shorting, max 50% per asset
	constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
	initial_weights = np.array([1/n] * n)
    
	result = minimize(neg_sharpe_ratio, initial_weights, args=(log_returns, cov_matrix, risk_free_rate),
								 method='SLSQP', bounds=bounds, constraints=constraints)

	if not result.success:
		raise ValueError("Optimization failed to find maximum Sharpe ratio portfolio.")

	return result.x

def max_sharpe_portfolio(tickers: Tuple[str], start: str, end: str, risk_free_rate: float) -> Portfolio:
	"""
	Returns the maximum Sharpe ratio portfolio for given tickers and date range.

	Args:
		tickers (Tuple[str]): Asset tickers
		start (str): Start date (YYYY-MM-DD)
		end (str): End date (YYYY-MM-DD)
		risk_free_rate (float): Annualized risk-free rate

	Returns:
		OptimalPortfolio: Data class with optimal weights, return, risk, Sharpe
	"""	
	if risk_free_rate is None: 
		risk_free_rate = fred_risk_free_rate()

	prices = download_data(tickers, start, end)
	log_returns = calc_log_returns(prices)
	cov_matrix = annualized_covariance(log_returns)
	optimal_weights = optimize_max_sharpe(log_returns, cov_matrix, risk_free_rate)
    
	return Portfolio(
        tickers=tickers,
        weights=optimal_weights,
        exp_return=expected_returns(optimal_weights, log_returns),
        exp_volatility=portfolio_risk(optimal_weights, cov_matrix),
        exp_sharpe_ratio=sharpe_ratio(optimal_weights, log_returns, cov_matrix, risk_free_rate)
    )

def optimized_portfolio_from_returns(tickers: Tuple[str], returns: float, start: str, end: str, risk_free_rate: float) -> Portfolio:
	"""
	Returns the minimum risk portfolio for a target return.

	Args:
		tickers (Tuple[str]): Asset tickers
		returns (float): Target annualized return
		start (str): Start date (YYYY-MM-DD)
		end (str): End date (YYYY-MM-DD)
		risk_free_rate (float): Annualized risk-free rate

	Returns:
		OptimalPortfolio: Data class with optimal weights, return, risk, Sharpe
	"""	
	prices = download_data(tickers, start, end)
	log_returns = calc_log_returns(prices)
	cov_matrix = annualized_covariance(log_returns)
	mean_returns = log_returns.mean() * 252

	constraints = (
		{'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
		{'type': 'eq', 'fun': lambda w: np.sum(w * mean_returns) - returns}
	)
	bounds = [default_bounds for _ in tickers]
	initial_weights = np.array([1 / len(tickers)] * len(tickers))
	
	result = minimize(portfolio_risk, initial_weights, args=(cov_matrix,), method='SLSQP', bounds=bounds, constraints=constraints)
	if not result.success:
		raise ValueError("Optimization failed for target return.")

	weights = result.x
	return Portfolio(
		tickers=tickers,
		weights=weights,
 	   exp_return=expected_returns(weights, log_returns),
		exp_volatility=portfolio_risk(weights, cov_matrix),
		exp_sharpe_ratio=sharpe_ratio(weights, log_returns, cov_matrix, risk_free_rate)
	)

# -------------------------
# Efficient frontier
# -------------------------

def efficient_frontier(tickers, start, end, points=50):
	"""
	Computes the efficient frontier (minimum risk portfolios for range of target returns).

	Args:
		tickers (Tuple[str]): Asset tickers
		start (str): Start date (YYYY-MM-DD)
		end (str): End date (YYYY-MM-DD)
		points (int): Number of portfolios to generate along frontier

	Returns:
		Tuple:
			- np.ndarray: Portfolio risks (σ) along frontier
			- np.ndarray: Portfolio expected returns (μ) along frontier
			- List[np.ndarray]: Portfolio weights for each frontier point
			- np.ndarray: Sharpe ratios for each frontier point
	"""
	prices = download_data(tickers, start, end)
	log_returns = calc_log_returns(prices)
	cov_matrix = annualized_covariance(log_returns)
	mean_returns = log_returns.mean() * 252
	risk_free_rate = fred_risk_free_rate()

	frontier_returns = []
	frontier_risks = []
	frontier_weights = []
	sharpe_ratios = []

	target_returns = np.linspace(mean_returns.min(), mean_returns.max(), points)
    
	for target in target_returns:
		constraints = (
			{'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
			{'type': 'eq', 'fun': lambda w: np.sum(w * mean_returns) - target}
		)
		bounds = [default_bounds for _ in tickers]
		initial_weights = np.array([1 / len(tickers)] * len(tickers))
		
		result = minimize(portfolio_risk, initial_weights, args=(cov_matrix,), method='SLSQP', bounds=bounds, constraints=constraints)
		if result.success:
			w = result.x
			frontier_weights.append(w)
			frontier_returns.append(np.sum(w * mean_returns))
			frontier_risks.append(np.sqrt(w.T @ cov_matrix @ w))
			sharpe_ratios.append(sharpe_ratio(w, log_returns, cov_matrix, risk_free_rate))

	return np.array(frontier_risks), np.array(frontier_returns), frontier_weights, np.array(sharpe_ratios)

# -------------------------
# Risk-free rate
# -------------------------

@functools.lru_cache()
def fred_risk_free_rate():
	"""
	Fetches the latest 10-year Treasury yield from FRED as the risk-free rate.

	Returns:
		float: Annualized risk-free rate (decimal)
	"""
	fred = Fred(api_key='cfedb04650930f3f51d12e1c0f11e5e0')
	ten_year_treasury_rate = fred.get_series_latest_release('DGS10') / 100 # As percentage

	return ten_year_treasury_rate.iloc[-1] 