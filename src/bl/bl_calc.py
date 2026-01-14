import pandas as pd
import numpy as np
from typing import List
from view import View
from mvo_calc import *
from yfinance import yf



def calc_equillibrium_returns(prices: pd.DataFrame, covariance_matrix: pd.DataFrame, risk_aversion) -> pd.DataFrame:
	"""
	Computes Black-Litterman equillibrium returns (∏).
	Args:
		prices (pd.DataFrame): Historic adjusted close prices from yfinance
		covariance_matrix (pd.DataFrame): Covariance matrix of asset returns
		risk_aversion (float): Risk aversion coefficient
	Returns:
		pd.DataFrame: Adjusted expected returns
	"""
	tickers = prices.columns.tolist()

	market_caps = get_market_caps(tickers)
	market_weights = market_caps / market_caps.sum()	
	
	return risk_aversion * covariance_matrix @ market_weights.values

def bl_expected_returns(prices: pd.DataFrame, covariance_matrix: pd.DataFrame, risk_aversion: float, views: List[View]) -> pd.Series:
	"""
	Step 2: Blends the Market Equilibrium (Pi) with Investor Views.
	Returns the final 'Refined Returns' to be used in your MVO.
	"""
	tickers = prices.columns.tolist()
	n = len(tickers)

	eq_returns = calc_equillibrium_returns(prices, covariance_matrix, risk_aversion, views)
	num_views = len(views)

	view_vector = np.zeros(num_views) 			# Q
	picking_matrix = np.zeros((num_views, n))	# P
	uncertainty_diag = [] 						# Omega_diag

	market_trust_factor = 0.05 # Scaling factor for uncertainty of the market baseline

	for i, view in enumerate(views):
		view_vector[i] = view.value # The return value you predicted
		
		# Build the Picking Matrix (P)
		if view.view_type == "absolute":
			for asset in view.assets:
				if asset in tickers:
					picking_matrix[i, tickers.index(asset)] = 1 / len(view.assets)
		
		elif view.view_type == "relative":
			for asset in view.long:
				if asset in tickers:
					picking_matrix[i, tickers.index(asset)] = 1 / len(view.long)
			for asset in view.short:
				if asset in tickers:
					picking_matrix[i, tickers.index(asset)] = -1 / len(view.short)

		# Calculate uncertainty for the view
		#  = P_iΣP_iᵀ
		view_variance = picking_matrix[i] @ (market_trust_factor * covariance_matrix) @ picking_matrix[i].T

		# Higher value = lower confidence
		uncertainty_diag.append(view_variance * (1 / view.confidence - 1 + 1e-9)) # + 1e-9 to avoid divide by zero

	uncertainty_matrix = np.diag(uncertainty_diag)

	# This math blends equillibrium returns and views based on the confidence
	market_precision = np.linalg.inv(market_trust_factor * covariance_matrix)
	view_precision = np.linalg.inv(uncertainty_matrix)

	# Combined Return = [Combined Confidence] x [Weighted Opinions]
	total_precision = np.linalg.inv(market_precision + picking_matrix.T @ view_precision @ picking_matrix) 	# How much information we have (confidence)
	weighted_opinions = market_precision @ eq_returns + picking_matrix.T @ view_precision @ view_vector 	# Market expected returns + views

	bl_returns = total_precision @ weighted_opinions

	return pd.Series(bl_returns, index=tickers)

		
def get_market_caps(tickers: List[str]) -> pd.Series:
    """Get current market caps for tickers."""
    caps = {}
    for t in tickers:
        stock = yf.Ticker(t)
        caps[t] = stock.info.get('marketCap', 0)
    return pd.Series(caps)
