from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
    QLabel, QListWidget, QSlider, QGroupBox, QListWidgetItem,
	QDateEdit, QFormLayout, QPushButton, QLineEdit, QSpinBox, QFileDialog
)
from Portfolio import Portfolio
from PortfolioData import PortfolioData
from PyQt6.QtCore import Qt, QDate
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from plot import plot_pie_chart, plot_efficient_frontier, small_threshold
from datetime import datetime, timedelta
import csv

class PortfolioWindow(QWidget):
	def __init__(self, tickers):
		super().__init__()
		self.tickers = tickers

		self.end_date = datetime.now() # Today
		self.start_date = self.end_date - timedelta(days=10*365) # Five years ago
		self.points = 50

		self.portfolio_data = PortfolioData(tickers, self.start_date, self.end_date)
		self.bounds_max = 1 # default upper bound
		self.current_portfolio = Portfolio.max_sharpe_portfolio(self.portfolio_data, (0, self.bounds_max))

		self.setWindowTitle("Portfolio Visualization")
		self.resize(1400, 700)

		self.mouse_down_graph = False

		self.init_ui()

	def init_ui(self):
		# Main horizontal layout
		main_layout = QHBoxLayout(self)

		# --- LEFT COLUMN ---
		left_layout = QVBoxLayout()

		# --- Top row: Settings + Weights ---
		top_row_layout = QHBoxLayout()

		# --- Settings group (Graph + Portfolio Settings) ---
		settings_group = QGroupBox("Settings")
		settings_layout = QVBoxLayout(settings_group)

		# Graph Settings
		graph_group = QGroupBox("Graph Settings")
		graph_layout = QVBoxLayout(graph_group)
		self.cml_cb = QCheckBox("Capital Market Line")
		self.tangency_cb = QCheckBox("Tangency Portfolio")
		self.gmv_cb = QCheckBox("Global Minimum Variance") 
		self.gmv_cb.clicked.connect(self.on_gmv_clicked)
		self.tangency_cb.clicked.connect(self.on_tp_clicked)
		# Keep this order to match graph
		for cb in [self.cml_cb, self.tangency_cb, self.gmv_cb]:
			cb.setChecked(True)
			cb.stateChanged.connect(self.toggle_artists)
			graph_layout.addWidget(cb)
		settings_layout.addWidget(graph_group)

		# Portfolio Settings (dates + render + bounds)
		portfolio_group = QGroupBox("Portfolio Settings")
		portfolio_main_layout = QVBoxLayout()

		# Top row: Dates + Render button
		top_portfolio_row = QHBoxLayout()

		# Dates
		date_layout = QFormLayout()
		today = QDate.currentDate()
		ten_years_ago = today.addYears(-10)

		self.start_date_edit = QDateEdit()
		self.start_date_edit.setCalendarPopup(True)
		self.start_date_edit.setDate(datetime_to_qdate(self.start_date))
		self.start_date_edit.setMaximumDate(today)
		self.start_date_edit.setMinimumDate(ten_years_ago)
		self.start_date_edit.dateChanged.connect(self.on_start_changed)

		self.end_date_edit = QDateEdit()
		self.end_date_edit.setCalendarPopup(True)
		self.end_date_edit.setDate(datetime_to_qdate(self.end_date))
		self.end_date_edit.setMaximumDate(today)
		self.end_date_edit.setMinimumDate(ten_years_ago)
		self.end_date_edit.dateChanged.connect(self.on_end_changed)

		date_layout.addRow(QLabel("Start Date:"), self.start_date_edit)
		date_layout.addRow(QLabel("End Date:"), self.end_date_edit)
		top_portfolio_row.addLayout(date_layout, 2)

		# Points 
		self.points_spin = QSpinBox()
		self.points_spin.setRange(10, 999) 
		self.points_spin.setValue(self.points)
		self.points_spin.setSingleStep(10)
		self.points_spin.valueChanged.connect(self.on_points_changed)
		date_layout.addRow(QLabel("Points:"), self.points_spin)  

		# Render button
		self.render_button = QPushButton("Render")
		self.render_button.setMinimumHeight(50)
		self.render_button.clicked.connect(self.on_render_clicked)
		top_portfolio_row.addWidget(self.render_button, 1)

		portfolio_main_layout.addLayout(top_portfolio_row)

		# Bounds slider
		self.slider = QSlider(Qt.Orientation.Horizontal)
		self.slider.setRange(0, 100)
		self.slider.setValue(self.bounds_max*100)
		self.slider.setFixedHeight(30)
		self.slider_text = QLineEdit()
		self.slider_text.setMaximumWidth(60)
		self.slider_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.slider_text.editingFinished.connect(self.slider_text_changed)
		self.slider_changed(self.bounds_max*100)
		self.slider.valueChanged.connect(self.slider_changed)

		portfolio_main_layout.addWidget(QLabel("Max weight:"))
		portfolio_main_layout.addWidget(self.slider)
		portfolio_main_layout.addWidget(self.slider_text, alignment=Qt.AlignmentFlag.AlignCenter)

		portfolio_group.setLayout(portfolio_main_layout)
		settings_layout.addWidget(portfolio_group)

		# --- Portfolio Information ---
		self.weight_group = QGroupBox("Portfolio Information")
		weight_layout = QVBoxLayout(self.weight_group)

		# Weights list
		self.weight_list = QListWidget()
		weight_layout.addWidget(self.weight_list)

		# --- Export button at the bottom ---
		self.export_button = QPushButton("Export to CSV")
		self.export_button.setMinimumHeight(40)
		self.export_button.clicked.connect(self.export_weights)  # Call the function
		weight_layout.addWidget(self.export_button, alignment=Qt.AlignmentFlag.AlignCenter)

		# Stats layout BELOW the list
		stats_layout = QFormLayout()
		stats_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
		stats_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
		stats_layout.setHorizontalSpacing(12)

		self.exp_return_label = QLabel("-")
		self.exp_vol_label = QLabel("-")
		self.exp_sharpe_label = QLabel("-")

		stats_layout.addRow("Return:", self.exp_return_label)
		stats_layout.addRow("Volatility:", self.exp_vol_label)
		stats_layout.addRow("Sharpe Ratio:", self.exp_sharpe_label)

		weight_layout.addLayout(stats_layout)

		# Add Settings + Weights to top row
		top_row_layout.addWidget(settings_group, 3)
		top_row_layout.addWidget(self.weight_group, 2)  # width ratio to match Pie Chart
		left_layout.addLayout(top_row_layout)

		# --- Pie Chart below (aligned with Settings + Weights) ---
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
		self.main_canvas.mpl_connect("button_press_event", self.on_frontier_press)
		self.main_canvas.mpl_connect("motion_notify_event", self.on_frontier_drag)
		self.main_canvas.mpl_connect("button_release_event", self.on_frontier_release)

		# Add left and right to main layout
		main_layout.addLayout(left_layout, 2)
		main_layout.addWidget(self.main_group, 3)

		self.update_all()
		self.set_bold_cb(self.tangency_cb, True) # Default is tangency point

		self.start_date_edit.clearFocus() # I don"t know why, but you start focused here

	def update_all(self, include_frontier=True):
		self.set_bold_cb(self.tangency_cb, False)
		self.set_bold_cb(self.gmv_cb, False)
		self.update_weights()
		self.update_stats()
		self.update_pie_chart()
		if include_frontier:
			self.update_main_plot()

	def on_points_changed(self, value):
		self.points = value

	def on_gmv_clicked(self):
		self.clear_marker()
		self.current_portfolio = Portfolio.min_variance_portfolio(self.portfolio_data, (0, self.bounds_max))
		self.update_all(False)
		self.set_bold_cb(self.gmv_cb, True)

	def on_tp_clicked(self):
		self.clear_marker()
		self.current_portfolio = Portfolio.max_sharpe_portfolio(self.portfolio_data, (0, self.bounds_max))
		self.update_all(False)
		self.set_bold_cb(self.tangency_cb, True)

	def set_bold_cb(self, cb: QCheckBox, bold: bool):
		font = cb.font()
		font.setBold(bold)
		cb.setFont(font)

	def clear_marker(self):
		if hasattr(self, "_selected_marker") and self._selected_marker:
			try:
				self._selected_marker.remove()
			except ValueError:
				# Already removed
				pass
			self._selected_marker = None

		# Redraw the canvas after removing
		if hasattr(self, "canvas"):
			self.canvas.draw_idle()

	def on_render_clicked(self):
		self.cml_cb.setChecked(True)
		self.gmv_cb.setChecked(True)
		self.tangency_cb.setChecked(True)

		self.current_portfolio = Portfolio.max_sharpe_portfolio(self.portfolio_data, (0, self.bounds_max))
		self.clear_marker()
		self.update_all()
		self.set_bold_cb(self.tangency_cb, True)

	def set_point(self, event, check_distance=True):
		self.mouse_down_graph = True
		ax = event.inaxes
		y = event.y
		if not hasattr(ax, "frontier_portfolios"):
			return 

		trans = ax.transData
		click_range = 8  # pixels
		min_dist = float("inf")
		nearest_idx = None

		# Uses y-coordinate ONLY for nearest point search
		for i, portfolio in enumerate(ax.frontier_portfolios):
			x_data, y_data = ax.frontier_risks[i], ax.frontier_returns[i]
			_, y_pix = trans.transform((x_data, y_data))
			dist = abs(y_pix - y)
			if dist < min_dist:
				min_dist = dist
				nearest_idx = i

		if min_dist <= click_range:
			self.current_portfolio = ax.frontier_portfolios[nearest_idx]

			self.update_all(False)

			self.highlight_selected_point(
				ax.frontier_risks[nearest_idx], 
				ax.frontier_returns[nearest_idx]
			)

	def export_weights(self, checked):
		# Keys are tickers, values are weights
		file_path, _ = QFileDialog.getSaveFileName(self, "Save Portfolio Weights to CSV", "", "CSV Files (*.csv);;All Files (*)")
		if not file_path:
			return  # User cancelled the dialog

		if not file_path.lower().endswith(".csv"):
			file_path += ".csv"

		with open(file_path, mode="w", newline="") as csv_file:
			writer = csv.writer(csv_file)
			writer.writerow(["ticker", "weight"])
			for ticker, weight in zip(self.tickers, self.current_portfolio.weights):
				# Skip very small weights
				if weight < small_threshold:
					continue
				writer.writerow([ticker, f"{weight:.6f}"])

	def on_frontier_press(self, event):
		if event.inaxes is None:
			return 

		self.set_point(event)
		

	def on_frontier_drag(self, event):
		if not self.mouse_down_graph:
			return
		if event.inaxes is None:
			return 

		self.set_point(event, check_distance=False)

	def on_frontier_release(self, event):
		self.mouse_down_graph = False

	def highlight_selected_point(self, risk, ret):
		ax = self.main_fig.axes[0]
		self.clear_marker()

		self._selected_marker = ax.scatter(
			risk, ret,
			s=120,
			facecolors="none",
			edgecolors="black",
			linewidths=2,
			zorder=4
		)
		self.main_canvas.draw_idle()

	def update_stats(self):
		p = self.current_portfolio

		self.exp_return_label.setText(f"{p.expected_return * 100:.2f}%")
		self.exp_vol_label.setText(f"{p.expected_volatility * 100:.2f}%")
		self.exp_sharpe_label.setText(f"{p.expected_sharpe_ratio:.2f}")

	def slider_changed(self, value):
		self.bounds_max = value/100
		self.slider_text.blockSignals(True)
		self.slider_text.setText(f"{value:.0f}%")
		self.slider_text.blockSignals(False)

	def slider_text_changed(self):
		try:
			val = float(self.slider_text.text())
			val = max(0, min(val, 1))  # clamp between 0 and 1
			self.bounds_max = val
			text = self.slider_text.text()

			if "." in text: # Minimum 2 decimals
				decimals = max(2, len(text.split(".")[1]))
			else:
				decimals = 2

			self.slider.blockSignals(True)
			self.slider_text.setText(f"{val:.{decimals}f}")
			self.slider.setValue(int(val * 100))
			self.slider.blockSignals(False)	
		except ValueError: # Incorrect input -> 1.00
			self.slider.blockSignals(True)
			self.slider_text.setText(f"{1:.2f}")
			self.slider.setValue(int(1 * 100))
			self.slider.blockSignals(False)	
		finally:
			self.slider_text.clearFocus()

	def toggle_artists(self):
		self.efficient_artists["CML"].set_visible(self.cml_cb.isChecked())
		self.efficient_artists["Tangency"].set_visible(self.tangency_cb.isChecked())
		self.efficient_artists["GMV"].set_visible(self.gmv_cb.isChecked())
		self.main_canvas.draw_idle()

	def update_weights(self):
		self.weight_list.clear()
		weights = self.current_portfolio.weights
		for i, ticker in enumerate(self.tickers):
			if weights[i] < small_threshold:
				continue
			item = QListWidgetItem(f"{ticker}: {weights[i]*100:.2f}%")
			self.weight_list.addItem(item)

	def on_start_changed(self, date):
		self.end_date_edit.setMinimumDate(date)
		self.start_date = qdate_to_datetime(date)
		self.update_portfolio_data()
		self.start_date_edit.clearFocus()

	def on_end_changed(self, date):
		self.start_date_edit.setMaximumDate(date)
		self.end_date = qdate_to_datetime(date)
		self.update_portfolio_data()
		self.end_date_edit.clearFocus()

	# DOESN"T rerender graphs, just changed internal portfolio_data
	def update_portfolio_data(self):
		self.portfolio_data = PortfolioData(self.tickers, self.start_date, self.end_date)

	def update_main_plot(self):
		bounds = (0, self.bounds_max)
		self.main_fig.clf()
		ax = self.main_fig.add_subplot(111)
		self.current_portfolio = Portfolio.max_sharpe_portfolio(self.portfolio_data, bounds) # Set new portfolio

		show_cml = self.cml_cb.isChecked()
		show_gmv = self.gmv_cb.isChecked()
		show_tangency = self.tangency_cb.isChecked()

		self.efficient_artists = plot_efficient_frontier(ax, self.portfolio_data, bounds, 
													show_cml=show_cml, show_gmv=show_gmv, show_tangency=show_tangency, points=self.points*2)
		self.toggle_artists()

	def update_pie_chart(self):
		ax = self.pie_fig.clf()
		ax = self.pie_fig.add_subplot(111)
		plot_pie_chart(ax, self.tickers, self.current_portfolio.weights)
		self.pie_canvas.draw_idle()

def qdate_to_datetime(qdate):
	return datetime(qdate.year(), qdate.month(), qdate.day())

def datetime_to_qdate(datetime):
	return QDate(datetime.year, datetime.month, datetime.day) 