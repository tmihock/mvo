# Assumes 252 trading days in a year
#
# Tristan Mihocko
import csv
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from scipy.optimize import minimize
from matplotlib import pyplot as plt
from fredapi import Fred
import mvo_calc as mvo
from typing import List, Tuple, Optional

def main():
	tickers = parse_tickers('example.csv')

	end_date = datetime.now() # Today
	start_date = end_date - timedelta(days=5*365) # Five years ago
 
	optimal_portfolio = mvo.get_optimal_weights(tickers, start=start_date, end=end_date)
 
	print(optimal_portfolio)
 
	
	
# Print expected return, volatility, sharpe ratio from optimal weights
def print_analytics(optimal_weights, log_returns, covariance_matrix, risk_free_rate):
	optimal_portfolio_return = mvo.expected_returns(optimal_weights, log_returns)
	optimal_portfolio_volatility = mvo.portfolio_risk(optimal_weights, covariance_matrix)
	optimal_sharpe_ratio = mvo.sharpe_ratio(optimal_weights, log_returns, covariance_matrix, risk_free_rate)

 
# Read csv file and return a list of tickers
def parse_tickers(file_path) -> List[str]:
	tickers = []
	with open('example.csv', mode='r') as file:
		csv_reader = csv.DictReader(file)

		for row in csv_reader:
			tickers.append(row['ticker'])
   
	return tickers

if __name__ == "__main__":
	main()