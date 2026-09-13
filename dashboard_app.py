@st.cache_data(ttl=3600)
def fetch_live_indicators_from_csv(csv_df, max_stocks=200):
    if csv_df.empty:
        return pd.DataFrame()
        
    # Identify ticker column from your Screener.in CSV
    ticker_col = None
    for col in ['NSE Code', 'BSE Code', 'Symbol', 'Ticker']:
        if col in csv_df.columns:
            ticker_col = col
            break
            
    if not ticker_col:
        st.error("Could not find a valid Ticker/Code column in the CSV.")
        return pd.DataFrame()
        
    subset_df = csv_df.head(max_stocks).copy()
    live_results = []
    
    progress_text = "Fetching live market candles from exchanges..."
    progress_bar = st.progress(0, text=progress_text)
    total = len(subset_df)
    
    success_count = 0
    for idx, row in subset_df.iterrows():
        raw_ticker = str(row[ticker_col]).strip()
        if not raw_ticker or raw_ticker.lower() == 'nan':
            continue
            
        # Clean and format ticker for Yahoo Finance (.NS for NSE by default)
        clean_symbol = raw_ticker.upper().replace('&', '-')
        if not clean_symbol.endswith(".NS") and not clean_symbol.endswith(".BO"):
            yf_symbol = f"{clean_symbol}.NS"
        else:
            yf_symbol = clean_symbol
            
        try:
            stock = yf.Ticker(yf_symbol)
            hist = stock.history(period="1y", interval="1wk")
            
            # Fallback to BSE (.BO) if NSE fails
            if hist.empty and not yf_symbol.endswith(".BO"):
                yf_symbol = f"{clean_symbol}.BO"
                stock = yf.Ticker(yf_symbol)
                hist = stock.history(period="1y", interval="1wk")
                
            if not hist.empty and len(hist) >= 30:
                close = hist['Close']
                high = hist['High']
                low = hist['Low']
                volume = hist['Volume']
                
                # Live numerical calculations (100% independent of CSV numbers)
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
                    'Ticker': clean_symbol,
                    'Industry': row.get('Industry', 'Unknown'),
                    'Current Price': round(current_price, 2),
                    'RSI (14)': round(rsi, 2),
                    'MFI (14)': round(mfi, 2),
                    'Price ROC (18)': round(roc, 2),
                    '1M Return (%)': round(ret_1m, 2),
                    'OBV Status': "Rising" if obv_rising else "Neutral",
                    'MA Trend': "Bullish" if ma_aligned else "Mixed"
                })
                success_count += 1
        except Exception:
            continue
            
        progress_bar.progress(min((idx + 1) / total, 1.0), text=f"Scanned {idx+1}/{total} stocks (Successful: {success_count})")
        
    progress_bar.empty()
    return pd.DataFrame(live_results)
