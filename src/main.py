# Assumes 252 trading days in a year
#
# Tristan Mihocko
import sys
from app import PortfolioWindow
from PyQt6.QtWidgets import QApplication
from parse_csv import parse_tickers

file_path = "example.csv"

def main():
	tickers = parse_tickers(file_path)

	app = QApplication(sys.argv)
	window = PortfolioWindow(tickers)
	window.show()
	sys.exit(app.exec())
	

if __name__ == "__main__":
	main()