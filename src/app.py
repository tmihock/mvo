import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
    QLabel, QListWidget, QSlider, QFrame, QGroupBox, QListWidgetItem
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from plot import plot_pie_chart, plot_efficient_frontier, small_threshold
from mvo_calc import max_sharpe_portfolio, fred_risk_free_rate


""""
TODO:

* Render button
 - Input risk free rate (option to use federal reserve rate)

 - Bounds for each ticker (ticker options?)
 - Bounds impl (on re-render)
 - set risk-free rate (on re-render)

* Data 
 - Hover to see sharpe (exact number)
 - Option to show points for 100% in a stock
 - Click on point on line to see weights
 - export weights to csv (ticker, weight)

* Format
 - portfolio weights box longer (down), bounds smaller
 - Maybe wrap weights to be two columned?
 - Checkboxes box on right 

"""

class PortfolioWindow(QWidget):
	def __init__(self, tickers, start, end):
		super().__init__()
		self.start = start
		self.end = end
		self.tickers = tickers
		self.setWindowTitle("Portfolio Visualization")
		self.setGeometry(100, 100, 1400, 700)

		self.init_ui()

	def init_ui(self):
		main_layout = QHBoxLayout()

		# --- Left column ---
		left_layout = QVBoxLayout()

		# Checkboxes
		cb_group = QGroupBox("Portfolios / Lines")
		cb_layout = QVBoxLayout()
		self.cml_cb = QCheckBox("Capital Market Line")
		self.gmv_cb = QCheckBox("Global Minimum Variance")
		self.tangency_cb = QCheckBox("Tangency Portfolio")
		for cb in [self.cml_cb, self.gmv_cb, self.tangency_cb]:
			cb.setChecked(True)
			cb.stateChanged.connect(self.toggle_artists)
		cb_layout.addWidget(self.cml_cb)
		cb_layout.addWidget(self.gmv_cb)
		cb_layout.addWidget(self.tangency_cb)
		cb_group.setLayout(cb_layout)
		left_layout.addWidget(cb_group)

		# Weights
		weight_group = QGroupBox("Portfolio Weights")
		weight_layout = QVBoxLayout()
		self.weight_list = QListWidget()
		max_sharpe = max_sharpe_portfolio(self.tickers, start=self.start, end=self.end, risk_free_rate=fred_risk_free_rate())
		weights = max_sharpe.weights

		for i, w in enumerate(self.tickers):
			ticker_weight = weights[i]
			if ticker_weight < small_threshold: 
				continue

			item = QListWidgetItem(f"{w}:\t{weights[i]*100:.2f}%")
			item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
			self.weight_list.addItem(item)

		self.weight_list.itemChanged.connect(self.update_pie_chart)
		weight_layout.addWidget(self.weight_list)
		weight_group.setLayout(weight_layout)
		left_layout.addWidget(weight_group)

		# Slider
		slider_group = QGroupBox("Bounds")
		slider_layout = QVBoxLayout()
		self.slider = QSlider(Qt.Orientation.Horizontal)
		self.slider.setRange(0,100)
		self.slider.setValue(50)
		self.slider.valueChanged.connect(self.slider_changed)
		self.slider_label = QLabel("0.50")
		slider_layout.addWidget(self.slider)
		slider_layout.addWidget(self.slider_label)
		slider_group.setLayout(slider_layout)
		left_layout.addWidget(slider_group)

		# Pie chart
		pie_group = QGroupBox("Portfolio Pie Chart")
		pie_layout = QVBoxLayout()
		self.pie_fig = Figure(figsize=(4,4))
		self.pie_canvas = FigureCanvas(self.pie_fig)
		pie_layout.addWidget(self.pie_canvas)
		pie_group.setLayout(pie_layout)
		left_layout.addWidget(pie_group)

		left_layout.addStretch()

		# --- Right column ---
		self.main_group = QGroupBox("Efficient Frontier")
		main_layout_right = QVBoxLayout()
		self.main_fig = Figure(figsize=(8,6))
		self.main_canvas = FigureCanvas(self.main_fig)
		main_layout_right.addWidget(self.main_canvas)
		self.main_group.setLayout(main_layout_right)

		main_layout.addLayout(left_layout,1)
		main_layout.addWidget(self.main_group,2)
		self.setLayout(main_layout)

		# Initial plots
		self.update_main_plot()
		self.update_pie_chart()

	# -------------------------
	# Slots
	# -------------------------
	def slider_changed(self, value):
		self.slider_label.setText(f"{value/100:.2f}")
		# Could implement dynamic frontier updates here if needed

	def update_main_plot(self):
		self.main_fig.clf()
		ax = self.main_fig.add_subplot(111)
		self.efficient_artists = plot_efficient_frontier(ax, self.tickers, self.start, self.end)
		self.toggle_artists()  # apply initial checkbox states
		self.main_canvas.draw_idle()

	def toggle_artists(self):
		self.efficient_artists['CML'].set_visible(self.cml_cb.isChecked())
		self.efficient_artists['GMV'].set_visible(self.gmv_cb.isChecked())
		self.efficient_artists['Tangency'].set_visible(self.tangency_cb.isChecked())
		self.main_canvas.draw_idle()

	def update_pie_chart(self):
		ax = self.pie_fig.add_subplot(111)

		max_sharpe = max_sharpe_portfolio(self.tickers, start=self.start, end=self.end, risk_free_rate=fred_risk_free_rate())


		plot_pie_chart(ax, self.tickers, max_sharpe.weights)
		self.pie_canvas.draw_idle()