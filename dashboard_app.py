import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Live Market Scanner Suite", layout="wide")

st.title("⚡ Live Stock Market Pulse & Multibagger Intelligence Suite")
st.markdown("Advanced Multi-Strategy Screener & Institutional Flow Analytics with Breakout Triggers.")

# Sidebar Controls
st.sidebar.header("⚙️ Scanner Settings")
max_scan = st.sidebar.slider("Max CSV stocks to scan per batch:", min_value=50, max_value=500, value=100, step=50)

@st.cache_data
def load_csv_directory():
    try:
        return pd.read_csv("query-results_13.09.2026.csv")
    except Exception as e:
        st.error(f"Error loading CSV directory: {e}")
        return pd.DataFrame()

csv_master_df = load_csv_directory()

# Helper to resolve ticker symbol from CSV
def get_yf_symbol(row, ticker_col):
    raw_ticker = str(row[ticker_col]).strip()
    if not raw_ticker or raw_ticker.lower() == 'nan':
        return None
    clean_symbol = raw_ticker.upper().replace('&', '-')
    yf_symbol = f"{clean_symbol}.NS" if not clean_symbol.endswith(".NS") and not clean_symbol.endswith(".BO") else clean_symbol
    return clean_symbol, yf_symbol

# 1. Weekly Breakout Engine (Strict 3-Parameter)
def process_ticker_weekly(row, ticker_col):
    res_sym = get_yf_symbol(row, ticker_col)
    if not res_sym: return None
    clean_symbol, yf_symbol = res_sym
    
    try:
        stock = yf.Ticker(yf_symbol)
        hist = stock.history(period="1y", interval="1wk")
        if hist.empty and not yf_symbol.endswith(".BO"):
            yf_symbol = f"{clean_symbol}.BO"
            stock = yf.Ticker(yf_symbol)
            hist = stock.history(period="1y", interval="1wk")
            
        if len(hist) >= 20:
            close = hist['Close']
            volume = hist['Volume']
            
            rsi = ta.momentum.rsi(close, window=14).iloc[-1]
            roc = ta.momentum.roc(close, window=18).iloc[-1]
            vol_sma_10 = volume.rolling(window=10).mean().iloc[-1]
            current_vol = volume.iloc[-1]
            volume_surging = current_vol > (1.2 * vol_sma_10) if vol_sma_10 > 0 else False
            current_price = close.iloc[-1]
            
            # STRICT WEEKLY FILTER: RSI (69-80) + Volume Surge + ROC (18) > 0
            if (69.0 <= rsi <= 80.0) and volume_surging and (roc > 0.0):
                return {
                    'Name': row.get('Name', clean_symbol),
                    'Ticker': clean_symbol,
                    'Industry': row.get('Industry', 'Unknown'),
                    'Current Price': round(current_price, 2),
                    'Weekly RSI (14)': round(rsi, 2),
                    'Price ROC (18)': round(roc, 2),
                    'Volume Surge Ratio': f"{round(current_vol / vol_sma_10, 2)}x Avg"
                }
    except Exception:
        pass
    return None

# 2. Monthly RSI Engine (Strictly Monthly Candles, RSI 14 between 69 and 75, No other filters)
def process_ticker_monthly(row, ticker_col):
    res_sym = get_yf_symbol(row, ticker_col)
    if not res_sym: return None
    clean_symbol, yf_symbol = res_sym
    
    try:
        stock = yf.Ticker(yf_symbol)
        # Fetching monthly historical interval
        hist = stock.history(period="max", interval="1mo")
        if hist.empty and not yf_symbol.endswith(".BO"):
            yf_symbol = f"{clean_symbol}.BO"
            stock = yf.Ticker(yf_symbol)
            hist = stock.history(period="max", interval="1mo")
            
        if len(hist) >= 20:
            close = hist['Close']
            
            # Compute Monthly RSI (14 periods based on monthly candles)
            rsi_monthly = ta.momentum.rsi(close, window=14).iloc[-1]
            current_price = close.iloc[-1]
            
            # EXACT FILTER: Monthly RSI (14) strictly between 69 and 75
            if 69.0 <= rsi_monthly <= 75.0:
                return {
                    'Name': row.get('Name', clean_symbol),
                    'Ticker': clean_symbol,
                    'Industry': row.get('Industry', 'Unknown'),
                    'Current Price': round(current_price, 2),
                    'Monthly RSI (14)': round(rsi_monthly, 2)
                }
    except Exception:
        pass
    return None

