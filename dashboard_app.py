import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Live Market Scanner Suite", layout="wide")

st.title("⚡ Live Stock Market Pulse & Intelligence Suite")
st.markdown("Master Ticker List from CSV | 100% Live Exchange Calculations")

# Sidebar Controls
st.sidebar.header("⚙️ Scanner Settings")
max_scan = st.sidebar.slider("Max CSV stocks to scan:", min_value=50, max_value=500, value=100, step=50)

@st.cache_data
def load_csv_directory():
    try:
        return pd.read_csv("query-results_13.09.2026.csv")
    except Exception as e:
        st.error(f"Error loading CSV directory: {e}")
        return pd.DataFrame()

csv_master_df = load_csv_directory()

def process_ticker_weekly(row, ticker_col):
    raw_ticker = str(row[ticker_col]).strip()
    if not raw_ticker or raw_ticker.lower() == 'nan':
        return None
        
    clean_symbol = raw_ticker.upper().replace('&', '-')
    yf_symbol = f"{clean_symbol}.NS" if not clean_symbol.endswith(".NS") and not clean_symbol.endswith(".BO") else clean_symbol
    
    try:
        stock = yf.Ticker(yf_symbol)
        hist = stock.history(period="6mo", interval="1wk")
        
        if hist.empty and not yf_symbol.endswith(".BO"):
            yf_symbol = f"{clean_symbol}.BO"
            stock = yf.Ticker(yf_symbol)
            hist = stock.history(period="6mo", interval="1wk")
            
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
                    'Name': row.get('Name', raw_ticker),
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

def process_ticker_monthly(row, ticker_col):
    raw_ticker = str(row[ticker_col]).strip()
    if not raw_ticker or raw_ticker.lower() == 'nan':
        return None
        
    clean_symbol = raw_ticker.upper().replace('&', '-')
    yf_symbol = f"{clean_symbol}.NS" if not clean_symbol.endswith(".NS") and not clean_symbol.endswith(".BO") else clean_symbol
    
    try:
        stock = yf.Ticker(yf_symbol)
        # Fetching monthly interval history
        hist = stock.history(period="max", interval="1mo")
        
        if hist.empty and not yf_symbol.endswith(".BO"):
            yf_symbol = f"{clean_symbol}.BO"
            stock = yf.Ticker(yf_symbol)
            hist = stock.history(period="max", interval="1mo")
            
        if len(hist) >= 20:
            close = hist['Close']
            
            # Monthly RSI (14)
            rsi_monthly = ta.momentum.rsi(close, window=14).iloc[-1]
            current_price = close.iloc[-1]
            
            # EXACT FILTER: Monthly RSI strictly between 69 and 75 (No other filters)
            if 69.0 <= rsi_monthly <= 75.0:
                return {
                    'Name': row.get('Name', raw_ticker),
                    'Ticker': clean_symbol,
                    'Industry': row.get('Industry', 'Unknown'),
                    'Current Price': round(current_price, 2),
                    'Monthly RSI (14)': round(rsi_monthly, 2)
                }
    except Exception:
        pass
    return None

@st.cache_data(ttl=3600)
def fetch_weekly_breakouts(df_master, limit):
    if df_master.empty:
        return pd.DataFrame()
    ticker_col = next((col for col in ['NSE Code', 'BSE Code', 'Symbol', 'Ticker'] if col in df_master.columns), None)
    if not ticker_col:
        return pd.DataFrame()
        
    subset_df = df_master.head(limit)
    matched_stocks = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_ticker_weekly, row, ticker_col) for _, row in subset_df.iterrows()]
        for future in as_completed(futures):
            res = future.result()
            if res:
                matched_stocks.append(res)
                
    return pd.DataFrame(matched_stocks)

@st.cache_data(ttl=3600)
def fetch_monthly_rsi_scan(df_master, limit):
    if df_master.empty:
        return pd.DataFrame()
    ticker_col = next((col for col in ['NSE Code', 'BSE Code', 'Symbol', 'Ticker'] if col in df_master.columns), None)
    if not ticker_col:
        return pd.DataFrame()
        
    subset_df = df_master.head(limit)
    matched_stocks = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_ticker_monthly, row, ticker_col) for _, row in subset_df.iterrows()]
        for future in as_completed(futures):
            res = future.result()
            if res:
                matched_stocks.append(res)
                
    return pd.DataFrame(matched_stocks)

# Navigation Tabs
tab1, tab2 = st.tabs(["⚡ Weekly Breakout Hunter (3-Parameter)", "🎯 Monthly RSI Scan (69–75)"])

with tab1:
    st.subheader("Active Breakout Candidates (Weekly RSI 69–80 + Volume Surge + ROC > 0)")
    with st.spinner("Scanning weekly feeds in parallel..."):
        df_weekly = fetch_weekly_breakouts(csv_master_df, max_scan)
        
    if not df_weekly.empty:
        df_weekly_sorted = df_weekly.sort_values(by='Weekly RSI (14)', ascending=False).reset_index(drop=True)
        st.success(f"Found **{len(df_weekly_sorted)}** matching stocks.")
        st.dataframe(df_weekly_sorted, use_container_width=True)
    else:
        st.warning("No stocks match the strict weekly parameters in this batch.")

with tab2:
    st.subheader("Monthly Momentum Pool (Monthly RSI 69–75)")
    with st.spinner("Scanning monthly charts across exchange feeds..."):
        df_monthly = fetch_monthly_rsi_scan(csv_master_df, max_scan)
        
    if not df_monthly.empty:
        df_monthly_sorted = df_monthly.sort_values(by='Monthly RSI (14)', ascending=False).reset_index(drop=True)
        st.success(f"Found **{len(df_monthly_sorted)}** stocks with Monthly RSI between 69 and 75.")
        st.dataframe(df_monthly_sorted, use_container_width=True)
    else:
        st.warning("No stocks match the Monthly RSI 69–75 filter in this batch.")
