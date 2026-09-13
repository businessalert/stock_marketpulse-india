import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta

st.set_page_config(page_title="Live Stock Market Intelligence Suite", layout="wide")

st.title("⚡ Live Stock Market Pulse & Multibagger Intelligence Suite")
st.markdown("Real-Time Technical Scanner with Zerodha Weekly Confluence Rules & Custom Multi-Factor Ranking.")

# Expanded universe of liquid NSE stocks for live scanning (Appending '.NS')
DEFAULT_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LICI.NS", "HINDUNILVR.NS", 
    "LT.NS", "AXISBANK.NS", "SUNPHARMA.NS", "TITAN.NS", "ASIANPAINT.NS",
    "TATASTEEL.NS", "NTPC.NS", "POWERGRID.NS", "MARUTI.NS", "TITAN.NS",
    "BAJFINANCE.NS", "KOTAKBANK.NS", "ASIANPAINT.NS", "HCLTECH.NS", "WIPRO.NS",
    "BLISSGVS.NS", "MODISONLTD.NS"
]

@st.cache_data(ttl=3600)
def fetch_and_scan_big_movers(tickers):
    matched_stocks = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            # Fetch 1 year of weekly candles to match Zerodha weekly chart setup ($1W$)
            hist = stock.history(period="1y", interval="1wk")
            if len(hist) >= 30:
                close = hist['Close']
                high = hist['High']
                low = hist['Low']
                volume = hist['Volume']
                
                # 1. Indicator Calculations
                rsi = ta.momentum.rsi(close, window=14).iloc[-1]
                roc = ta.momentum.roc(close, window=18).iloc[-1]
                mfi = ta.volume.money_flow_index(high, low, close, volume, window=14).iloc[-1]
                
                obv = ta.volume.on_balance_volume(close, volume)
                obv_sloping_up = obv.iloc[-1] > obv.iloc[-5] # OBV rising over recent weeks
                
                # Moving Averages (10 and 30 SMA alignment)
                ma_fast = close.rolling(window=10).mean().iloc[-1]
                ma_slow = close.rolling(window=30).mean().iloc[-1]
                ma_aligned = ma_fast > ma_slow and close.iloc[-1] > ma_fast
                
                current_price = close.iloc[-1]
                ret_1m = ((current_price - close.iloc[-4]) / close.iloc[-4]) * 100 if len(close) >= 4 else 0
                ret_3m = ((current_price - close.iloc[-12]) / close.iloc[-12]) * 100 if len(close) >= 12 else 0
                
                # Full Zerodha Confluence Filter Criteria
                is_big_mover = (
                    rsi >= 70 and 
                    mfi >= 70 and 
                    roc >= 10 and 
                    obv_sloping_up and 
                    ma_aligned
                )
                
                matched_stocks.append({
                    'Ticker': t.replace(".NS", ""),
                    'Current Price': round(current_price, 2),
                    'RSI (14)': round(rsi, 2),
                    'MFI (14)': round(mfi, 2),
                    'Price ROC (18)': round(roc, 2),
                    '1M Return (%)': round(ret_1m, 2),
                    '3M Return (%)': round(ret_3m, 2),
                    'OBV Accumulation': "Rising" if obv_sloping_up else "Neutral",
                    'MA Alignment': "Bullish (10>30)" if ma_aligned else "Mixed",
                    'Big_Mover_Match': is_big_mover
                })
        except Exception:
            continue
    return pd.DataFrame(matched_stocks)