# 3. Legacy / Alternate Ranking Dashboard (RSI 70-95 & Multi-Factor Scoring)
def process_ticker_legacy_ranked(row, ticker_col):
    res_sym = get_yf_symbol(row, ticker_col)
    if not res_sym: return None
    clean_symbol, yf_symbol = res_sym
    
    try:
        stock = yf.Ticker(yf_symbol)
        hist = stock.history(period="1y", interval="1wk")
        if hist.empty and not yf_symbol.endswith(".BO"):
            yf_symbol = f"{clean_symbol}.BO"
            stock = yf.Ticker(yf_symbol)
            hist = stock.history(period="1y", interval="1wk")
            
        if len(hist) >= 20:
            close = hist['Close']
            volume = hist['Volume']
            
            rsi = ta.momentum.rsi(close, window=14).iloc[-1]
            roc = ta.momentum.roc(close, window=18).iloc[-1]
            mfi = ta.volume.money_flow_index(hist['High'], hist['Low'], close, volume, window=14).iloc[-1]
            
            # 1M / 3M Return proxy calculations
            ret_1m = ((close.iloc[-1] - close.iloc[-4]) / close.iloc[-4]) * 100 if len(close) >= 4 else 0.0
            ret_3m = ((close.iloc[-1] - close.iloc[-12]) / close.iloc[-12]) * 100 if len(close) >= 12 else 0.0
            recent_perf = (ret_1m + ret_3m) / 2.0
            
            current_price = close.iloc[-1]
            
            if (70.0 <= rsi <= 95.0) and (roc > 0.0):
                # Multi-Factor Score Weighting
                score = (rsi * 0.4) + (max(roc, 0) * 0.3) + (max(recent_perf, 0) * 0.2) + (mfi * 0.1)
                return {
                    'Name': row.get('Name', clean_symbol),
                    'Ticker': clean_symbol,
                    'Industry': row.get('Industry', 'Unknown'),
                    'Composite Score': round(score, 2),
                    'Current Price': round(current_price, 2),
                    'Weekly RSI (14)': round(rsi, 2),
                    'Price ROC (18)': round(roc, 2),
                    'Money Flow Index': round(mfi, 2)
                }
    except Exception:
        pass
    return None

# Caching Data Pulls
@st.cache_data(ttl=3600)
def fetch_scan_results(df_master, limit, mode):
    if df_master.empty:
        return pd.DataFrame()
    ticker_col = next((col for col in ['NSE Code', 'BSE Code', 'Symbol', 'Ticker'] if col in df_master.columns), None)
    if not ticker_col:
        return pd.DataFrame()
        
    subset_df = df_master.head(limit)
    matched_stocks = []
    
    if mode == 'weekly':
        worker_func = process_ticker_weekly
    elif mode == 'monthly':
        worker_func = process_ticker_monthly
    else:
        worker_func = process_ticker_legacy_ranked
        
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker_func, row, ticker_col) for _, row in subset_df.iterrows()]
        for future in as_completed(futures):
            res = future.result()
            if res:
                matched_stocks.append(res)
                
    return pd.DataFrame(matched_stocks)

# Navigation Dashboards
tab1, tab2, tab3 = st.tabs([
    "⚡ Weekly Breakout Hunter (3-Parameter)", 
    "🎯 Monthly Momentum Scan (Monthly RSI 69–75)", 
    "📊 Advanced Multi-Strategy & Ranked Top 25"
])

with tab1:
    st.subheader("Leading Indicators & Breakout Hunter (Live Weekly Candles)")
    st.markdown("Breakout Zone: Weekly RSI (69–80), Volume Surge (>1.2x 10W MA), and Positive Price Velocity (ROC > 0).")
    
    with st.spinner("Scanning weekly exchange feeds in parallel..."):
        df_weekly = fetch_scan_results(csv_master_df, max_scan, 'weekly')
        
    if not df_weekly.empty:
        df_w_sorted = df_weekly.sort_values(by='Weekly RSI (14)', ascending=False).reset_index(drop=True)
        st.success(f"Found **{len(df_w_sorted)}** qualified weekly breakout candidates.")
        st.dataframe(df_w_sorted, use_container_width=True)
    else:
        st.warning("No stocks match the strict weekly parameters in this batch window.")

with tab2:
    st.subheader("Monthly RSI Intelligence (Pure Monthly Ticker Evaluation)")
    st.markdown("Filter Rule: **Monthly RSI (14)** calculated strictly from monthly historical charts, pinned between **69 and 75**.")
    
    with st.spinner("Fetching monthly historical feeds across CSV universe..."):
        df_monthly = fetch_scan_results(csv_master_df, max_scan, 'monthly')
        
    if not df_monthly.empty:
        df_m_sorted = df_monthly.sort_values(by='Monthly RSI (14)', ascending=False).reset_index(drop=True)
        st.success(f"Found **{len(df_m_sorted)}** stocks meeting the Monthly RSI 69–75 criteria.")
        st.dataframe(df_m_sorted, use_container_width=True)
    else:
        st.warning("No stocks match the Monthly RSI 69–75 filter in this batch window.")

with tab3:
    st.subheader("Advanced Multi-Strategy Screener & Institutional Flow Analytics")
    st.markdown("Custom Multi-Factor Ranking Weights: RSI 14 (40%), Price ROC (30%), Recent Return (20%), MFI 14 (10%).")
    
    with st.spinner("Computing multi-factor rankings..."):
        df_ranked = fetch_scan_results(csv_master_df, max_scan, 'ranked')
        
    if not df_ranked.empty:
        df_ranked_sorted = df_ranked.sort_values(by='Composite Score', ascending=False).head(25).reset_index(drop=True)
        st.success(f"Generated Top Ranked Selection (**{len(df_ranked_sorted)}** stocks).")
        st.dataframe(df_ranked_sorted, use_container_width=True)
    else:
        st.warning("No stocks qualified for the advanced multi-factor ranking in this batch.")
