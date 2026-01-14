from view import View, AbsoluteView, RelativeView
import yaml
from typing import List, Tuple

# Black litterman model implementation
def parse_yaml(file_path) -> Tuple[List[str], List[str]]:
	tickers = []
	views = []

	with open(file_path, 'r') as file:
		config = yaml.safe_load(file)
		for ticker in config['tickers']:
			tickers.append(ticker)

		for view in config['views']:
			match view['type']:
				case 'absolute':
					views.append(AbsoluteView(view))
				case 'relative':
					views.append(RelativeView(view))
				case _:
					raise ValueError("Invalid view type in YAML")
	return tickers, views, config['risk_aversion']
 