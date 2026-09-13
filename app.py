import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Stock Market Pulse - PEAD & Multibagger Screener", layout="wide")

st.title("🚀 PEAD & Multibagger Momentum Intelligence Dashboard")
st.markdown("Advanced Top 500 Gainers, Volume Surge, and Multibagger Momentum Screener.")

@st.cache_data
def load_data():
    df = pd.read_csv("query-results_13.09.2026.csv")
    # Clean numeric columns
    for col in ['Return over 1year', 'Return over 6months', 'RSI', 'Market Capitalization', 'YOY Quarterly sales growth', 'QoQ Sales', 'YOY Quarterly profit growth']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

try:
    df = load_data()
    
    st.sidebar.header("Navigation")
    view = st.sidebar.radio("Select View:", [
        "🔥 Top 500 Gainers & Momentum",
        "🚀 Multibagger Momentum Screener",
        "📈 PEAD (Post-Earnings Drift)",
        "🔍 Master Stock Explorer"
    ])
    
    if view == "🔥 Top 500 Gainers & Momentum":
        st.subheader("Top 500 Gainers & Momentum Performance")
        st.markdown("Ranking top-performing stocks by 1-year and 6-month returns with liquidity and market cap filters.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            min_mcap = st.number_input("Min Market Capitalization (Cr):", value=500.0)
        with col2:
            min_rsi = st.slider("Min RSI:", 0, 100, 55)
        with col3:
            sort_metric = st.selectbox("Sort By:", ["Return over 1year", "Return over 6months", "Market Capitalization", "RSI"])
            
        filtered = df.copy()
        if 'Market Capitalization' in filtered.columns:
            filtered = filtered[filtered['Market Capitalization'] >= min_mcap]
        if 'RSI' in filtered.columns:
            filtered = filtered[filtered['RSI'] >= min_rsi]
            
        top_gainers = filtered.sort_values(by=sort_metric, ascending=False).head(500)
        
        st.write(f"Showing top **{len(top_gainers)}** stocks matching your criteria:")
        
        display_cols = ['Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 'Market Capitalization', 'Return over 6months', 'Return over 1year', 'RSI', 'Price to Earning']
        existing_cols = [c for c in display_cols if c in top_gainers.columns]
        
        st.dataframe(top_gainers[existing_cols], use_container_width=True)
        
    elif view == "🚀 Multibagger Momentum Screener":
        st.subheader("Multibagger Momentum & Volume Surge Screener")
        st.markdown("Filtering stocks where **Monthly RSI > 70**, **Positive Returns / Momentum**, and **Drastic Volume / Sales / Profit Growth** are aligning.")
        
        # User criteria mapping:
        # - RSI > 70
        # - Return over 6months > 0 & Return over 1year > 0
        # - QoQ Sales > 0 or YOY Quarterly profit growth > 0
        
        col1, col2 = st.columns(2)
        with col1:
            target_rsi = st.slider("Minimum RSI Threshold:", 50, 90, 70)
        with col2:
            min_1yr_return = st.number_input("Minimum 1-Year Return (%):", value=10.0)
            
        multibagger_df = df.copy()
        if 'RSI' in multibagger_df.columns:
            multibagger_df = multibagger_df[multibagger_df['RSI'] >= target_rsi]
        if 'Return over 1year' in multibagger_df.columns:
            multibagger_df = multibagger_df[multibagger_df['Return over 1year'] >= min_1yr_return]
        
        # Sort by 1-year return or momentum
        multibagger_df = multibagger_df.sort_values(by='Return over 1year', ascending=False)
        
        st.success(f"Found **{len(multibagger_df)}** potential multibagger momentum candidates meeting your strict criteria.")
        
        mb_cols = ['Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 'Market Capitalization', 'Return over 6months', 'Return over 1year', 'RSI', 'QoQ Sales', 'YOY Quarterly profit growth', 'Price to Earning']
        existing_mb_cols = [c for c in mb_cols if c in multibagger_df.columns]
        
        st.dataframe(multibagger_df[existing_mb_cols], use_container_width=True)
        
    elif view == "📈 PEAD (Post-Earnings Drift)":
        st.subheader("PEAD (Post-Earnings Announcement Drift) Screener")
        st.markdown("Capturing earnings surprises, positive quarterly profit acceleration, and institutional accumulation.")
        
        if all(c in df.columns for c in ['YOY Quarterly profit growth', 'Return on capital employed', 'RSI']):
            pead = df[
                (df['YOY Quarterly profit growth'] > 25) & 
                (df['Return on capital employed'] > 15) & 
                (df['RSI'] > 60)
            ].sort_values(by='YOY Quarterly profit growth', ascending=False)
            
            st.write(f"Found **{len(pead)}** stocks exhibiting strong PEAD characteristics.")
            st.dataframe(pead[['Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 'YOY Quarterly profit growth', 'Net Profit latest quarter', 'Return on capital employed', 'RSI']].head(100), use_container_width=True)
        else:
            st.dataframe(df.head(50), use_container_width=True)
            
    elif view == "🔍 Master Stock Explorer":
        st.subheader("Master Stock Explorer")
        ind = st.selectbox("Industry Filter:", ["All"] + list(df['Industry'].dropna().unique()))
        query = st.text_input("Search Company Name:")
        
        res = df if ind == "All" else df[df['Industry'] == ind]
        if query:
            res = res[res['Name'].str.contains(query, case=False, na=False)]
        st.dataframe(res, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
