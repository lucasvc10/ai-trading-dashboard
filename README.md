# 📈 Professional Trading Dashboard

A professional Streamlit-based trading dashboard with real-time stock data, technical analysis, and interactive charts.

## 🚀 Features

- **Ticker Input**: Search any stock ticker symbol
- **Live Stock Data**: Real-time data powered by yfinance
- **Interactive Charts**: Plotly-based interactive visualizations
- **Technical Indicators**:
  - 5-day Moving Average
  - 10-day Moving Average
  - Buy/Sell signal markers
- **Dark Finance Theme**: Professional dark UI optimized for trading
- **Sidebar Controls**: Easy-to-use control panel for indicators
- **Key Metrics**: Display of current price, high, low, and period change
- **Trading Signals**: BUY, SELL, or HOLD recommendations based on MA crossover strategy
- **Statistics Table**: Detailed trading metrics

## 📦 Installation

1. **Clone or download the project**
   ```bash
   cd trading-agent
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ Running the Dashboard

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## 🎮 How to Use

1. **Enter a Stock Ticker**: Type any stock symbol (e.g., AAPL, GOOGL, MSFT)
2. **Select Time Period**: Choose from 1 month, 3 months, 6 months, or 1 year
3. **Toggle Indicators**: Use checkboxes to show/hide moving averages and signals
4. **Analyze the Chart**: Hover over the chart for detailed information
5. **Check the Signal**: View the current trading recommendation (BUY/SELL/HOLD)

## 📊 Understanding the Dashboard

### Key Metrics
- **Current Price**: Latest closing price
- **Period Change**: Percentage change over selected period
- **Period High/Low**: Highest and lowest prices in the period

### Trading Signals
- **BUY Signal** (Green ▲): When 5-day MA > 10-day MA
- **SELL Signal** (Red ▼): When 5-day MA < 10-day MA
- **HOLD Signal** (Orange): When MAs are aligned

### Moving Averages
- **5-Day MA** (Green): Faster, more responsive indicator
- **10-Day MA** (Orange): Slower, smoother trend line

## 💡 Trading Strategy

This dashboard uses a simple **Moving Average Crossover Strategy**:
- When the 5-day MA crosses above the 10-day MA → **BUY Signal**
- When the 5-day MA crosses below the 10-day MA → **SELL Signal**

## ⚠️ Disclaimer

This dashboard is for **educational purposes only**. It is not financial advice. Always conduct your own research and consult with a financial advisor before making trading decisions.

## 🛠️ Customization

You can easily customize:
- **Color Scheme**: Edit CSS in the `st.markdown()` section
- **Moving Average Periods**: Change window values in `rolling(window=X)`
- **Time Periods**: Add new periods to the selectbox
- **Additional Indicators**: Add more technical indicators as needed

## 📚 Dependencies

- **Streamlit**: Web application framework
- **yfinance**: Yahoo Finance data fetching
- **Plotly**: Interactive charting library
- **Pandas**: Data manipulation and analysis

## 🎓 Beginner-Friendly Code

The code is organized and well-commented with:
- Clear section headers
- Descriptive variable names
- Simple, readable logic
- Comprehensive comments for each section

Happy trading! 📈
