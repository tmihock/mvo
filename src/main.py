# Assumes 252 trading days in a year
#
# Tristan Mihocko
import csv
from datetime import datetime, timedelta
from mvo_calc import max_sharpe_portfolio, expected_returns, portfolio_risk, sharpe_ratio, fred_risk_free_rate
from typing import List, Tuple, Optional
from plot import plot_efficient_frontier

def main():
	tickers = parse_tickers('example.csv')

	end_date = datetime.now() # Today
	start_date = end_date - timedelta(days=5*365) # Five years ago
 
	optimal_portfolio = max_sharpe_portfolio(tickers, start=start_date, end=end_date, risk_free_rate=fred_risk_free_rate())
 
	print("Tangency Portfolio")
	print(optimal_portfolio)

	plot_efficient_frontier(tickers, start=start_date, end=end_date, points=100)
 
	
	
# Print expected return, volatility, sharpe ratio from optimal weights
def print_analytics(optimal_weights, log_returns, covariance_matrix, risk_free_rate):
	optimal_portfolio_return = expected_returns(optimal_weights, log_returns)
	optimal_portfolio_volatility = portfolio_risk(optimal_weights, covariance_matrix)
	optimal_sharpe_ratio = sharpe_ratio(optimal_weights, log_returns, covariance_matrix, risk_free_rate)

 
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