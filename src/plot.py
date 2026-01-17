# plot.py
from mvo_calc import efficient_frontier, max_sharpe_portfolio, fred_risk_free_rate
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
from matplotlib.collections import LineCollection
import numpy as np


dot_size = 50

curve_cmap = 'rainbow' # viridis
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
	ax.pie(filtered_weights, labels=filtered_tickers, autopct='%.2f%%', textprops={'fontsize':8}, startangle=140)
	ax.set_title('Portfolio Allocation')
	ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
	# plt.show()


def plot_efficient_frontier(ax, tickers, start=None, end=None, *, show_cml=True, 
							show_gmv=True, show_tangency=True, show_rf=True, points=50):
	risk_free_rate = fred_risk_free_rate()
	risks, returns, weights, sharpe_ratios = efficient_frontier(tickers, start, end, points=points)

	max_sharpe = max_sharpe_portfolio(tickers, start, end, risk_free_rate)
	
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

	color_bar = ax.figure.colorbar(lc, ax=ax, label='Sharpe Ratio')

	# Hover tooltips for Sharpe ratios

	lc.sharpes = sharpe_ratios # Make sharpe results accessible to cursor hover

	#----------
	# Other
	#----------

	artists = {}

	# Tangency Portfolio
	if show_tangency:
		artists['Tangency'] = ax.scatter(
			max_sharpe.exp_volatility, max_sharpe.exp_return,
			c='r', marker='o', s=dot_size, label='Tangency Point', zorder=3
		)

	# Global Minimum Variance Point
	if show_gmv:
		min_risk_idx = np.argmin(risks)
		artists['GMV'] = ax.scatter(
			risks[min_risk_idx], returns[min_risk_idx],
			c='orange', marker='o', s=dot_size, label='Global Minimum Variance', zorder=3
		)

	# Capital Market Line
	if show_cml:
		sigma_cml = np.linspace(0, max(risks), 100)
		return_cml = risk_free_rate + sigma_cml * (max_sharpe.exp_return - risk_free_rate) / max_sharpe.exp_volatility
		artists['CML'] = ax.plot(sigma_cml, return_cml, 'm--', label='Capital Market Line')[0]

	# Omit Risk-Free Rate Line Toggle

	ax.set_xlabel('Portfolio Risk (σ)')
	ax.set_ylabel('Expected Portfolio Return (μ)')
	ax.set_title('Efficient Frontier')
	ax.grid(True)
	ax.legend()
	
	return artists
