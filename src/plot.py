# plot.py
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from Portfolio import Portfolio, PortfolioData
from typing import Tuple
from scipy.optimize import minimize

dot_size = 50

curve_cmap = "rainbow" # viridis
curve_alpha = 0.8


# -------------------------
# Plot
# -------------------------

small_threshold = 1e-6 # Threshold to consider weight as zero due to floating point errors

def plot_pie_chart(ax, tickers, weights):
	# Remove tickers with weights of 0
	filtered_tickers = [t for t, w in zip(tickers, weights) if w > small_threshold]
	filtered_weights = [w for w in weights if w > small_threshold]

	ax.clear()
	ax.pie(filtered_weights, labels=filtered_tickers, autopct="%.2f%%", textprops={"fontsize":8}, startangle=140)
	ax.set_title("Portfolio Allocation")
	ax.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.
	# plt.show()


def plot_efficient_frontier(ax, data: PortfolioData, bounds: Tuple[float, float], *, show_cml=True, 
							show_gmv=True, show_tangency=True, show_rf=True, points=50):
	frontier_portfolios = efficient_frontier(data, bounds, points=points)

	risks = []
	returns = []
	sharpe_ratios = []

	for p in frontier_portfolios:
		risks.append(p.expected_volatility)
		returns.append(p.expected_return)
		sharpe_ratios.append(p.expected_sharpe_ratio)
	
	risks = np.array(risks)
	returns = np.array(returns)
	sharpe_ratios = np.array(sharpe_ratios)

	ax.frontier_risks = risks
	ax.frontier_returns = returns
	ax.frontier_portfolios = frontier_portfolios


	max_sharpe = Portfolio.max_sharpe_portfolio(data, bounds)
	
	# Colored efficient frontier based on Sharpe ratio

	points = np.array([risks, returns]).T.reshape(-1, 1, 2)
	segments = np.concatenate([points[:-1], points[1:]], axis=1)

	lc = LineCollection(
		segments,
		cmap=curve_cmap, # viridis
		alpha=curve_alpha,
		norm=plt.Normalize(sharpe_ratios.min(), sharpe_ratios.max()*1.15),
		linewidth=2
	)
	lc.set_array(sharpe_ratios)            # set color per segment
	ax.add_collection(lc)

	color_bar = ax.figure.colorbar(lc, ax=ax, label="Sharpe Ratio")

	# Hover tooltips for Sharpe ratios

	lc.sharpes = sharpe_ratios # Make sharpe results accessible to cursor hover

	#----------
	# Other
	#----------

	artists = {}

	# Tangency Portfolio
	if show_tangency:
		artists["Tangency"] = ax.scatter(
			max_sharpe.expected_volatility, max_sharpe.expected_return,
			c="r", marker="o", s=dot_size, label="Tangency Point", zorder=3, picker=True
		)

	# Global Minimum Variance Point
	if show_gmv:
		min_risk_idx = np.argmin(risks)
		artists["GMV"] = ax.scatter(
			risks[min_risk_idx], returns[min_risk_idx],
			c="orange", marker="o", s=dot_size, label="Global Minimum Variance", zorder=3, picker=True
		)

	# Capital Market Line
	if show_cml:
		risk_free_rate = data.risk_free_rate

		sigma_cml = np.linspace(0, max(risks), 100)
		return_cml = risk_free_rate + sigma_cml * (max_sharpe.expected_return - risk_free_rate) / max_sharpe.expected_volatility
		artists["CML"] = ax.plot(sigma_cml, return_cml, "m--", label="Capital Market Line")[0]

	# Omit Risk-Free Rate Line Toggle

	ax.set_xlabel("Portfolio Risk (σ)")
	ax.set_ylabel("Expected Portfolio Return (μ)")
	ax.set_title("Efficient Frontier")

	ax.grid(True)
	ax.legend()
	
	return artists


def efficient_frontier(data: PortfolioData, bounds: Tuple[float, float], points=50) -> np.ndarray[Portfolio]:
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
	tickers = data.tickers

	log_returns = data.log_returns
	annualized_covariance = data.annualized_covariance
	mean_returns = log_returns.mean() * 252

	n = log_returns.shape[1]

	frontier_portfolios = []

	target_returns = np.linspace(mean_returns.min(), mean_returns.max(), points)
    
	for target in target_returns:
		constraints = (
			{"type": "eq", "fun": lambda w: np.sum(w) - 1},
			{"type": "eq", "fun": lambda w: np.sum(w * mean_returns) - target}
		)
		initial_weights = np.array([1 / len(tickers)] * len(tickers))

		def risk(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
			return np.sqrt(weights.T @ cov_matrix @ weights)
		
		result = minimize(risk, initial_weights, args=(annualized_covariance,), method="SLSQP", bounds=[bounds]*n, constraints=constraints)
		if result.success:
			weights = result.x
			frontier_portfolios.append(Portfolio(data, weights))

	return np.array(frontier_portfolios)
