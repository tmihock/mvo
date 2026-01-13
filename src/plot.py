# plot.py
from mvo_calc import efficient_frontier, max_sharpe_portfolio, fred_risk_free_rate, sharpe_ratio
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
from matplotlib.collections import LineCollection
from tkinter import Tk, Label
import numpy as np
import mplcursors

# -------------------------
# Plot
# -------------------------
def plot_efficient_frontier(tickers, *, start, end, points=50):
	risks, returns, weights, sharpe_ratios = efficient_frontier(tickers, start, end, points=points)
	risk_free_rate = fred_risk_free_rate()

	max_sharpe = max_sharpe_portfolio(tickers, start, end, risk_free_rate)

	fig, ax = plt.subplots(figsize=(10, 6))
	plt.subplots_adjust(left=0.25)  # leave room for checkbox

	# ax.plot(risks, returns, 'b-', linewidth=2, label='Efficient Frontier')

	# Colorful efficient frontier based on Sharpe ratio

	points = np.array([risks, returns]).T.reshape(-1, 1, 2)
	segments = np.concatenate([points[:-1], points[1:]], axis=1)

	lc = LineCollection(
		segments,
		cmap='viridis',
		alpha=0.5,
		norm=plt.Normalize(sharpe_ratios.min(), sharpe_ratios.max()*1.15),
		linewidth=2
	)
	lc.set_array(sharpe_ratios)            # set color per segment
	ax.add_collection(lc)

	color_bar = plt.colorbar(lc, ax=ax, label='Sharpe Ratio')

	# Hover tooltips for Sharpe ratios

	lc.sharpes = sharpe_ratios # Make sharpe results accessible to cursor hover

	# Create cursor
	cursor = mplcursors.cursor(lc, hover=True)
	cursor._pickradius = 18  # default is 5 points; makes it easier/smoother to hover

	@cursor.connect("add")
	def on_add(sel):
		target = sel.target
		
		# Check if target is a single number (sometimes happens)
		if isinstance(target, np.float64) or target.shape == ():
			# I honestly don't know when this happens, better to not show anything than show wrong information
			return
		else:
			# Find nearest line segment in lc to use for sharpe ratio lookup
			x0, y0 = target[0] if target.ndim == 2 else target
			dists = np.sqrt((segments[:,0,0] - x0)**2 + (segments[:,0,1] - y0)**2) 
			idx = np.argmin(dists)
		
		sharpe_value = lc.sharpes[idx]
		sel.annotation.set_text(f"Sharpe: {sharpe_value:.4f}")
		sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)

	@cursor.connect("remove")
	def on_remove(sel):
		sel.annotation.set_visible(False)

	
	#----------
	# Other
	#----------

	# Show max Sharpe ratio point
	max_sharpe_point = ax.scatter(
		max_sharpe.exp_volatility, 
		max_sharpe.exp_return, 
		c='r', marker='o', s=200, label='Max Sharpe'
	)

	# Show risk-free rate line
	risk_free_line = ax.plot(
		[0, max(risks)], 
		[risk_free_rate, max(returns)], 
		'g--', label='Risk-Free Rate'
	)[0]

	# Capital Market Line (CML)
	sigma_max = max(risks)

	sigma_cml = np.linspace(0, sigma_max, 100)
	return_cml = risk_free_rate + (sigma_cml) * (max_sharpe.exp_return - risk_free_rate) / max_sharpe.exp_volatility

	cml_line = ax.plot(
		sigma_cml,
		return_cml, 
		'm--', label='Capital Market Line'
	)[0]

	# Global Minimum Variance Point
	min_risk_index = risks.argmin()
	gmv_point = ax.scatter(risks[min_risk_index], returns[min_risk_index], c='orange', marker='o', s=200, label='Global Minimum Variance')

	# Omit Risk-Free Rate Line Toggle
	ax_check = plt.axes([0.05, 0.4, 0.18, 0.15], facecolor='lightgoldenrodyellow')

	labels = {
		'Risk-Free Rate Line' : risk_free_line,
		'Capital Market Line': cml_line,
		'Global Minimum Variance': gmv_point,
		'Tangency Portfolio (Max Sharpe)': max_sharpe_point
	}

	check = CheckButtons(ax_check, list(labels.keys()), [True]*len(labels))

	def toggle_visibility(label):
		labels[label].set_visible(not labels[label].get_visible())

		fig.canvas.draw_idle()

	check.on_clicked(toggle_visibility)

	# Click Event (Get weights)


	

	ax.set_xlabel('Portfolio Risk (σ)')
	ax.set_ylabel('Expected Portfolio Return (μ)')
	ax.set_title('Efficient Frontier')
	ax.grid(True)
	ax.legend()
	
	plt.show()



# -------------------------
# Show data 
# -------------------------
def show_portfolio_data():
	pass