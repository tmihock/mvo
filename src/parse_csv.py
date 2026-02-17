from typing import Tuple 
from csv import DictReader

# Read csv file and return a list of tickers
def parse_tickers(file_path) -> Tuple[str]:
	tickers = []
	with open(file_path, mode="r") as file:
		csv_reader = DictReader(file)

		for row in csv_reader:
			tickers.append(row["ticker"])
   
	return tuple(tickers)
