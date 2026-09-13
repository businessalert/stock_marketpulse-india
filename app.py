import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import ta

# Force clear all caches programmatically on script load
st.cache_data.clear()

st.set_page_config(page_title="Strict Live Breakout Hunter", layout="wide")

st.title("⚡ Live Breakout Hunter (Strict 3-Parameter Engine)")
st.markdown("100% Live Exchange Feed | 1. Weekly RSI (69–80) | 2. Volume Surge | 3. Positive 18W ROC")

# Expanded liquid NSE ticker universe
EXPANDED_NSE_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LICI.NS", "HINDUNILVR.NS", 
    "LT.NS", "AXISBANK.NS", "SUNPHARMA.NS", "TITAN.NS", "ASIANPAINT.NS", "TATASTEEL.NS", "NTPC.NS", "POWERGRID.NS", "MARUTI.NS", "BAJFINANCE.NS", 
    "KOTAKBANK.NS", "HCLTECH.NS", "WIPRO.NS", "BLISSGVS.NS", "MODISONLTD.NS", "WELCORP.NS", "STLTECH.NS", "CUPID.NS", "JINDALSTEL.NS", "VEDL.NS",
    "GRASIM.NS", "ADANIENT.NS", "ADANIPORTS.NS", "TATACOMM.NS", "SIEMENS.NS", "BEL.NS", "HAL.NS", "IRCTC.NS", "ZOMATO.NS", "PAYTM.NS", 
    "NAUKRI.NS", "SUZLON.NS", "ASHOKLEY.NS", "OBEROIRLTY.NS", "DLF.NS", "PERSISTENT.NS", "COFORGE.NS", "LTIM.NS", "MPHASIS.NS", "POLYCAB.NS", 
    "KEI.NS", "DIXON.NS", "RVNL.NS", "IRFC.NS", "NHPC.NS", "SJVN.NS", "HUDCO.NS", "IOC.NS", "BPCL.NS", "HPCL.NS", "GAIL.NS", 
    "ONGC.NS", "COALINDIA.NS", "NMDC.NS", "SAIL.NS", "PNB.NS", "BANKBARODA.NS", "CANBK.NS", "UNIONBANK.NS", "IDFCFIRSTB.NS", "FEDERALBNK.NS",
    "ASTRAL.NS", "SRF.NS", "PIDILITIND.NS", "GODREJCP.NS", "DABUR.NS", "MARICO.NS", "BRITANNIA.NS", "NESTLEIND.NS", "TATACONSUM.NS", "UPL.NS"
]

@st.cache_data(ttl=3600)
def fetch_strict_breakouts(tickers):
    matched_stocks = []
    progress_bar = st.progress(0, text="Scanning live weekly exchange feeds...")
    total = len(tickers)
    
    for idx, t in enumerate(tickers):
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="1y", interval="1wk")
            
            if len(hist) >= 30:
                close = hist['Close']
                volume = hist['Volume']
                
                # Live Technical Indicators (Strictly the requested 3 parameters)
                rsi = ta.momentum.rsi(close, window=14).iloc[-1]
                roc = ta.momentum.roc(close, window=18).iloc[-1]
                
                # Volume Increase Check (> 1.2x of 10-week average)
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
                        'Ticker': t.replace(".NS", ""),
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

with st.spinner("Running live 3-parameter breakout filter..."):
    df_results = fetch_strict_breakouts(EXPANDED_NSE_TICKERS)

st.subheader("🎯 Active Breakout Candidates (RSI 69–80 + Volume Surge + Positive ROC)")

if not df_results.empty:
    df_sorted = df_results.sort_values(by='Weekly RSI (14)', ascending=False).reset_index(drop=True)
    st.success(f"Found **{len(df_sorted)}** stocks matching your exact 3 parameters.")
    st.dataframe(df_sorted, use_container_width=True)
else:
    st.warning("No live stocks currently match all 3 strict parameters in this batch.")
