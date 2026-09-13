import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta

st.set_page_config(page_title="Live Stock Market Intelligence Suite", layout="wide")

st.title("⚡ Live Stock Market Pulse & Multibagger Intelligence Suite")
st.markdown("100% Live Exchange Feed | Weekly RSI (69–80) + Volume Surge + Positive ROC (18) Engine")

# Comprehensive built-in liquid NSE ticker list (No CSV required)
DEFAULT_NSE_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LICI.NS", "HINDUNILVR.NS", 
    "LT.NS", "AXISBANK.NS", "SUNPHARMA.NS", "TITAN.NS", "ASIANPAINT.NS",
    "TATASTEEL.NS", "NTPC.NS", "POWERGRID.NS", "MARUTI.NS", "BAJFINANCE.NS", 
    "KOTAKBANK.NS", "HCLTECH.NS", "WIPRO.NS", "BLISSGVS.NS", "MODISONLTD.NS",
    "WELCORP.NS", "STLTECH.NS", "CUPID.NS", "JINDALSTEL.NS", "VEDL.NS",
    "GRASIM.NS", "ADANIENT.NS", "ADANIPORTS.NS", "TATACOMM.NS", "SIEMENS.NS",
    "BEL.NS", "HAL.NS", "IRCTC.NS", "ZOMATO.NS", "PAYTM.NS", "NAUKRI.NS",
    "SUZLON.NS", "ASHOKLEY.NS", "OBEROIRLTY.NS", "DLF.NS", "PERSISTENT.NS",
    "COFORGE.NS", "LTIM.NS", "MPHASIS.NS", "POLYCAB.NS", "KEI.NS", "DIXON.NS"
]

@st.cache_data(ttl=3600)
def fetch_live_breakouts(tickers):
    matched_stocks = []
    
    progress_text = "Fetching live weekly exchange feeds..."
    progress_bar = st.progress(0, text=progress_text)
    total = len(tickers)
    
    for idx, t in enumerate(tickers):
        try:
            stock = yf.Ticker(t)
            # Fetch 1 year of weekly candles for accurate multi-week analysis
            hist = stock.history(period="1y", interval="1wk")
            
            if len(hist) >= 30:
                close = hist['Close']
                high = hist['High']
                low = hist['Low']
                volume = hist['Volume']
                
                # 1. Live Technical Indicators (100% Live Data)
                rsi = ta.momentum.rsi(close, window=14).iloc[-1]
                roc = ta.momentum.roc(close, window=18).iloc[-1]
                mfi = ta.volume.money_flow_index(high, low, close, volume, window=14).iloc[-1]
                
                # Volume Drastic Increase Check: Current weekly volume > 1.5x of 10-week average volume
                vol_sma_10 = volume.rolling(window=10).mean().iloc[-1]
                current_vol = volume.iloc[-1]
                volume_surging = current_vol > (1.5 * vol_sma_10) if vol_sma_10 > 0 else False
                
                current_price = close.iloc[-1]
                ret_1m = ((current_price - close.iloc[-4]) / close.iloc[-4]) * 100 if len(close) >= 4 else 0
                ret_3m = ((current_price - close.iloc[-12]) / close.iloc[-12]) * 100 if len(close) >= 12 else 0
                
                # Exact Confluence Filter Criteria requested:
                # 1. Weekly RSI strictly between 69 and 80
                # 2. Volume increasing drastically (Surging > 1.5x avg)
                # 3. Rate of Change (18 week) positive (> 0)
                is_qualified = (
                    (69.0 <= rsi <= 80.0) and 
                    volume_surging and 
                    (roc > 0.0)
                )
                
                if is_qualified:
                    matched_stocks.append({
                        'Ticker': t.replace(".NS", ""),
                        'Current Price': round(current_price, 2),
                        'RSI (14)': round(rsi, 2),
                        'Price ROC (18)': round(roc, 2),
                        'Volume Surge': f"{round(current_vol / vol_sma_10, 2)}x Avg" if vol_sma_10 > 0 else "High",
                        'MFI (14)': round(mfi, 2),
                        '1M Return (%)': round(ret_1m, 2),
                        '3M Return (%)': round(ret_3m, 2)
                    })
        except Exception:
            continue
            
        progress_bar.progress(min((idx + 1) / total, 1.0), text=f"Scanned {idx+1}/{total} stocks live...")
        
    progress_bar.empty()
    return pd.DataFrame(matched_stocks)

# Sidebar Navigation
st.sidebar.header("🧭 Navigation Dashboards")
view = st.sidebar.radio("Select Dashboard:", [
    "⭐ 1. Positional Master Portfolio (Custom Ranking)",
    "⚡ 2. Breakout Hunter: Weekly RSI (69-80) + Volume Surge"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚖️ Multi-Factor Ranking Weights")
st.sidebar.markdown("""
* **RSI (14):** 40%
* **Price ROC (18):** 30%
* **Short-Term Return (1M):** 20%
* **Money Flow Index (MFI):** 10%
""")

with st.spinner("Connecting to live exchange APIs and running technical filters..."):
    scanned_df = fetch_live_breakouts(DEFAULT_NSE_TICKERS)

def rank_and_select_top_25(df_input):
    if df_input.empty:
        return df_input
    
    df_input['RSI_Rank'] = df_input['RSI (14)'].rank(ascending=False, pct=True)
    df_input['ROC_Rank'] = df_input['Price ROC (18)'].rank(ascending=False, pct=True)
    df_input['Return_Rank'] = df_input['1M Return (%)'].rank(ascending=False, pct=True)
    df_input['MFI_Rank'] = df_input['MFI (14)'].rank(ascending=False, pct=True)
    
    # Composite Score (Lower sum = Higher priority)
    df_input['Composite_Score'] = (
        df_input['RSI_Rank'] * 0.40 + 
        df_input['ROC_Rank'] * 0.30 + 
        df_input['Return_Rank'] * 0.20 + 
        df_input['MFI_Rank'] * 0.10
    )
    return df_input.sort_values(by='Composite_Score', ascending=True).head(25).reset_index(drop=True)

if view == "⭐ 1. Positional Master Portfolio (Custom Ranking)":
    st.subheader("⭐ Positional Master Portfolio (Live Execution)")
    if not scanned_df.empty:
        top_portfolio = rank_and_select_top_25(scanned_df)
        st.success(f"Successfully generated portfolio with **{len(top_portfolio)}** live-ranked breakout stocks.")
        st.dataframe(top_portfolio, use_container_width=True)
    else:
        st.warning("No stocks currently meet the strict 69–80 RSI + Volume Surge criteria in this batch.")

elif view == "⚡ 2. Breakout Hunter: Weekly RSI (69-80) + Volume Surge":
    st.subheader("⚡ Active Breakout Hunter (Strict RSI 69–80 Band)")
    st.markdown("""
    ### 🎯 Active Confluence Filters:
    * **Weekly RSI Range**: Strictly **69 to 80**.
    * **Volume Expansion**: Drastic volume surge (`> 1.5x` of 10-week moving average).
    * **Momentum Trend**: Positive 18-week Rate of Change (`ROC > 0`).
    """)
    
    if not scanned_df.empty:
        final_ranked = rank_and_select_top_25(scanned_df)
        st.success(f"Found **{len(final_ranked)}** elite breakout leaders matching your criteria.")
        st.dataframe(final_ranked, use_container_width=True)
    else:
        st.warning("No live stocks matching the exact RSI 69–80 and Volume surge rules right now. Try expanding the ticker universe.")
