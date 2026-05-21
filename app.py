import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

import json
import os

### Beginner-friendly project structure
### The dashboard app stores persistent data in the storage folder.
### This keeps raw JSON storage separate from the main app code.
### Project structure note for beginners:
### - apps and logic stay in app.py for now
### - `storage/` keeps persistent JSON files like portfolio and watchlist
### - `agents/`, `data/`, `ui/`, and `utils/` are created for future organization

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
PORTFOLIO_FILE = os.path.join(STORAGE_DIR, "portfolio.json")
WATCHLIST_FILE = os.path.join(STORAGE_DIR, "watchlist.json")
JOURNAL_FILE = os.path.join(STORAGE_DIR, "journal.json")

def load_portfolio():
    # Ensure the portfolio file exists before trying to read it.
    # If the file is missing, create it with an empty portfolio.
    if not os.path.exists(PORTFOLIO_FILE):
        save_portfolio([])
        return []

    try:
        with open(PORTFOLIO_FILE, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        # If the file is corrupted or can't be read, reset it safely.
        save_portfolio([])
        return []


def save_portfolio(portfolio):
    # Write the portfolio to disk so holdings persist across refreshes.
    with open(PORTFOLIO_FILE, "w") as file:
        json.dump(portfolio, file, indent=4)


def load_watchlist():
    # Ensure the watchlist file exists before trying to read it.
    # If the file is missing, create it with an empty watchlist.
    if not os.path.exists(WATCHLIST_FILE):
        save_watchlist([])
        return []

    try:
        with open(WATCHLIST_FILE, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        save_watchlist([])
        return []


def save_watchlist(watchlist):
    # Write the watchlist to disk so it persists across app restarts.
    with open(WATCHLIST_FILE, "w") as file:
        json.dump(watchlist, file, indent=4)


def load_journal():
    # Load trade journal entries. Create empty if missing.
    if not os.path.exists(JOURNAL_FILE):
        save_journal([])
        return []
    try:
        with open(JOURNAL_FILE, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        save_journal([])
        return []


def save_journal(journal):
    # Write journal entries to disk so trades persist across app restarts.
    with open(JOURNAL_FILE, "w") as file:
        json.dump(journal, file, indent=4)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize saved state for portfolio and watchlist when app starts.
if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_portfolio()
if "watchlist" not in st.session_state:
    st.session_state.watchlist = load_watchlist()
if "ticker" not in st.session_state:
    st.session_state.ticker = "AAPL"
if "ticker_input" not in st.session_state:
    st.session_state.ticker_input = st.session_state.ticker

# Helper callback to update both ticker values from a watchlist click.
def select_watchlist_ticker(watch_ticker):
    st.session_state.ticker = watch_ticker
    st.session_state.ticker_input = watch_ticker

# Dark professional finance theme
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #0a0e14 0%, #151b28 100%);
    }
    .metric-card {
        background: #1e2738;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #00d4ff;
        margin-bottom: 10px;
    }
    .buy-signal {
        color: #00ff41;
        font-weight: bold;
    }
    .sell-signal {
        color: #ff4444;
        font-weight: bold;
    }
    .hold-signal {
        color: #ffaa00;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - CONTROLS
# ============================================================================
with st.sidebar:
    st.header("⚙️ Dashboard Controls")
    st.divider()
    
    # Ticker input
    ticker = st.text_input(
        "Stock Ticker",
        value=st.session_state.ticker_input,
        placeholder="Enter ticker (e.g., AAPL, GOOGL, MSFT)",
        help="Enter any valid stock ticker symbol",
        key="ticker_input"
    ).strip().upper()
    
    st.session_state.ticker = ticker
    
    # Period selection
    period = st.selectbox(
        "Select Time Period",
        options=["1mo", "3mo", "6mo", "1y"],
        index=0,
        help="Choose the time range for analysis"
    )

    st.divider()
    st.subheader("⭐ Watchlist")

    # Add a ticker to the saved watchlist
    new_watchlist_ticker = st.text_input(
        "Add Watchlist Ticker",
        placeholder="e.g., TSLA",
        key="new_watchlist_ticker"
    ).strip().upper()

    if st.button("➕ Add to Watchlist", use_container_width=True):
        if new_watchlist_ticker:
            if new_watchlist_ticker in st.session_state.watchlist:
                st.warning(f"{new_watchlist_ticker} is already in your watchlist.")
            else:
                st.session_state.watchlist.append(new_watchlist_ticker)
                save_watchlist(st.session_state.watchlist)
                st.success(f"✅ Added {new_watchlist_ticker} to watchlist.")
                st.rerun()
        else:
            st.error("⚠️ Enter a ticker symbol to add.")

    # Show saved tickers and allow quick selection or removal
    if st.session_state.watchlist:
        for watch_ticker in st.session_state.watchlist:
            watch_col1, watch_col2 = st.columns([3, 1])
            watch_col1.button(
                watch_ticker,
                key=f"watch_{watch_ticker}",
                on_click=select_watchlist_ticker,
                args=(watch_ticker,)
            )
            if watch_col2.button("Remove", key=f"remove_watch_{watch_ticker}"):
                st.session_state.watchlist = [
                    t for t in st.session_state.watchlist if t != watch_ticker
                ]
                save_watchlist(st.session_state.watchlist)
                st.success(f"✅ Removed {watch_ticker} from watchlist.")
                st.rerun()

    st.divider()
    st.subheader("📊 Technical Indicators")
    
    # Moving averages toggle
    show_ma5 = st.checkbox("Show 5-Day MA", value=True)
    show_ma10 = st.checkbox("Show 10-Day MA", value=True)
    
    # Signal markers
    show_signals = st.checkbox("Show Buy/Sell Signals", value=True)
    
    st.divider()
    st.info(
        "💡 **How to use:**\n"
        "- Enter a stock ticker\n"
        "- Select your time period\n"
        "- Toggle indicators on/off\n"
        "- Hover over chart for details"
    )

# ============================================================================
# MAIN DASHBOARD
# ============================================================================
st.title("📈 Professional Trading Dashboard")
st.markdown(
    f"Real-time stock analysis powered by yfinance | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

# ============================================================================
# MARKET OVERVIEW
# ----------------------------------------------------------------------------
# A compact market overview for active traders. Shows common market instruments
# (equities, volatility index, commodities) with current price and daily % change.
# Uses yfinance; errors are handled so the dashboard won't crash if a ticker fails.
# This is intentionally small and non-invasive so existing app logic stays intact.
# ============================================================================

# Performance optimizations: cached data fetchers to reduce API calls.
@st.cache_data(ttl=60)
def fetch_stock_history(ticker, period):
    """Fetch historical stock data. Cached for 60 seconds to improve performance."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        return data
    except Exception as e:
        raise e

@st.cache_data(ttl=60)
def fetch_live_stock_price(ticker):
    """Fetch current live price for a single ticker. Cached for 60 seconds."""
    try:
        hist = yf.Ticker(ticker).history(period="1d")
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None

st.subheader("🌎 Market Overview")

# Instruments to show: (display name, yfinance ticker)
MARKET_INSTRUMENTS = [
    ("S&P 500", "SPY"),
    ("Nasdaq 100", "QQQ"),
    ("Dow Jones", "DIA"),
    ("VIX", "^VIX"),
    ("Gold", "GC=F"),
    ("Crude Oil", "CL=F"),
    ("Natural Gas", "NG=F"),
]

@st.cache_data(ttl=60)
def fetch_instrument_summary(ticker):
    """Return (price, pct_change) or (None, None) on failure.
    Cached for 60 seconds to reduce API calls and improve dashboard speed.
    """
    try:
        hist = yf.Ticker(ticker).history(period="2d")
        if hist.empty:
            return None, None
        last = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2] if len(hist) > 1 else last
        pct = ((last - prev) / prev) * 100 if prev != 0 else 0
        return float(last), float(pct)
    except Exception:
        return None, None

# Display cards in a single responsive row. Each column is one instrument.
try:
    cols = st.columns(len(MARKET_INSTRUMENTS))
    for (name, ticker), col in zip(MARKET_INSTRUMENTS, cols):
        with col:
            price, pct = fetch_instrument_summary(ticker)
            if price is None:
                # Show a graceful placeholder if data is missing
                st.markdown(f"<div style='background: linear-gradient(135deg, #131820, #1f2935); padding: 12px; border-radius: 8px; text-align:center;'>\n  <div style='color: #b0b9c1; font-size:12px;'>{name} • {ticker}</div>\n  <div style='color: #ffffff; font-size:16px; font-weight:bold;'>N/A</div>\n  <div style='color: #ffaa00;'>Data unavailable</div>\n</div>", unsafe_allow_html=True)
            else:
                color = "#51cf66" if pct >= 0 else "#ff6b6b"
                sign = "+" if pct >= 0 else ""
                st.markdown(f"<div style='background: linear-gradient(135deg, #131820, #1f2935); padding: 12px; border-radius: 8px; border-left: 4px solid {color}; text-align:center;'>\n  <div style='color: #b0b9c1; font-size:12px;'>{name} • {ticker}</div>\n  <div style='color: #ffffff; font-size:18px; font-weight:bold;'>${price:.2f}</div>\n  <div style='color: {color}; font-weight:bold;'>{sign}{pct:.2f}%</div>\n</div>", unsafe_allow_html=True)
except Exception as e:
    # Non-fatal: show a simple warning but keep the app running
    st.warning(f"Market overview currently unavailable: {str(e)}")

# ============================================================================
# TOP MOVERS SCANNER
# ----------------------------------------------------------------------------
# Compact, beginner-friendly scanner showing today's biggest movers for a
# short list of popular tickers. Fetches last-close and previous-close via
# yfinance and sorts by daily % change (largest gain → largest loss).
# Errors are handled per-ticker so the app stays stable.
# ============================================================================
st.subheader("🔥 Top Movers Scanner")

# Example tickers to scan
MOVERS_TICKERS = ["NVDA", "TSLA", "META", "AMD", "PLTR", "AAPL", "MSFT", "AMZN"]

@st.cache_data(ttl=60)
def fetch_stock_change(ticker):
    """Return (price, pct_change) or (None, None) on failure.
    Cached for 60 seconds to reduce API calls and improve scanner speed.
    """
    try:
        hist = yf.Ticker(ticker).history(period="2d")
        if hist.empty:
            return None, None
        last = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2] if len(hist) > 1 else last
        pct = ((last - prev) / prev) * 100 if prev != 0 else 0
        return float(last), float(pct)
    except Exception:
        return None, None

# Gather data for all tickers (failures yield None values but won't crash)
movers = []
for t in MOVERS_TICKERS:
    price, pct = fetch_stock_change(t)
    movers.append((t, price, pct))

# Sort by pct change descending (biggest gain → biggest loss). Place missing
# data at the bottom.
movers_sorted = sorted(movers, key=lambda x: (x[2] is not None, x[2] if x[2] is not None else -1e9), reverse=True)

# Display in compact rows of 4 columns each for a professional look
cols_per_row = 4
for i in range(0, len(movers_sorted), cols_per_row):
    row = movers_sorted[i:i+cols_per_row]
    cols = st.columns(cols_per_row)
    for col, item in zip(cols, row):
        tkr, price, pct = item
        with col:
            if price is None:
                st.markdown(
                    """
                    <div style='background: linear-gradient(135deg, #131820, #1f2935); padding: 12px; border-radius: 8px; text-align:center;'>
                        <div style='color: #b0b9c1; font-size:12px;'>{}</div>
                        <div style='color: #ffffff; font-size:16px; font-weight:bold;'>N/A</div>
                        <div style='color: #ffaa00;'>Data unavailable</div>
                    </div>
                    """.format(tkr), unsafe_allow_html=True)
            else:
                color = "#51cf66" if pct >= 0 else "#ff6b6b"
                sign = "+" if pct >= 0 else ""
                st.markdown(
                    """
                    <div style='background: linear-gradient(135deg, #131820, #1f2935); padding: 12px; border-radius: 8px; border-left: 4px solid %s; text-align:center;'>
                        <div style='color: #b0b9c1; font-size:12px;'>%s</div>
                        <div style='color: #ffffff; font-size:16px; font-weight:bold;'>$%.2f</div>
                        <div style='color: %s; font-weight:bold;'>%s%.2f%%</div>
                    </div>
                    """ % (color, tkr, price, color, sign, pct), unsafe_allow_html=True)


# ============================================================================
# TRADE ALERTS
# ============================================================================
# Simple rule-based alerts for the selected ticker. Shows technical warnings
# and opportunities based on RSI, moving averages, and volatility.
# No AI analysis; just beginner-friendly trading indicators.
# ============================================================================
st.subheader("🚨 Trade Alerts")

# Function to generate alerts based on simple technical rules
def generate_trade_alerts(ticker):
    """
    Generate simple trading alerts for the selected ticker.
    Returns a list of alert dictionaries with: message, type (bullish/bearish/caution), explanation
    Safe to call; handles missing data gracefully.
    """
    alerts = []
    
    try:
        # Fetch recent data (5 days to calculate volatility)
        hist_data = yf.Ticker(ticker).history(period="5d")
        
        if hist_data.empty or len(hist_data) < 2:
            # Not enough data; return empty alerts gracefully
            return alerts
        
        close_prices = hist_data["Close"]
        
        # Get current and previous close
        current_price = close_prices.iloc[-1]
        previous_close = close_prices.iloc[-2]
        
        # Calculate daily percentage change
        daily_change = ((current_price - previous_close) / previous_close) * 100
        
        # ===== VOLATILITY ALERT =====
        if abs(daily_change) > 3:
            alert_type = "caution"  # Yellow/orange for high volatility
            symbol = "⚡"
            if daily_change > 3:
                message = f"High Volatility: Up {daily_change:.2f}% - Price moving fast"
            else:
                message = f"High Volatility: Down {abs(daily_change):.2f}% - Price moving fast"
            explanation = "Large daily moves can indicate increased risk or opportunity. Stay alert to market news."
            alerts.append({
                "message": message,
                "type": alert_type,
                "symbol": symbol,
                "explanation": explanation
            })
        
        # Calculate RSI (14-period)
        price_changes = close_prices.diff()
        gains = price_changes.clip(lower=0)
        losses = -price_changes.clip(upper=0)
        avg_gains = gains.rolling(window=14).mean()
        avg_losses = losses.rolling(window=14).mean()
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # ===== RSI ALERTS =====
        if current_rsi > 70:
            alert_type = "bearish"
            symbol = "📈"
            message = f"Overbought Alert: RSI = {current_rsi:.2f}"
            explanation = "RSI above 70 suggests the stock may have risen too quickly. Watch for potential pullback or profit-taking."
            alerts.append({
                "message": message,
                "type": alert_type,
                "symbol": symbol,
                "explanation": explanation
            })
        elif current_rsi < 30:
            alert_type = "bullish"
            symbol = "📉"
            message = f"Oversold Opportunity: RSI = {current_rsi:.2f}"
            explanation = "RSI below 30 suggests the stock may have fallen too far. This could be a buying opportunity if the trend reverses."
            alerts.append({
                "message": message,
                "type": alert_type,
                "symbol": symbol,
                "explanation": explanation
            })
        
        # Calculate moving averages for trend signals
        ma5 = close_prices.rolling(window=5).mean()
        ma10 = close_prices.rolling(window=10).mean()
        
        if len(ma5) >= 5 and len(ma10) >= 10:
            current_ma5 = ma5.iloc[-1]
            current_ma10 = ma10.iloc[-1]
            
            # ===== TREND ALERTS =====
            if current_price > current_ma5 and current_ma5 > current_ma10:
                alert_type = "bullish"
                symbol = "🟢"
                message = "Bullish Trend: Price above both moving averages"
                explanation = "Price is trading above both 5-day and 10-day MAs. This is a bullish setup for potential continued upside."
                alerts.append({
                    "message": message,
                    "type": alert_type,
                    "symbol": symbol,
                    "explanation": explanation
                })
            elif current_price < current_ma5 and current_ma5 < current_ma10:
                alert_type = "bearish"
                symbol = "🔴"
                message = "Bearish Trend: Price below both moving averages"
                explanation = "Price is trading below both 5-day and 10-day MAs. This is a bearish setup; caution advised on new long positions."
                alerts.append({
                    "message": message,
                    "type": alert_type,
                    "symbol": symbol,
                    "explanation": explanation
                })
    
    except Exception as e:
        # If data fetch fails, return empty list; don't crash the dashboard
        pass
    
    return alerts

# Generate alerts for the selected ticker
trade_alerts = generate_trade_alerts(ticker)

# Display alerts in colored cards
if trade_alerts:
    alert_cols = st.columns(1)
    
    for alert in trade_alerts:
        # Color scheme: green for bullish, red for bearish, yellow/orange for caution
        if alert["type"] == "bullish":
            bg_color = "#0d3a1a"  # Dark green
            border_color = "#51cf66"  # Bright green
            text_color = "#51cf66"
        elif alert["type"] == "bearish":
            bg_color = "#3a0d0d"  # Dark red
            border_color = "#ff6b6b"  # Bright red
            text_color = "#ff6b6b"
        else:  # caution
            bg_color = "#3a2a0d"  # Dark orange/yellow
            border_color = "#ffaa00"  # Orange/yellow
            text_color = "#ffaa00"
        
        # Display alert card
        st.markdown(f"""
        <div style='
            background: {bg_color};
            padding: 16px;
            border-radius: 10px;
            border-left: 5px solid {border_color};
            margin-bottom: 12px;
        '>
            <div style='display: flex; align-items: flex-start; gap: 12px;'>
                <div style='font-size: 24px; margin-top: -2px;'>{alert["symbol"]}</div>
                <div style='flex: 1;'>
                    <p style='color: {text_color}; font-weight: bold; margin: 0; font-size: 16px;'>{alert["message"]}</p>
                    <p style='color: #b0b9c1; margin: 8px 0 0 0; font-size: 14px;'>{alert["explanation"]}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info(f"ℹ️ No major alerts for {ticker} at this time. Market conditions appear neutral.")


# Fetch data
try:
    with st.spinner(f"📥 Fetching data for {ticker}..."):
        # Use cached function to reduce API calls and improve performance
        data = fetch_stock_history(ticker, period)
        
        if data.empty:
            st.error(f"❌ No data found for ticker: {ticker}")
            st.stop()
        
        # Calculate indicators
        close_prices = data["Close"]
        ma5 = close_prices.rolling(window=5).mean()
        ma10 = close_prices.rolling(window=10).mean()
        
        # Generate signals
        buy_signal = ma5 > ma10
        sell_signal = ma5 < ma10
        
        # Current signal
        if ma5.iloc[-1] > ma10.iloc[-1]:
            signal = "BUY"
            signal_color = "#00ff41"
        elif ma5.iloc[-1] < ma10.iloc[-1]:
            signal = "SELL"
            signal_color = "#ff4444"
        else:
            signal = "HOLD"
            signal_color = "#ffaa00"
    
except Exception as e:
    st.error(f"❌ Error fetching data: {str(e)}")
    st.stop()

# ============================================================================
# KEY METRICS
# ============================================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    current_price = close_prices.iloc[-1]
    st.metric(
        "Current Price",
        f"${current_price:.2f}",
        f"{(current_price - close_prices.iloc[-2]):.2f}",
        delta_color="inverse"
    )

with col2:
    price_change = ((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]) * 100
    st.metric(
        "Period Change",
        f"{price_change:.2f}%",
        delta_color="inverse"
    )

with col3:
    high_price = close_prices.max()
    st.metric("Period High", f"${high_price:.2f}")

with col4:
    low_price = close_prices.min()
    st.metric("Period Low", f"${low_price:.2f}")

# Trading signal display
st.divider()
signal_html = f"""
<div style='
    background: linear-gradient(135deg, #1e2738, #2a3447);
    padding: 25px;
    border-radius: 10px;
    border-left: 5px solid {signal_color};
    text-align: center;
'>
    <h3 style='color: #ffffff; margin: 0;'>Current Trading Signal</h3>
    <h1 style='color: {signal_color}; margin: 10px 0;'>{signal}</h1>
    <p style='color: #b0b9c1; margin: 0;'>
        5-Day MA: ${ma5.iloc[-1]:.2f} | 10-Day MA: ${ma10.iloc[-1]:.2f}
    </p>
</div>
"""
st.markdown(signal_html, unsafe_allow_html=True)

# ============================================================================
# INTERACTIVE CHART
# ============================================================================
st.subheader("📊 Price Chart with Technical Indicators")

# Create interactive chart
fig = go.Figure()

# Close price line
fig.add_trace(go.Scatter(
    x=data.index,
    y=close_prices,
    name="Close Price",
    line=dict(color="#00d4ff", width=2.5),
    hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> $%{y:.2f}<extra></extra>"
))

# 5-Day MA
if show_ma5:
    fig.add_trace(go.Scatter(
        x=data.index,
        y=ma5,
        name="5-Day MA",
        line=dict(color="#00ff41", width=2, dash="dash"),
        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>MA5:</b> $%{y:.2f}<extra></extra>"
    ))

# 10-Day MA
if show_ma10:
    fig.add_trace(go.Scatter(
        x=data.index,
        y=ma10,
        name="10-Day MA",
        line=dict(color="#ff8800", width=2, dash="dash"),
        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>MA10:</b> $%{y:.2f}<extra></extra>"
    ))

# Buy signals
if show_signals:
    buy_points = data.index[buy_signal]
    buy_prices = close_prices[buy_signal]
    fig.add_trace(go.Scatter(
        x=buy_points,
        y=buy_prices,
        mode="markers",
        name="Buy Signal",
        marker=dict(color="#00ff41", size=10, symbol="triangle-up"),
        hovertemplate="<b>BUY Signal</b><br><b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> $%{y:.2f}<extra></extra>"
    ))
    
    # Sell signals
    sell_points = data.index[sell_signal]
    sell_prices = close_prices[sell_signal]
    fig.add_trace(go.Scatter(
        x=sell_points,
        y=sell_prices,
        mode="markers",
        name="Sell Signal",
        marker=dict(color="#ff4444", size=10, symbol="triangle-down"),
        hovertemplate="<b>SELL Signal</b><br><b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> $%{y:.2f}<extra></extra>"
    ))

# Update layout with dark theme
fig.update_layout(
    title=f"{ticker} Stock Price Analysis",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    template="plotly_dark",
    hovermode="x unified",
    height=500,
    paper_bgcolor="rgba(15, 20, 25, 0)",
    plot_bgcolor="rgba(26, 31, 46, 0.5)",
    font=dict(color="#ffffff", size=12),
    xaxis=dict(
        gridcolor="rgba(255, 255, 255, 0.1)",
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="rgba(255, 255, 255, 0.1)",
        zeroline=False,
    ),
    legend=dict(
        bgcolor="rgba(30, 39, 56, 0.8)",
        bordercolor="#00d4ff",
        borderwidth=1,
    ),
)

st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# RSI (RELATIVE STRENGTH INDEX) INDICATOR
# ============================================================================
st.subheader("📊 RSI (Relative Strength Index) Indicator")

# Function to calculate RSI (Relative Strength Index)
# RSI measures momentum by comparing upward and downward price movements
# Range: 0-100 | Above 70 = Overbought (may sell) | Below 30 = Oversold (may buy)
@st.cache_data(ttl=60)
def calculate_rsi(prices, period=14):
    """
    Calculate Relative Strength Index (RSI)
    
    Parameters:
    - prices: Series of price data
    - period: Number of periods for RSI calculation (default 14)
    
    Returns:
    - RSI values as a pandas Series
    """
    # Calculate price changes from day to day
    price_changes = prices.diff()
    
    # Separate gains (positive changes) and losses (negative changes)
    gains = price_changes.clip(lower=0)  # Keep only positive values
    losses = -price_changes.clip(upper=0)  # Keep only negative values (as positive)
    
    # Calculate average gains and losses over the period
    avg_gains = gains.rolling(window=period).mean()
    avg_losses = losses.rolling(window=period).mean()
    
    # Calculate RS (Relative Strength) and RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

# Calculate RSI with 14-day period (standard for technical analysis)
rsi = calculate_rsi(close_prices, period=14)

# Create RSI chart
rsi_fig = go.Figure()

# RSI line
rsi_fig.add_trace(go.Scatter(
    x=data.index,
    y=rsi,
    name="RSI (14)",
    line=dict(color="#00d4ff", width=2.5),
    hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>RSI:</b> %{y:.2f}<extra></extra>"
))

# Overbought zone (RSI > 70) - red background
rsi_fig.add_hline(
    y=70,
    line_dash="dash",
    line_color="#ff6b6b",
    annotation_text="Overbought (70)",
    annotation_position="right",
)
rsi_fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255, 107, 107, 0.1)", layer="below", line_width=0)

# Oversold zone (RSI < 30) - green background
rsi_fig.add_hline(
    y=30,
    line_dash="dash",
    line_color="#51cf66",
    annotation_text="Oversold (30)",
    annotation_position="right",
)
rsi_fig.add_hrect(y0=0, y1=30, fillcolor="rgba(81, 207, 102, 0.1)", layer="below", line_width=0)

# Neutral zone (30-70)
rsi_fig.add_hline(y=50, line_dash="dot", line_color="rgba(255, 255, 255, 0.2)", line_width=1)

# Update RSI chart layout with dark theme
rsi_fig.update_layout(
    title=f"{ticker} RSI (14-Period) - Momentum Indicator",
    xaxis_title="Date",
    yaxis_title="RSI Value (0-100)",
    template="plotly_dark",
    hovermode="x unified",
    height=350,
    paper_bgcolor="rgba(15, 20, 25, 0)",
    plot_bgcolor="rgba(26, 31, 46, 0.5)",
    font=dict(color="#ffffff", size=12),
    xaxis=dict(
        gridcolor="rgba(255, 255, 255, 0.1)",
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="rgba(255, 255, 255, 0.1)",
        zeroline=False,
        range=[0, 100],  # RSI always ranges from 0 to 100
    ),
    legend=dict(
        bgcolor="rgba(30, 39, 56, 0.8)",
        bordercolor="#00d4ff",
        borderwidth=1,
    ),
)

st.plotly_chart(rsi_fig, use_container_width=True)

# Display current RSI interpretation
col1, col2, col3 = st.columns(3)

current_rsi = rsi.iloc[-1]

# Determine RSI status
if current_rsi > 70:
    rsi_status = "📈 Overbought"
    rsi_message = "Price may have risen too fast. Potential pullback or sell signal."
    rsi_status_color = "#ff6b6b"
elif current_rsi < 30:
    rsi_status = "📉 Oversold"
    rsi_message = "Price may have fallen too much. Potential bounce or buy signal."
    rsi_status_color = "#51cf66"
else:
    rsi_status = "⚖️ Neutral"
    rsi_message = "Momentum is balanced. No extreme conditions."
    rsi_status_color = "#ffaa00"

with col1:
    st.metric("Current RSI", f"{current_rsi:.2f}")

with col2:
    st.markdown(f"""
    <div style='
        background: linear-gradient(135deg, #1e2738, #2a3447);
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid {rsi_status_color};
        text-align: center;
    '>
        <h4 style='color: {rsi_status_color}; margin: 0;'>{rsi_status}</h4>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.info(f"💡 {rsi_message}")

# RSI explanation
with st.expander("ℹ️ What is RSI?"):
    st.markdown("""
    **Relative Strength Index (RSI)** is a momentum indicator that measures the strength of price movements.
    
    **How it works:**
    - Compares average gains and losses over 14 periods
    - Ranges from 0 to 100
    
    **Interpretation:**
    - **Above 70**: Overbought - Price may be too high, potential sell opportunity
    - **Below 30**: Oversold - Price may be too low, potential buy opportunity
    - **30-70**: Neutral - Normal price action
    
    **Use with Moving Averages:**
    - RSI confirms trends: Uptrend with RSI > 50 is strong
    - Divergences: Price makes new high but RSI doesn't = potential reversal
    - Use RSI with MA crossovers for better signals
    """)

# ============================================================================
# STATISTICS TABLE
# ============================================================================
st.subheader("📋 Trading Statistics")

stats_data = {
    "Metric": [
        "Current Price",
        "Highest Price (Period)",
        "Lowest Price (Period)",
        "Average Price",
        "5-Day MA",
        "10-Day MA",
        "Trading Signal",
        "Days Analyzed"
    ],
    "Value": [
        f"${close_prices.iloc[-1]:.2f}",
        f"${close_prices.max():.2f}",
        f"${close_prices.min():.2f}",
        f"${close_prices.mean():.2f}",
        f"${ma5.iloc[-1]:.2f}",
        f"${ma10.iloc[-1]:.2f}",
        signal,
        f"{len(data)} days"
    ]
}

stats_df = pd.DataFrame(stats_data)
st.dataframe(stats_df, use_container_width=True, hide_index=True)

# ============================================================================
# AI TRADING INSIGHTS
# ============================================================================

@st.cache_data(ttl=60)
def generate_ai_insights(current_price, ma5_value, ma10_value, rsi_value, signal):
    """
    Create simple rule-based market commentary using current indicators.
    This function returns a beginner-friendly sentiment and two message cards.
    """
    price_trend = "bullish" if current_price > ma5_value and ma5_value > ma10_value else "bearish" if current_price < ma5_value and ma5_value < ma10_value else "neutral"
    rsi_condition = "overbought" if rsi_value > 70 else "oversold" if rsi_value < 30 else "balanced"

    if signal == "BUY" and price_trend == "bullish" and rsi_condition != "overbought":
        sentiment = "Bullish"
        summary = "Price is above both moving averages and the chart looks constructive."
        detail = "Momentum is positive, and RSI is not yet overbought. This suggests strength while the trend holds."
        color = "#1f7a1f"
    elif signal == "SELL" and price_trend == "bearish" and rsi_condition != "oversold":
        sentiment = "Bearish"
        summary = "Price is below both moving averages and the trend is weak."
        detail = "Momentum is negative, and RSI is not deeply oversold. Caution is advised on new long positions."
        color = "#7a1f1f"
    elif signal == "BUY" and rsi_condition == "overbought":
        sentiment = "Cautious Bullish"
        summary = "The uptrend is present but RSI is extended."
        detail = "A pullback could happen soon, so watch support levels closely."
        color = "#7a7a1f"
    elif signal == "SELL" and rsi_condition == "oversold":
        sentiment = "Cautious Bearish"
        summary = "The downtrend is visible, but RSI is stretched low."
        detail = "A short-term bounce may occur before the next move."
        color = "#7a4f1f"
    else:
        sentiment = "Neutral"
        summary = "The indicators are mixed and the market may be consolidating."
        detail = "Wait for a clearer setup before taking new action, and use both MAs and RSI for confirmation."
        color = "#4f4f4f"

    return sentiment, summary, detail, color


insight_sentiment, insight_summary, insight_detail, insight_color = generate_ai_insights(
    current_price,
    ma5.iloc[-1],
    ma10.iloc[-1],
    current_rsi,
    signal
)

st.subheader("🤖 AI Trading Insights")
insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #131820, #1f2935); padding: 20px; border-radius: 12px; border-left: 5px solid {insight_color};'>
        <h3 style='color: #ffffff; margin: 0;'>Market Sentiment</h3>
        <p style='color: {insight_color}; font-size: 22px; margin: 10px 0 0 0;'>{insight_sentiment}</p>
        <p style='color: #b0b9c1; margin: 10px 0 0 0;'>{insight_summary}</p>
    </div>
    """, unsafe_allow_html=True)

with insight_col2:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #131820, #1f2935); padding: 20px; border-radius: 12px; border-left: 5px solid {insight_color};'>
        <h3 style='color: #ffffff; margin: 0;'>What the indicators say</h3>
        <p style='color: #b0b9c1; margin: 12px 0 0 0;'>Signal: <strong>{signal}</strong></p>
        <p style='color: #b0b9c1; margin: 8px 0 0 0;'>MA5: <strong>${ma5.iloc[-1]:.2f}</strong></p>
        <p style='color: #b0b9c1; margin: 8px 0 0 0;'>MA10: <strong>${ma10.iloc[-1]:.2f}</strong></p>
        <p style='color: #b0b9c1; margin: 8px 0 0 0;'>RSI: <strong>{current_rsi:.2f}</strong></p>
        <p style='color: #ffffff; margin: 16px 0 0 0;'>{insight_detail}</p>
    </div>
    """, unsafe_allow_html=True)


def rate_news_sentiment(headline):
    """Assign a basic sentiment label based on headline keywords."""
    text = headline.lower()
    bullish_keywords = ["beat", "gain", "upgrade", "buy", "record", "optimistic", "rally", "strong"]
    bearish_keywords = ["miss", "drop", "downgrade", "sell", "warn", "cut", "weak", "decline"]
    if any(word in text for word in bullish_keywords):
        return "Bullish"
    if any(word in text for word in bearish_keywords):
        return "Bearish"
    return "Neutral"


def news_sentiment_color(sentiment):
    if sentiment == "Bullish":
        return "#51cf66"
    if sentiment == "Bearish":
        return "#ff6b6b"
    return "#ffaa00"


@st.cache_data(ttl=60)
def fetch_stock_news(ticker, max_items=5):
    """Fetch recent news headlines for the selected ticker using yfinance.
    Cached for 60 seconds to reduce API load.
    """
    try:
        stock = yf.Ticker(ticker)
        raw_news = getattr(stock, "news", []) or []
    except Exception:
        return []

    news_items = []
    for item in raw_news[:max_items]:
        content = item.get("content") or {}
        headline = content.get("title") or item.get("title") or item.get("headline") or "Headline unavailable"
        provider = content.get("provider") or {}
        publisher = (
            provider.get("displayName")
            or item.get("publisher")
            or item.get("providerPublishSource")
            or "Unknown"
        )
        click_url = content.get("clickThroughUrl") or {}
        canonical_url = content.get("canonicalUrl") or {}
        link = (
            click_url.get("url")
            or canonical_url.get("url")
            or item.get("link")
            or item.get("url")
            or ""
        )
        published_date = "Unknown date"
        pub_date_raw = content.get("pubDate") or content.get("displayTime") or item.get("providerPublishTime")
        if isinstance(pub_date_raw, int):
            published_date = datetime.fromtimestamp(pub_date_raw).strftime("%Y-%m-%d %H:%M")
        elif isinstance(pub_date_raw, str) and pub_date_raw:
            try:
                published_date = datetime.fromisoformat(pub_date_raw.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
            except ValueError:
                published_date = pub_date_raw

        sentiment = rate_news_sentiment(headline)
        news_items.append({
            "headline": headline,
            "publisher": publisher,
            "published_date": published_date,
            "sentiment": sentiment,
            "color": news_sentiment_color(sentiment),
            "link": link,
        })
    return news_items


st.subheader("📰 Stock News & Sentiment")
news_items = fetch_stock_news(ticker)

if news_items:
    for article in news_items:
        headline_html = f"<a href='{article['link']}' target='_blank' style='color: #00d4ff; text-decoration: none;'>{article['headline']}</a>" if article['link'] else article['headline']
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #131820, #1f2935); padding: 18px; border-radius: 12px; border-left: 5px solid {article['color']}; margin-bottom: 12px;'>
            <p style='color: #ffffff; font-weight: bold; margin: 0;'>{headline_html}</p>
            <p style='color: #b0b9c1; margin: 6px 0 0 0;'>Publisher: {article['publisher']} • {article['published_date']}</p>
            <p style='color: {article['color']}; margin: 8px 0 0 0; font-weight: bold;'>Sentiment: {article['sentiment']}</p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("📰 No recent news headlines available for this ticker.")

# ============================================================================
# PORTFOLIO TRACKER SECTION
# ============================================================================
st.divider()
st.title("💼 Portfolio Tracker")

# Initialize session state for portfolio holdings
if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_portfolio()

# Portfolio input section in sidebar
with st.sidebar:
    st.divider()
    st.subheader("➕ Add Holdings")
    
    # Input fields for new holding
    col_ticker, col_shares = st.columns(2)
    
    with col_ticker:
        new_ticker = st.text_input(
            "Ticker Symbol",
            key="new_ticker",
            placeholder="e.g., AAPL"
        ).upper()
    
    with col_shares:
        new_shares = st.number_input(
            "Shares Owned",
            key="new_shares",
            min_value=0.0,
            step=0.1,
            value=0.0
        )
    
    new_avg_price = st.number_input(
        "Average Buy Price ($)",
        key="new_avg_price",
        min_value=0.0,
        step=0.01,
        value=0.0
    )
    
    # Button to add holding
    col_add, col_clear = st.columns(2)
    
    with col_add:
        if st.button("➕ Add Holding", use_container_width=True):
            if new_ticker and new_shares > 0 and new_avg_price > 0:
                # Check if ticker already exists
                existing = [h for h in st.session_state.portfolio if h["ticker"] == new_ticker]
                if existing:
                    st.warning(f"{new_ticker} already in portfolio!")
                else:
                    st.session_state.portfolio.append({
                        "ticker": new_ticker,
                        "shares": new_shares,
                        "avg_price": new_avg_price
                    })
                    
                    save_portfolio(st.session_state.portfolio)
                    st.success(f"✅ Added {new_ticker}!")
                    st.rerun()
            else:
                st.error("⚠️ Please fill all fields correctly")
    
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.portfolio = []
            save_portfolio(st.session_state.portfolio)
            st.rerun()

# Display portfolio section
if st.session_state.portfolio:
    
    # Fetch live data for all holdings
    portfolio_data = []
    total_investment = 0
    total_current_value = 0
    
    with st.spinner("📊 Fetching live prices..."):
        for holding in st.session_state.portfolio:
            try:
                # Use cached function to reduce API calls for portfolio prices
                live_price = fetch_live_stock_price(holding["ticker"])
                
                if live_price is None:
                    st.error(f"❌ Could not fetch price for {holding['ticker']}")
                    continue
                
                # Calculate metrics
                shares = holding["shares"]
                avg_price = holding["avg_price"]
                current_value = shares * live_price
                investment_cost = shares * avg_price
                gain_loss = current_value - investment_cost
                percent_return = (gain_loss / investment_cost) * 100 if investment_cost > 0 else 0
                
                # Track totals
                total_investment += investment_cost
                total_current_value += current_value
                
                portfolio_data.append({
                    "Ticker": holding["ticker"],
                    "Shares": shares,
                    "Avg Buy Price": f"${avg_price:.2f}",
                    "Current Price": f"${live_price:.2f}",
                    "Cost Basis": f"${investment_cost:.2f}",
                    "Current Value": f"${current_value:.2f}",
                    "Gain/Loss": f"${gain_loss:.2f}",
                    "Return %": f"{percent_return:.2f}%",
                    "live_price": live_price,
                    "gain_loss": gain_loss,
                    "percent_return": percent_return,
                    "allocation_value": current_value
                })
            
            except Exception as e:
                st.error(f"❌ Error fetching {holding['ticker']}: {str(e)}")
    
    # Portfolio Summary Cards
    st.subheader("📈 Portfolio Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    total_gain_loss = total_current_value - total_investment
    total_percent_return = (total_gain_loss / total_investment) * 100 if total_investment > 0 else 0
    
    with col1:
        st.metric("Total Investment", f"${total_investment:.2f}")
    
    with col2:
        st.metric("Current Value", f"${total_current_value:.2f}")
    
    with col3:
        delta_color = "inverse" if total_gain_loss >= 0 else "normal"
        st.metric(
            "Total Gain/Loss",
            f"${total_gain_loss:.2f}",
            f"{total_percent_return:.2f}%",
            delta_color=delta_color
        )
    
    with col4:
        num_holdings = len(st.session_state.portfolio)
        st.metric("Holdings", f"{num_holdings}")
    
    # Create two columns for portfolio table and pie chart
    st.divider()
    chart_col1, chart_col2 = st.columns([1.5, 1])
    
    with chart_col1:
        st.subheader("📊 Holdings Details")
        
        # Create DataFrame for display with color coding
        display_data = []
        for holding in portfolio_data:
            display_data.append({
                "Ticker": holding["Ticker"],
                "Shares": f"{holding['Shares']:.2f}",
                "Avg Buy Price": holding["Avg Buy Price"],
                "Current Price": holding["Current Price"],
                "Cost Basis": holding["Cost Basis"],
                "Current Value": holding["Current Value"],
                "Gain/Loss": holding["Gain/Loss"],
                "Return %": holding["Return %"]
            })
        
        portfolio_df = pd.DataFrame(display_data)
        st.dataframe(portfolio_df, use_container_width=True, hide_index=True)
        
        # Add details about removing holdings
        if st.checkbox("Remove a holding?"):
            remove_ticker = st.selectbox(
                "Select holding to remove:",
                options=[h["ticker"] for h in st.session_state.portfolio]
            )
            if st.button("🗑️ Remove", use_container_width=True):
                st.session_state.portfolio = [
                    h for h in st.session_state.portfolio if h["ticker"] != remove_ticker
                ]
                save_portfolio(st.session_state.portfolio)
                st.success(f"✅ Removed {remove_ticker}!")
                st.rerun()
    
    with chart_col2:
        st.subheader("💰 Allocation")
        
        # Create allocation pie chart
        if portfolio_data:
            allocation_fig = go.Figure(data=[go.Pie(
                labels=[h["Ticker"] for h in portfolio_data],
                values=[h["allocation_value"] for h in portfolio_data],
                marker=dict(
                    colors=["#00d4ff", "#00ff41", "#ff8800", "#ff4444", "#9d4edd", "#3a86ff"],
                    line=dict(color="#0f1419", width=2)
                ),
                hovertemplate="<b>%{label}</b><br>Value: $%{value:.2f}<br>Allocation: %{percent}<extra></extra>"
            )])
            
            allocation_fig.update_layout(
                template="plotly_dark",
                height=350,
                paper_bgcolor="rgba(15, 20, 25, 0)",
                font=dict(color="#ffffff", size=11),
                legend=dict(
                    bgcolor="rgba(30, 39, 56, 0.8)",
                    bordercolor="#00d4ff",
                    borderwidth=1,
                )
            )
            
            st.plotly_chart(allocation_fig, use_container_width=True)
    
    # Detailed gain/loss analysis
    st.divider()
    st.subheader("🎯 Performance Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    # Calculate statistics
    gainers = [h for h in portfolio_data if h["gain_loss"] > 0]
    losers = [h for h in portfolio_data if h["gain_loss"] < 0]
    
    with col1:
        st.metric(
            "Best Performer",
            gainers[0]["Ticker"] if gainers else "N/A",
            f"{gainers[0]['percent_return']:.2f}%" if gainers else "N/A"
        )
    
    with col2:
        worst_performer = max(losers, key=lambda x: x["percent_return"]) if losers else None
        st.metric(
            "Worst Performer",
            worst_performer["Ticker"] if worst_performer else "N/A",
            f"{worst_performer['percent_return']:.2f}%" if worst_performer else "N/A"
        )
    
    with col3:
        winning_pct = (len(gainers) / len(portfolio_data)) * 100 if portfolio_data else 0
        st.metric(
            "Win Rate",
            f"{winning_pct:.0f}%",
            f"{len(gainers)} of {len(portfolio_data)}"
        )
    
    # Colored holding cards showing gain/loss
    st.markdown("**Individual Holdings Performance:**")
    for holding in portfolio_data:
        gain_loss = holding["gain_loss"]
        percent_return = holding["percent_return"]
        
        # Color based on gain/loss
        if gain_loss >= 0:
            card_color = "#1a3a2a"  # Dark green
            text_color = "#51cf66"  # Bright green
            arrow = "📈"
        else:
            card_color = "#3a1a1a"  # Dark red
            text_color = "#ff6b6b"  # Bright red
            arrow = "📉"
        
        st.markdown(f"""
        <div style='
            background: {card_color};
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid {text_color};
            margin-bottom: 8px;
        '>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <h4 style='color: #ffffff; margin: 0;'>{arrow} {holding["Ticker"]}</h4>
                    <p style='color: #b0b9c1; margin: 5px 0 0 0;'>{holding["Shares"]} shares @ {holding["Avg Buy Price"]}</p>
                </div>
                <div style='text-align: right;'>
                    <p style='color: {text_color}; font-size: 18px; font-weight: bold; margin: 0;'>${gain_loss:.2f}</p>
                    <p style='color: {text_color}; margin: 0;'>{percent_return:.2f}%</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("📝 No holdings yet. Add your first stock in the sidebar to get started!")

# ============================================================================
# TRADE JOURNAL
# ============================================================================
# Simple trade logging tool for home traders to record trades and later
# analyze patterns. Each trade is appended to storage/journal.json.
# This is a basic starter; no AI analysis yet, just data collection.
# ============================================================================
st.divider()
st.title("📝 Trade Journal")

# Initialize or load journal
if "journal" not in st.session_state:
    st.session_state.journal = load_journal()

# Form to log a new trade
st.subheader("Log a Trade")
with st.form("trade_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        journal_ticker = st.text_input(
            "Ticker Symbol",
            placeholder="e.g., AAPL",
            help="Stock or asset ticker"
        ).upper()
    
    with col2:
        trade_type = st.selectbox(
            "Trade Type",
            options=["Stock", "Call Option", "Put Option", "Futures"],
            help="What instrument are you trading?"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        direction = st.selectbox(
            "Direction",
            options=["Long", "Short"],
            help="Are you going long or short?"
        )
    
    with col2:
        entry_price = st.number_input(
            "Entry Price ($)",
            min_value=0.0,
            step=0.01,
            help="Price you entered at"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        exit_price = st.number_input(
            "Exit Price ($) - Optional",
            min_value=0.0,
            step=0.01,
            value=0.0,
            help="Leave 0 if trade is still open"
        )
    
    with col2:
        position_size = st.number_input(
            "Position Size",
            min_value=0.0,
            step=0.1,
            help="Shares, contracts, or units"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        setup_type = st.text_input(
            "Setup Type",
            placeholder="e.g., Breakout, Pullback, RSI Oversold",
            help="What triggered this trade?"
        )
    
    with col2:
        confidence = st.slider(
            "Confidence (1-10)",
            min_value=1,
            max_value=10,
            value=5,
            help="How confident were you in this trade?"
        )
    
    notes = st.text_area(
        "Notes",
        placeholder="Any additional observations or context...",
        height=80,
        help="Keep it brief for patterns"
    )
    
    submitted = st.form_submit_button("Save Trade", use_container_width=True)
    
    if submitted:
        if journal_ticker and entry_price > 0:
            # Calculate P&L if exit price is provided
            pnl = None
            if exit_price > 0:
                if direction == "Long":
                    pnl = (exit_price - entry_price) * position_size
                else:  # Short
                    pnl = (entry_price - exit_price) * position_size
            
            new_trade = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ticker": journal_ticker,
                "trade_type": trade_type,
                "direction": direction,
                "entry_price": entry_price,
                "exit_price": exit_price if exit_price > 0 else None,
                "position_size": position_size,
                "setup_type": setup_type,
                "confidence": confidence,
                "notes": notes,
                "pnl": pnl
            }
            
            st.session_state.journal.append(new_trade)
            save_journal(st.session_state.journal)
            st.success(f"✅ Trade logged: {journal_ticker} {direction} @ ${entry_price}")
            st.rerun()
        else:
            st.error("⚠️ Ticker and Entry Price are required")

# ============================================================================
# JOURNAL SUMMARY METRICS
# ============================================================================
# Calculate performance summary from saved trades for quick insights.
# This helps traders see patterns without AI analysis yet.

def calculate_journal_summary(journal_entries):
    """
    Analyze saved trades and return summary metrics.
    Safe to call with empty journal; returns default values.
    """
    if not journal_entries:
        return None
    
    closed_trades = [t for t in journal_entries if t.get('exit_price') and t['exit_price'] > 0]
    
    if not closed_trades:
        # No closed trades yet; only show total count
        return {
            "total_trades": len(journal_entries),
            "closed_trades": 0,
            "total_pnl": None,
            "win_rate": None,
            "avg_confidence": sum(t['confidence'] for t in journal_entries) / len(journal_entries),
            "best_setup": None
        }
    
    # Calculate metrics for closed trades only
    total_pnl = sum(t['pnl'] for t in closed_trades if t['pnl'] is not None)
    
    # Win rate: trades with positive P&L / total closed trades
    winning_trades = len([t for t in closed_trades if t.get('pnl', 0) > 0])
    win_rate = (winning_trades / len(closed_trades)) * 100
    
    # Average confidence across all trades
    avg_confidence = sum(t['confidence'] for t in journal_entries) / len(journal_entries)
    
    # Best setup type (most frequent, excluding empty)
    setups = [t['setup_type'] for t in journal_entries if t.get('setup_type', '').strip()]
    best_setup = max(set(setups), key=setups.count) if setups else None
    
    return {
        "total_trades": len(journal_entries),
        "closed_trades": len(closed_trades),
        "total_pnl": total_pnl,
        "win_rate": win_rate,
        "avg_confidence": avg_confidence,
        "best_setup": best_setup
    }

# Display saved trades
st.subheader("Saved Trades")
if st.session_state.journal:
    # Show performance summary if trades exist
    summary = calculate_journal_summary(st.session_state.journal)
    
    if summary:
        st.subheader("🎯 Journal Performance Summary")
        
        # Create summary cards in a responsive grid
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Total Trades",
                summary["total_trades"],
                help="Total number of trades logged"
            )
        
        with col2:
            st.metric(
                "Closed Trades",
                summary["closed_trades"],
                help="Trades with exit price (for P&L calculation)"
            )
        
        with col3:
            pnl_display = f"${summary['total_pnl']:.2f}" if summary["total_pnl"] is not None else "N/A"
            pnl_color = "off" if summary["total_pnl"] is None or summary["total_pnl"] >= 0 else "inverse"
            st.metric(
                "Total P&L",
                pnl_display,
                delta_color=pnl_color if summary["total_pnl"] is not None else "off",
                help="Cumulative profit/loss from closed trades"
            )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            win_rate_display = f"{summary['win_rate']:.1f}%" if summary["win_rate"] is not None else "N/A"
            st.metric(
                "Win Rate",
                win_rate_display,
                help="Percentage of closed trades with positive P&L"
            )
        
        with col2:
            st.metric(
                "Avg Confidence",
                f"{summary['avg_confidence']:.1f}/10",
                help="Average confidence level across all trades"
            )
        
        with col3:
            setup_display = summary["best_setup"] if summary["best_setup"] else "N/A"
            st.metric(
                "Best Setup",
                setup_display,
                help="Most frequently used setup type"
            )
    
    # Convert journal to display-friendly DataFrame
    display_trades = []
    for trade in st.session_state.journal:
        pnl_str = f"${trade['pnl']:.2f}" if trade['pnl'] is not None else "Open"
        display_trades.append({
            "Date": trade["timestamp"],
            "Ticker": trade["ticker"],
            "Type": trade["trade_type"],
            "Dir": trade["direction"],
            "Entry": f"${trade['entry_price']:.2f}",
            "Exit": f"${trade['exit_price']:.2f}" if trade['exit_price'] else "Open",
            "Size": trade["position_size"],
            "Setup": trade["setup_type"],
            "Conf": trade["confidence"],
            "P&L": pnl_str,
        })
    
    trades_df = pd.DataFrame(display_trades)
    st.dataframe(trades_df, use_container_width=True, hide_index=True)
    
    # Option to clear entire journal
    if st.checkbox("Clear all trades?"):
        if st.button("🗑️ Delete Journal", use_container_width=True):
            st.session_state.journal = []
            save_journal(st.session_state.journal)
            st.success("✅ Journal cleared!")
            st.rerun()
else:
    st.info("📝 No trades logged yet. Use the form above to log your first trade.")

# Footer
st.divider()
st.markdown(
    "⚠️ **Disclaimer:** This dashboard is for educational purposes only. "
    "Not financial advice. Always conduct your own research before trading."
)
