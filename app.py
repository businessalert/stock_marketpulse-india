import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta

st.set_page_config(page_title="Live Stock Market Intelligence Suite", layout="wide")

st.title("⚡ Live Stock Market Pulse & Multibagger Intelligence Suite")
st.markdown("Advanced Multi-Strategy Screener with Fresh Breakout Triggers & Custom Multi-Factor Top 25 Ranking.")

@st.cache_data(ttl=3600)
def fetch_and_scan_big_movers(tickers):
    matched_stocks = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            # Fetch weekly historical data to match Zerodha weekly chart structures
            hist = stock.history(period="1y", interval="1wk")
            if len(hist) >= 30:
                close = hist['Close']
                high = hist['High']
                low = hist['Low']
                volume = hist['Volume']
                
                # 1. Technical Indicators calculation
                rsi_series = ta.momentum.rsi(close, window=14)
                roc_series = ta.momentum.roc(close, window=18)
                mfi_series = ta.volume.money_flow_index(high, low, close, volume, window=14)
                obv_series = ta.volume.on_balance_volume(close, volume)
                
                current_rsi = rsi_series.iloc[-1]
                prev_rsi = rsi_series.iloc[-2] if len(rsi_series) >= 2 else 50.0
                
                current_roc = roc_series.iloc[-1]
                current_mfi = mfi_series.iloc[-1]
                
                # 2. Fresh RSI Crossover Condition (Just crossed 70+ this week, avoiding stale peaks)
                is_fresh_rsi_cross = (prev_rsi < 70) and (current_rsi >= 70)
                
                # 3. Supporting Confluence Checks
                mfi_confirmed = current_mfi >= 70
                roc_positive = current_roc > 0
                obv_sloping_up = obv_series.iloc[-1] > obv_series.iloc[-5] # OBV rising over recent weeks
                
                # Moving Averages (10 and 30 SMA/EMA)
                ma_fast = close.rolling(window=10).mean().iloc[-1]
                ma_slow = close.rolling(window=30).mean().iloc[-1]
                ma_aligned = ma_fast > ma_slow and close.iloc[-1] > ma_fast
                
                current_price = close.iloc[-1]
                ret_1m = ((current_price - close.iloc[-4]) / close.iloc[-4]) * 100 if len(close) >= 4 else 0.0
                ret_3m = ((current_price - close.iloc[-12]) / close.iloc[-12]) * 100 if len(close) >= 12 else 0.0
                
                # Full Confluence Trigger
                is_big_mover = (
                    is_fresh_rsi_cross and 
                    mfi_confirmed and 
                    roc_positive and 
                    obv_sloping_up and 
                    ma_aligned
                )
                
                matched_stocks.append({
                    'Ticker': t,
                    'Current Price': round(current_price, 2),
                    'RSI (14)': round(current_rsi, 2),
                    'Prev RSI': round(prev_rsi, 2),
                    'MFI (14)': round(current_mfi, 2),
                    'Price ROC (18)': round(current_roc, 2),
                    '1M Return (%)': round(ret_1m, 2),
                    '3M Return (%)': round(ret_3m, 2),
                    'OBV Trend': "Rising" if obv_sloping_up else "Flat",
                    'MA Alignment': "Bullish" if ma_aligned else "Mixed",
                    'Big_Mover_Match': is_big_mover
                })
        except Exception as e:
            continue
            
    return pd.DataFrame(matched_stocks)

# Comprehensive sample list of liquid NSE scrips (Can be extended with full exchange symbol lists)
watchlist = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LICI.NS", "HINDUNILVR.NS", 
    "LT.NS", "AXISBANK.NS", "SUNPHARMA.NS", "TITAN.NS", "ASIANPAINT.NS",
    "BLISSGVS.NS", "MODISONLTD.NS", "CUPID.NS", "STLTECH.NS", "SIGMA.NS"
]

