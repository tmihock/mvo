import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Tuple
from PortfolioData import PortfolioData

default_bounds = (0, 1)

class Portfolio:
	def __init__(self, data: PortfolioData, weights: np.ndarray):
		self.data = data
		self.weights = weights
	
	@property
	def expected_return(self) -> float:
		"""
		Calculates portfolio expected return.

		Args:
			weights (np.ndarray): Portfolio weights
			log_returns (pd.DataFrame): Daily log returns

		Returns:
			float: Portfolio expected return (annualized)
		"""	
		return np.sum(self.data.log_returns.mean() * self.weights) * 252

	@property
	def expected_volatility(self):
		"""
		Calculates portfolio standard deviation (risk).

		Args:
			weights (np.ndarray): Portfolio weights
			cov_matrix (np.ndarray): Covariance matrix of asset returns

		Returns:
			float: Portfolio volatility (annualized)
		"""
		return np.sqrt(self.weights.T @ self.data.annualized_covariance @ self.weights)

	@property
	def expected_sharpe_ratio(self):
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
		return (self.expected_return - self.data.risk_free_rate) / self.expected_volatility

	@classmethod
	def max_sharpe_portfolio(cls, data: PortfolioData, bounds: Tuple[float, float] = None):
		n = data.log_returns.shape[1]
		bounds = bounds or default_bounds # default: no shorting, max 50% per asset
		initial_weights = np.array([1/n] * n) # Doesn"t change output

		constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1})
		
		def neg_sharpe(weights: np.ndarray, log_returns: pd.DataFrame, cov_matrix: np.ndarray, risk_free_rate: float) -> float:
			exp_returns = np.sum(log_returns.mean() * weights) * 252
			exp_volatility = np.sqrt(weights.T @ cov_matrix @ weights)
			return -((exp_returns - risk_free_rate) / exp_volatility)

		result = minimize(neg_sharpe, initial_weights, args=(
							data.log_returns, data.annualized_covariance, data.risk_free_rate),
							method="SLSQP", bounds=[bounds]*n, constraints=constraints
						)

		if not result.success:
			raise ValueError("Optimization failed to find maximum Sharpe ratio portfolio.")

		return cls(data, result.x)

	@classmethod
	def min_variance_portfolio(cls, data: PortfolioData, bounds: Tuple[float, float] = None):
		n = data.log_returns.shape[1]
		bounds = bounds or default_bounds # default: no shorting, max 50% per asset
		initial_weights = np.array([1/n] * n) # Doesn"t change output

		constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1})
		
		def risk(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
			return np.sqrt(weights.T @ cov_matrix @ weights)

		result = minimize(risk, initial_weights, args=(data.annualized_covariance,),
						 	method="SLSQP", bounds=[bounds]*n, constraints=constraints
						)

		if not result.success:
			raise ValueError("Optimization failed to find minimum variance portfolio.")

		return cls(data, result.x)

	@classmethod
	def from_target_return(cls, data: PortfolioData, target_return: float, bounds: Tuple[float, float]):
		n = data.log_returns.shape[1]
		bounds = bounds or default_bounds # default: no shorting, max 50% per asset
		annualized_covariance = data.annualized_covariance
		initial_weights = np.array([1 / len(data.tickers)] * len(data.tickers))

		constraints = (
			{"type": "eq", "fun": lambda w: np.sum(w) - 1},
			{"type": "eq", "fun": lambda w: np.sum(w * data.mean_returns) - target_return}
		)
		def risk(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
			return np.sqrt(weights.T @ cov_matrix @ weights)

		# Minimize risk (volatility) with target return
		result = minimize(risk, initial_weights, args=(annualized_covariance),
						 	method="SLSQP", bounds=[bounds]*n, constraints=constraints
						)

		if not result.success:
			raise ValueError("Optimization failed for target return.")

		return cls(data, result.x)
