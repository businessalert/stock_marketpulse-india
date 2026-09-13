import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta

st.set_page_config(page_title="Live Stock Market Intelligence Suite", layout="wide")

st.title("⚡ Live Stock Market Pulse & Multibagger Intelligence Suite")
st.markdown("Master Ticker Directory from CSV + 100% Live Exchange API Numerical Calculation & Multi-Factor Ranking.")

@st.cache_data
def load_master_ticker_list():
    """Loads ONLY stock names, tickers, and industries from the CSV file."""
    try:
        df_csv = pd.read_csv("query-results_13.09.2026.csv")
        return df_csv
    except Exception as e:
        st.error(f"Error loading CSV directory: {e}")
        return pd.DataFrame()

master_csv_df = load_master_ticker_list()

# Sidebar Navigation & Settings
st.sidebar.header("🧭 Navigation Dashboards")
view = st.sidebar.radio("Select Dashboard:", [
    "⭐ 7. Positional Master Portfolio (Top 25 Ranked)",
    "⚡ 8. Full Zerodha Confluence Breakout Hunter (RSI 69-80+ Live Scan)"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚖️ Custom Ranking Weights")
st.sidebar.markdown("""
* **RSI (14):** 40%
* **Price ROC (18):** 30%
* **Short-Term Return:** 20%
* **Money Flow Index (MFI):** 10%
""")

@st.cache_data(ttl=3600)
def fetch_live_indicators_for_universe(csv_df, max_stocks=150):
    """
    Takes tickers from CSV and fetches 100% live historical weekly candles 
    via yfinance to compute numerical indicators on the fly.
    """
    if csv_df.empty:
        return pd.DataFrame()
        
    # Get ticker column (checking standard naming conventions)
    ticker_col = 'NSE Code' if 'NSE Code' in csv_df.columns else ('BSE Code' if 'BSE Code' in csv_df.columns else None)
    if not ticker_col:
        return pd.DataFrame()
        
    subset_df = csv_df.head(max_stocks).copy() # Batch limit to keep UI responsive
    live_results = []
    
    progress_bar = st.progress(0)
    total = len(subset_df)
    
    for idx, row in subset_df.iterrows():
        raw_ticker = str(row[ticker_col]).strip()
        if not raw_ticker or raw_ticker.lower() == 'nan':
            continue
            
        # Format for Yahoo Finance (appending .NS for NSE)
        yf_symbol = f"{raw_ticker}.NS" if not raw_ticker.endswith(".NS") and not raw_ticker.endswith(".BO") else raw_ticker
        
        try:
            stock = yf.Ticker(yf_symbol)
            # Fetch live weekly candles
            hist = stock.history(period="1y", interval="1wk")
            if len(hist) >= 30:
                close = hist['Close']
                high = hist['High']
                low = hist['Low']
                volume = hist['Volume']
                
                # 100% Live numerical calculations (Never from CSV)
                rsi = ta.momentum.rsi(close, window=14).iloc[-1]
                roc = ta.momentum.roc(close, window=18).iloc[-1]
                mfi = ta.volume.money_flow_index(high, low, close, volume, window=14).iloc[-1]
                
                obv = ta.volume.on_balance_volume(close, volume)
                obv_rising = obv.iloc[-1] > obv.iloc[-5]
                
                ma_fast = close.rolling(window=10).mean().iloc[-1]
                ma_slow = close.rolling(window=30).mean().iloc[-1]
                ma_aligned = ma_fast > ma_slow and close.iloc[-1] > ma_fast
                
                current_price = close.iloc[-1]
                ret_1m = ((current_price - close.iloc[-4]) / close.iloc[-4]) * 100 if len(close) >= 4 else 0
                
                live_results.append({
                    'Name': row.get('Name', raw_ticker),
                    'Ticker': raw_ticker,
                    'Industry': row.get('Industry', 'Unknown'),
                    'Current Price': round(current_price, 2),
                    'RSI (14)': round(rsi, 2),
                    'MFI (14)': round(mfi, 2),
                    'Price ROC (18)': round(roc, 2),
                    '1M Return (%)': round(ret_1m, 2),
                    'OBV Status': "Rising" if obv_rising else "Neutral",
                    'MA Trend': "Bullish" if ma_aligned else "Mixed"
                })
        except Exception:
            continue
        progress_bar.progress(min((idx + 1) / total, 1.0))
        
    progress_bar.empty()
    return pd.DataFrame(live_results)

# Run Live Scanner on CSV Master List
with st.spinner("Mapping master stock list from CSV and pulling live weekly exchange data for indicators..."):
    live_scanned_df = fetch_live_indicators_for_universe(master_csv_df, max_stocks=100)

def rank_and_select_top_25(df_input):
    if df_input.empty:
        return df_input
    df_input['RSI_Rank'] = df_input['RSI (14)'].rank(ascending=False, pct=True)
    df_input['ROC_Rank'] = df_input['Price ROC (18)'].rank(ascending=False, pct=True)
    df_input['Return_Rank'] = df_input['1M Return (%)'].rank(ascending=False, pct=True)
    df_input['MFI_Rank'] = df_input['MFI (14)'].rank(ascending=False, pct=True)
    
    # Custom User Weights: RSI 40%, ROC 30%, Returns 20%, MFI 10%
    df_input['Composite_Score'] = (
        df_input['RSI_Rank'] * 0.40 + 
        df_input['ROC_Rank'] * 0.30 + 
        df_input['Return_Rank'] * 0.20 + 
        df_input['MFI_Rank'] * 0.10
    )
    return df_input.sort_values(by='Composite_Score', ascending=True).head(25).reset_index(drop=True)

if view == "⭐ 7. Positional Master Portfolio (Top 25 Ranked)":
    st.subheader("⭐ Positional Master Portfolio (Live Ranked)")
    if not live_scanned_df.empty:
        top_25_port = rank_and_select_top_25(live_scanned_df)
        st.success(f"Successfully generated Top {len(top_25_port)} portfolio from live exchange calculations.")
        st.dataframe(top_25_port, use_container_width=True)
    else:
        st.warning("No live data retrieved from CSV tickers.")

elif view == "⚡ 8. Full Zerodha Confluence Breakout Hunter (RSI 69-80+ Live Scan)":
    st.subheader("⚡ Breakout Hunter: Weekly RSI 69–80+ Zone (100% Live Data)")
    st.markdown("""
    ### 🎯 Active Filtering & Ranking:
    * **CSV Usage**: Ticker directory and industry names mapped from CSV.
    * **Numerical Values**: 100% live weekly candles (`yfinance`) calculating RSI, ROC, MFI, and Volume dynamically.
    * **Breakout Zone**: Isolates stocks with Weekly RSI between **69 and 95** and ranks them using your **40/30/20/10** weights.
    """)
    
    if not live_scanned_df.empty:
        # Filter strictly for the RSI 69-95 breakout band
        breakout_zone = live_scanned_df[(live_scanned_df['RSI (14)'] >= 69.0) & (live_scanned_df['RSI (14)'] <= 95.0)].copy()
        
        if not breakout_zone.empty:
            ranked_breakouts = rank_and_select_top_25(breakout_zone)
            st.success(f"Found **{len(breakout_zone)}** live stocks in the RSI 69–80+ breakout zone. Displaying top-ranked leaders:")
            
            display_cols = ['Name', 'Ticker', 'Industry', 'Current Price', 'RSI (14)', 'Price ROC (18)', 'MFI (14)', '1M Return (%)', 'Composite_Score']
            st.dataframe(ranked_breakouts[[c for c in display_cols if c in ranked_breakouts.columns]], use_container_width=True)
        else:
            st.warning("No stocks currently fall in the 69-95 RSI window from the scanned batch. Try increasing the stock batch limit.")