st.sidebar.header("🧭 Navigation Dashboards")
view = st.sidebar.radio("Select Dashboard:", [
    "⭐ 1. Positional Master Portfolio (Technical Triggers & 30% Target)",
    "⚡ 2. Leading Indicators & Breakout Hunter (Fresh RSI Cross > 70)"
])

with st.spinner("Scanning live market candles & calculating multi-indicator confluence..."):
    scanned_df = fetch_and_scan_big_movers(watchlist)

if view == "⭐ 1. Positional Master Portfolio (Technical Triggers & 30% Target)":
    st.subheader("⭐ Positional Master Portfolio")
    st.markdown("""
    ### 🛠️ Technical Entry & Exit Rulebook:
    * **🟢 Entry Trigger**: Weekly fresh RSI cross ($\ge 70$) + OBV Accumulation + MFI $\ge 70$.
    * **🔴 Exit Trigger**: Profit target at **$+30\%$** or Stop-Loss at **$-8\%$**.
    """)
    if not scanned_df.empty:
        st.dataframe(scanned_df, use_container_width=True)
    else:
        st.warning("No data retrieved from active feeds.")

elif view == "⚡ 2. Leading Indicators & Breakout Hunter (Fresh RSI Cross > 70)":
    st.subheader("⚡ Leading Indicators & Breakout Hunter (Top 25 Ranked)")
    st.markdown("""
    ### 🎯 Fresh Breakout & Multi-Factor Scoring Rules:
    * **Fresh RSI Crossover**: Prioritizes stocks that have *just crossed* $70+$ this week (`Prev RSI < 70` & `Current RSI >= 70`), eliminating stale, overextended trends.
    * **Custom Multi-Factor Ranking (Top 25 Selection)**:
        * **RSI (14)**: `40%` weight
        * **Price ROC (18)**: `30%` weight
        * **Recent Performance (1M/3M Return)**: `20%` weight
        * **Money Flow Index (MFI)**: `10%` weight
    """)
    
    if not scanned_df.empty:
        # Filter for fresh breakout matches
        breakout_pool = scanned_df[scanned_df['Big_Mover_Match'] == True].copy()
        
        if len(breakout_pool) > 0:
            st.success(f"Found **{len(breakout_pool)}** stocks matching the fresh breakout criteria.")
            
            # Apply Custom Multi-Factor Ranking Logic for Top 25
            breakout_pool['RSI_Rank'] = breakout_pool['RSI (14)'].rank(ascending=False, pct=True)
            breakout_pool['ROC_Rank'] = breakout_pool['Price ROC (18)'].rank(ascending=False, pct=True)
            breakout_pool['Return_Rank'] = breakout_pool['1M Return (%)'].rank(ascending=False, pct=True)
            breakout_pool['MFI_Rank'] = breakout_pool['MFI (14)'].rank(ascending=False, pct=True)
            
            # Composite Alpha Score using your exact weightings (Lower rank sum = higher priority)
            breakout_pool['Composite_Score'] = (
                breakout_pool['RSI_Rank'] * 0.40 + 
                breakout_pool['ROC_Rank'] * 0.30 + 
                breakout_pool['Return_Rank'] * 0.20 + 
                breakout_pool['MFI_Rank'] * 0.10
            )
            
            top_25_ranked = breakout_pool.sort_values(by='Composite_Score', ascending=True).head(25).reset_index(drop=True)
            
            top_25_ranked['Target_Return'] = "+30.0%"
            top_25_ranked['Stop_Loss'] = "-8.0%"
            
            display_cols = [
                'Ticker', 'Current Price', 'RSI (14)', 'Prev RSI', 'MFI (14)', 
                'Price ROC (18)', '1M Return (%)', 'Target_Return', 'Stop_Loss'
            ]
            st.dataframe(top_25_ranked[[c for c in display_cols if c in top_25_ranked.columns]], use_container_width=True)
        else:
            st.warning("⚠️ No stocks in the current watchlist have *just* crossed RSI 70+ this exact week with full confluence. Showing all scanned stocks with technical indicators below:")
            st.dataframe(scanned_df, use_container_width=True)
    else:
        st.error("Error connecting to live market feeds.")
