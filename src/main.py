# Assumes 252 trading days in a year
#
# Tristan Mihocko
import sys
from app import PortfolioWindow
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication
from parse_csv import parse_tickers
from todos import PortfolioWindow as pf
from mvo_calc import fred_risk_free_rate

def main():
	tickers = parse_tickers('example.csv')

	end_date = datetime.now() # Today
	start_date = end_date - timedelta(days=5*365) # Five years ago
	
	app = QApplication(sys.argv)
	window = pf(tickers, start_date, end_date)
	# window = PortfolioWindow(tickers, start_date, end_date)
	window.show()
	sys.exit(app.exec())
	

	# optimal_portfolio = max_sharpe_portfolio(tickers, start=start_date, end=end_date, risk_free_rate=fred_risk_free_rate())

	# plot_pie_chart(tickers, optimal_portfolio.weights)

	# print("Tangency Portfolio")
	# print(optimal_portfolio)

	# plot_efficient_frontier(tickers, start=start_date, end=end_date, points=100)
 
	

if __name__ == "__main__":
	main()