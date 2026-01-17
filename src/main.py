# Assumes 252 trading days in a year
#
# Tristan Mihocko
import sys
from app import PortfolioWindow
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication
from parse_csv import parse_tickers
from tester import TesterWindow
from app import PortfolioWindow
from mvo_calc import fred_risk_free_rate

def main():
	tickers = parse_tickers('example.csv')

	end_date = datetime.now() # Today
	start_date = end_date - timedelta(days=5*365) # Five years ago
	
	app = QApplication(sys.argv)
	# window = PortfolioWindow(tickers, start_date, end_date)
	window = TesterWindow(tickers, start_date, end_date)
	window.show()
	sys.exit(app.exec())
	

if __name__ == "__main__":
	main()