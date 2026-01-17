import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
    QLabel, QListWidget, QSlider, QGroupBox, QListWidgetItem
)
from Portfolio import Portfolio
from PortfolioData import PortfolioData
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from plot import plot_pie_chart, plot_efficient_frontier, small_threshold
from mvo_calc import max_sharpe_portfolio, fred_risk_free_rate

class PortfolioWindow(QWidget):
	def __init__(self, tickers, start, end):
		super().__init__()
		self.tickers = tickers
		self.start = start
		self.end = end

		self.portfolio_data = PortfolioData(tickers, start, end)
		self.bounds_max = 1 # default upper bound
		self.current_portfolio = Portfolio.max_sharpe_portfolio(self.portfolio_data, (0, self.bounds_max))

		self.setWindowTitle("Portfolio Visualization")
		self.resize(1400, 700)

		self.init_ui()

	def init_ui(self):
		# Main horizontal layout
		main_layout = QHBoxLayout(self)

		# --- LEFT COLUMN ---
		left_layout = QVBoxLayout()

		# --- Top: Checkboxes, Dates, Slider ---
		# Graph Settings
		settings_group = QGroupBox("Graph Settings")
		settings_layout = QVBoxLayout(settings_group)

		# Checkboxes
		cb_group = QGroupBox("Portfolios / Lines")
		cb_layout = QVBoxLayout(cb_group)
		self.cml_cb = QCheckBox("Capital Market Line")
		self.gmv_cb = QCheckBox("Global Minimum Variance")
		self.tangency_cb = QCheckBox("Tangency Portfolio")
		for cb in [self.cml_cb, self.gmv_cb, self.tangency_cb]:
			cb.setChecked(True)
			cb.stateChanged.connect(self.toggle_artists)
			cb_layout.addWidget(cb)
		settings_layout.addWidget(cb_group)

		# Dates
		from PyQt6.QtWidgets import QDateEdit, QFormLayout
		date_group = QGroupBox("Date Range")
		date_layout = QFormLayout(date_group)
		self.startDateEdit = QDateEdit()
		self.endDateEdit = QDateEdit()
		date_layout.addRow(QLabel("Start:"), self.startDateEdit)
		date_layout.addRow(QLabel("End:"), self.endDateEdit)
		settings_layout.addWidget(date_group)

		# Bounds Slider
		bounds_group = QGroupBox("Bounds")
		bounds_layout = QVBoxLayout(bounds_group)
		self.slider = QSlider(Qt.Orientation.Horizontal)
		self.slider.setRange(0, 100)
		self.slider.setValue(self.bounds_max)
		self.slider.valueChanged.connect(self.slider_changed)
		self.slider_label = QLabel(str(self.bounds_max))
		self.slider_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		bounds_layout.addWidget(self.slider)
		bounds_layout.addWidget(self.slider_label)
		settings_layout.addWidget(bounds_group)

		# --- Right of top: Weights list ---
		self.weight_group = QGroupBox("Portfolio Weights")
		weight_layout = QVBoxLayout(self.weight_group)
		self.weight_list = QListWidget()
		weight_layout.addWidget(self.weight_list)

		# Combine top left and weights horizontally
		top_layout = QHBoxLayout()
		top_layout.addWidget(settings_group, 3)  # wider
		top_layout.addWidget(self.weight_group, 1)  # skinnier
		left_layout.addLayout(top_layout)

		# --- Bottom: Pie chart ---
		pie_group = QGroupBox("Portfolio Pie Chart")
		pie_layout = QVBoxLayout(pie_group)
		self.pie_fig = Figure(figsize=(4, 4))
		self.pie_canvas = FigureCanvas(self.pie_fig)
		pie_layout.addWidget(self.pie_canvas)
		left_layout.addWidget(pie_group)

		# --- RIGHT COLUMN: Efficient Frontier ---
		self.main_group = QGroupBox("Efficient Frontier")
		main_layout_right = QVBoxLayout(self.main_group)
		self.main_fig = Figure(figsize=(8, 6))
		self.main_canvas = FigureCanvas(self.main_fig)
		main_layout_right.addWidget(self.main_canvas)

		# Add left and right to main layout
		main_layout.addLayout(left_layout, 2)
		main_layout.addWidget(self.main_group, 3)

		# Populate initial weights
		self.load_weights()
		self.update_main_plot()
		self.update_pie_chart()

	# -------------------------
	# Slots
	# -------------------------
	def slider_changed(self, value):
		self.bounds_max = value
		self.slider_label.setText(f"{value/100:.2f}")

	def toggle_artists(self):
		self.efficient_artists['CML'].set_visible(self.cml_cb.isChecked())
		self.efficient_artists['GMV'].set_visible(self.gmv_cb.isChecked())
		self.efficient_artists['Tangency'].set_visible(self.tangency_cb.isChecked())
		self.main_canvas.draw_idle()

	def load_weights(self):
		self.weight_list.clear()
		weights = self.current_portfolio.weights
		for i, ticker in enumerate(self.tickers):
			if weights[i] < small_threshold:
				continue
			item = QListWidgetItem(f"{ticker}: {weights[i]*100:.2f}%")
			item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
			self.weight_list.addItem(item)
		self.weight_list.itemChanged.connect(self.update_pie_chart)

	def update_main_plot(self):
		self.main_fig.clf()
		ax = self.main_fig.add_subplot(111)
		self.current_portfolio = Portfolio.max_sharpe_portfolio(self.portfolio_data, (0, self.bounds_max)) # Set new portfolio
		self.efficient_artists = plot_efficient_frontier(ax, self.tickers, self.start, self.end)
		self.toggle_artists()

	def update_pie_chart(self):
		ax = self.pie_fig.clf()
		ax = self.pie_fig.add_subplot(111)
		plot_pie_chart(ax, self.tickers, self.current_portfolio.weights)
		self.pie_canvas.draw_idle()
