import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta

st.set_page_config(page_title="Live Breakout Hunter (CSV Directory)", layout="wide")

st.title("⚡ Live Breakout Hunter (CSV Directory + Live Exchange Data)")
st.markdown("Master Ticker List from CSV | 100% Live Numerical Calculation (RSI 69–80 + Volume Surge + ROC > 0)")

@st.cache_data
def load_csv_directory():
    """Loads ONLY stock names, tickers, and industries from the local CSV file."""
    try:
        df = pd.read_csv("query-results_13.09.2026.csv")
        return df
    except Exception as e:
        st.error(f"Error loading CSV directory: {e}")
        return pd.DataFrame()

csv_master_df = load_csv_directory()

@st.cache_data(ttl=3600)
def fetch_live_breakouts_from_csv(df_master):
    if df_master.empty:
        return pd.DataFrame()
        
    # Dynamically locate the ticker column in your CSV
    ticker_col = None
    for col in ['NSE Code', 'BSE Code', 'Symbol', 'Ticker']:
        if col in df_master.columns:
            ticker_col = col
            break
            
    if not ticker_col:
        st.error("Could not find a valid Ticker/Code column in the CSV.")
        return pd.DataFrame()
        
    matched_stocks = []
    progress_bar = st.progress(0, text="Scanning tickers from CSV directory live...")
    total = len(df_master)
    
    for idx, row in df_master.iterrows():
        raw_ticker = str(row[ticker_col]).strip()
        if not raw_ticker or raw_ticker.lower() == 'nan':
            continue
            
        # Clean and format ticker for Yahoo Finance (.NS for NSE, fallback to .BO for BSE)
        clean_symbol = raw_ticker.upper().replace('&', '-')
        yf_symbol = f"{clean_symbol}.NS" if not clean_symbol.endswith(".NS") and not clean_symbol.endswith(".BO") else clean_symbol
        
        try:
            stock = yf.Ticker(yf_symbol)
            hist = stock.history(period="1y", interval="1wk")
            
            # Fallback check for BSE if NSE returns empty
            if hist.empty and not yf_symbol.endswith(".BO"):
                yf_symbol = f"{clean_symbol}.BO"
                stock = yf.Ticker(yf_symbol)
                hist = stock.history(period="1y", interval="1wk")
                
            if len(hist) >= 30:
                close = hist['Close']
                volume = hist['Volume']
                
                # 1. Live Technical Indicators (Calculated live, never from CSV)
                rsi = ta.momentum.rsi(close, window=14).iloc[-1]
                roc = ta.momentum.roc(close, window=18).iloc[-1]
                
                # 2. Volume Increase Check (Current weekly volume > 1.2x of 10-week average)
                vol_sma_10 = volume.rolling(window=10).mean().iloc[-1]
                current_vol = volume.iloc[-1]
                volume_surging = current_vol > (1.2 * vol_sma_10) if vol_sma_10 > 0 else False
                
                current_price = close.iloc[-1]
                
                # EXACT FILTER: RSI (69-80) + Volume Surge + ROC (18) > 0
                is_qualified = (
                    (69.0 <= rsi <= 80.0) and 
                    volume_surging and 
                    (roc > 0.0)
                )
                
                if is_qualified:
                    matched_stocks.append({
                        'Name': row.get('Name', raw_ticker),
                        'Ticker': clean_symbol,
                        'Industry': row.get('Industry', 'Unknown'),
                        'Current Price': round(current_price, 2),
                        'Weekly RSI (14)': round(rsi, 2),
                        'Price ROC (18)': round(roc, 2),
                        'Volume Surge Ratio': f"{round(current_vol / vol_sma_10, 2)}x Avg"
                    })
        except Exception:
            continue
            
        progress_bar.progress(min((idx + 1) / total, 1.0), text=f"Scanned {idx+1}/{total} stocks live...")
        
    progress_bar.empty()
    return pd.DataFrame(matched_stocks)

with st.spinner("Reading master ticker directory from CSV and fetching live weekly exchange data..."):
    df_results = fetch_live_breakouts_from_csv(csv_master_df)

st.subheader("🎯 Active Breakout Candidates (CSV Directory + Live 3-Parameter Engine)")

if not df_results.empty:
    df_sorted = df_results.sort_values(by='Weekly RSI (14)', ascending=False).reset_index(drop=True)
    st.success(f"Found **{len(df_sorted)}** stocks matching your exact 3 parameters from your CSV master list.")
    st.dataframe(df_sorted, use_container_width=True)
else:
    st.warning("No live stocks currently match all 3 strict parameters simultaneously from your CSV tickers.")
