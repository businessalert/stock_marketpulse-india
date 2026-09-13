import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Stock Market Pulse - PEAD & Top Gainers Dashboard", layout="wide")

st.title("🚀 PEAD & Top 500 Gainers Intelligence Dashboard")
st.markdown("Advanced Earnings Drift, Momentum Tracking, and Stock Screener powered by Master Mapping Data.")

@st.cache_data
def load_master_data():
    # Load the master mapping CSV file containing fundamentals, returns, and PEAD indicators
    df = pd.read_csv("query-results_13.09.2026.csv")
    return df

try:
    df = load_master_data()
    
    # Sidebar Navigation for your real dashboards
    st.sidebar.header("Dashboard Modules")
    module = st.sidebar.radio("Select View:", [
        "🔥 Top Gainers & Momentum Tracker",
        "📈 PEAD (Post-Earnings Announcement Drift)",
        "🧹 Cigar Butt & Value Screener",
        "🔍 Master Stock Explorer"
    ])
    
    if module == "🔥 Top Gainers & Momentum Tracker":
        st.subheader("Top 500 Gainers & Momentum Performance")
        st.markdown("Tracking top performing stocks based on 6-month and 1-year returns, volume/RSI indicators, and market capitalization.")
        
        # Sort by 1-year return or 6-month return if available
        return_col = 'Return over 1year' if 'Return over 1year' in df.columns else df.columns[0]
        
        col1, col2 = st.columns(2)
        with col1:
            min_mcap = st.number_input("Min Market Capitalization (Cr):", value=100.0)
        with col2:
            min_rsi = st.slider("Min RSI (Momentum Filter):", 0, 100, 50)
            
        filtered = df[(df['Market Capitalization'] >= min_mcap) & (df['RSI'] >= min_rsi)] if 'Market Capitalization' in df.columns and 'RSI' in df.columns else df
        
        top_gainers = filtered.sort_values(by=return_col, ascending=False).head(100)
        
        display_cols = ['Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 'Market Capitalization', 'Return over 6months', 'Return over 1year', 'RSI', 'Price to Earning']
        existing_cols = [c for c in display_cols if c in top_gainers.columns]
        
        st.write(f"Showing top **{len(top_gainers)}** momentum gainers matching criteria:")
        st.dataframe(top_gainers[existing_cols], use_container_width=True)
        
    elif module == "📈 PEAD (Post-Earnings Announcement Drift)":
        st.subheader("PEAD (Post-Earnings Announcement Drift) Screener")
        st.markdown("Identifying companies with strong earnings surprises, positive YOY/QoQ profit growth, and sustained upward price momentum.")
        
        # PEAD filtering logic: Positive profit growth + positive quarterly sales growth + strong ROCE
        if all(col in df.columns for col in ['YOY Quarterly profit growth', 'Return on capital employed', 'RSI']):
            pead_stocks = df[
                (df['YOY Quarterly profit growth'] > 20) & 
                (df['Return on capital employed'] > 15) & 
                (df['RSI'] > 50)
            ].sort_values(by='YOY Quarterly profit growth', ascending=False)
            
            st.success(f"Found **{len(pead_stocks)}** stocks exhibiting high earnings growth and positive price drift characteristics (PEAD).")
            
            pead_cols = ['Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 'YOY Quarterly profit growth', 'Net Profit latest quarter', 'Return on capital employed', 'RSI', 'Price to Earning']
            existing_pead_cols = [c for c in pead_cols if c in pead_stocks.columns]
            
            st.dataframe(pead_stocks[existing_pead_cols].head(100), use_container_width=True)
        else:
            st.info("Required columns for PEAD analysis are currently missing from the dataset.")
            st.dataframe(df.head(50), use_container_width=True)
            
    elif module == "🧹 Cigar Butt & Value Screener":
        st.subheader("Cigar Butt & Deep Value Opportunities")
        st.markdown("Companies trading below intrinsic value with solid underlying fundamentals.")
        
        if 'Intrinsic Value' in df.columns and 'Current Price' in df.columns:
            value_stocks = df[df['Intrinsic Value'] > df.columns and df['Intrinsic Value'] > df['Current Price']].dropna(subset=['Name', 'Current Price', 'Intrinsic Value'])
            st.write(f"Found **{len(value_stocks)}** value stocks.")
            st.dataframe(value_stocks[['Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 'Intrinsic Value', 'Price to Earning', 'Return on capital employed']].head(100), use_container_width=True)
        else:
            st.dataframe(df.head(50), use_container_width=True)
            
    elif module == "🔍 Master Stock Explorer":
        st.subheader("Complete Stock & Industry Database")
        selected_ind = st.selectbox("Select Industry:", ["All"] + list(df['Industry'].dropna().unique()))
        search_query = st.text_input("Search Company Name or Ticker:")
        
        res = df if selected_ind == "All" else df[df['Industry'] == selected_ind]
        if search_query:
            res = res[res['Name'].str.contains(search_query, case=False, na=False) | res['NSE Code'].str.contains(search_query, case=False, na=False)]
            
        st.write(f"Results: **{len(res)}** companies")
        st.dataframe(res, use_container_width=True)

except Exception as e:
    st.error(f"Dashboard Error: {e}")
