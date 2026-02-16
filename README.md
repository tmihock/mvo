# Mean-Variance Portfolio Optimization

A powerful Python application for portfolio optimization, implementing Mean-Variance Optimization (MVO) with a PyQt6 interface. Quickly find the optimal asset allocation based on historical market data.

## Key Features

### 📊 Smart Portfolio Optimization

- **Efficient Frontier Visualization** - Instantly see the optimal risk-return tradeoff for your portfolio
- **One-Click Optimization** - Find the best portfolios with a single click:
  - 🎯 **Maximum Sharpe Ratio** - Optimal risk-adjusted returns
  - 🛡️ **Minimum Variance** - Lowest possible risk
  - 🎯 **Custom Targets** - Choose any portfolio along the efficient frontier

### ⚙️ Customization

- **Flexible Time Frames** - Analyze performance across different market conditions
- **Risk Management** - Set maximum allocation per asset to prevent over-concentration
- **Advanced Controls**:
  - Adjust risk-free rate for precise Sharpe ratio calculations
  - Fine-tune the efficient frontier resolution
  - Set custom weight constraints

### 📈 Data-Driven Insights

- Analysis on historical market data
- Real-time portfolio statistics
- Clear visualization of asset allocations

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/tmihock/mvo
cd mvo
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Prepare your ticker list in a CSV file

```csv
tickers
AAPL
MSFT
GOOGL
AMZN
TSLA
```

### 4. Run the application

```bash
python src/main.py your_tickers.csv
```

## Requirements

- Python 3.8+
- PyQt6
- pandas
- numpy
- matplotlib
- yfinance
- scipy

## License

This project is licensed under the [MIT License](LICENSE)