# Sidebar Navigation
st.sidebar.header("🧭 Navigation Dashboards")
view = st.sidebar.radio("Select Dashboard:", [
    "⭐ 7. Positional Master Portfolio (Live Multi-Factor Top 25)",
    "⚡ 8. Full Zerodha Confluence Breakout Hunter (Top 25 Ranked)"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚖️ Ranking Weights Model")
st.sidebar.markdown("""
* **RSI (14):** 40%
* **Price ROC (18):** 30%
* **Short-Term Trend (1M/3M):** 20%
* **Money Flow Index (MFI):** 10%
""")

# Run Live Scanner
with st.spinner("Fetching live market feeds and evaluating weekly technical confluence..."):
    scanned_df = fetch_and_scan_big_movers(DEFAULT_TICKERS)

def rank_and_select_top_25(df_input):
    if df_input.empty:
        return df_input
    
    # Cross-sectional percentile ranking
    df_input['RSI_Rank'] = df_input['RSI (14)'].rank(ascending=False, pct=True)
    df_input['ROC_Rank'] = df_input['Price ROC (18)'].rank(ascending=False, pct=True)
    df_input['Return_Rank'] = df_input['1M Return (%)'].rank(ascending=False, pct=True)
    df_input['MFI_Rank'] = df_input['MFI (14)'].rank(ascending=False, pct=True)
    
    # Custom Composite Alpha Score (Lower percentile rank sum = higher priority)
    df_input['Composite_Score'] = (
        df_input['RSI_Rank'] * 0.40 + 
        df_input['ROC_Rank'] * 0.30 + 
        df_input['Return_Rank'] * 0.20 + 
        df_input['MFI_Rank'] * 0.10
    )
    
    # Sort and take top 25
    return df_input.sort_values(by='Composite_Score', ascending=True).head(25).reset_index(drop=True)

if view == "⭐ 7. Positional Master Portfolio (Live Multi-Factor Top 25)":
    st.subheader("⭐ Positional Master Portfolio (Live Execution)")
    st.markdown("Optimized portfolio allocation derived from live market momentum and multi-factor ranking.")
    
    if not scanned_df.empty:
        top_25_portfolio = rank_and_select_top_25(scanned_df)
        
        # Add risk/reward rules
        top_25_portfolio['Allocation_%'] = round(100 / len(top_25_portfolio), 2)
        top_25_portfolio['Target_Return'] = "+30.0%"
        top_25_portfolio['Stop_Loss'] = "-8.0%"
        
        portfolio_cols = [
            'Ticker', 'Current Price', 'Allocation_%', 'Composite_Score', 
            'RSI (14)', 'Price ROC (18)', 'Target_Return', 'Stop_Loss'
        ]
        st.success(f"Generated live portfolio for **{len(top_25_portfolio)}** top-ranked assets.")
        st.dataframe(top_25_portfolio[[c for c in portfolio_cols if c in top_25_portfolio.columns]], use_container_width=True)
    else:
        st.warning("No live data retrieved.")

elif view == "⚡ 8. Full Zerodha Confluence Breakout Hunter (Top 25 Ranked)":
    st.subheader("⚡ Full Zerodha Confluence Breakout Hunter")
    st.markdown("""
    ### 🎯 Active Confluence Criteria & Ranking Engine:
    * **Filters**: Weekly RSI $\ge 70$, MFI $\ge 70$, ROC $\ge 10$, Rising OBV, and Bullish MA alignment (`10 > 30`).
    * **Ranking**: Prioritized using your precise weighting (**RSI 40%**, **ROC 30%**, **Short-Term Returns 20%**, **MFI 10%**) to isolate the top breakout leaders.
    """)
    
    if not scanned_df.empty:
        confluence_filtered = scanned_df[scanned_df['Big_Mover_Match'] == True].copy()
        
        if not confluence_filtered.empty:
            final_top_25 = rank_and_select_top_25(confluence_filtered)
            st.success(f"Successfully identified and ranked **{len(final_top_25)}** elite breakout stocks matching the full Zerodha blueprint.")
            st.dataframe(final_top_25, use_container_width=True)
        else:
            st.warning("No stocks currently meet the *strict simultaneous* 5-point confluence in the default watchlist. Displaying all live scanned stocks sorted by your custom ranking weights below:")
            fallback_ranked = rank_and_select_top_25(scanned_df)
            st.dataframe(fallback_ranked, use_container_width=True)
    else:
        st.error("Error connecting to live market feeds.")
