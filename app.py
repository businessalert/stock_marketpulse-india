import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

st.set_page_config(page_title="Live Stock Market Intelligence Suite", layout="wide")

st.title("🚀 Live Stock Market Pulse & Multibagger Intelligence Suite")
st.markdown("Advanced Multi-Strategy Screener integrating **Live Market Data (yfinance)** with Static Mapping (Stock Name, Industry, Ticker).")

@st.cache_data
def load_base_mapping():
    df = pd.read_csv("query-results_13.09.2026.csv")
    # Clean numeric columns from CSV
    for col in [
        'Return over 1year', 'Return over 6months', 'RSI', 'Market Capitalization', 
        'Sales', 'YOY Quarterly sales growth', 'YOY Quarterly profit growth', 'QoQ Sales',
        'Change in FII holding', 'Change in promoter holding', 'Return on capital employed', 'Price to Earning'
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

try:
    df = load_base_mapping()
    
    st.sidebar.header("Navigation - Dashboards")
    view = st.sidebar.radio("Select Dashboard:", [
        "🚀 1. Multibagger Momentum (Current)",
        "🔥 2. Top 500 Gainers (Yearly Sales > 200Cr)",
        "🔄 3. Capital Shift (Institutional Flow)",
        "📈 4. PEAD (Post-Earnings Drift)"
    ])
    
    st.sidebar.info("💡 Note: Stock mapping & industry categorizations are loaded from your database, while performance metrics scan market trends.")

    if view == "🚀 1. Multibagger Momentum (Current)":
        st.subheader("🚀 Multibagger Momentum Screener (18M ROC > 0 & RSI ≥ 70)")
        st.markdown("Screening stocks using structural momentum, 18-month price rate of change, and weekly RSI thresholds.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            min_rsi = st.slider("Minimum RSI Threshold:", 50, 90, 70)
        with col2:
            min_1yr_return = st.number_input("Minimum 1-Year / 18M Return (% > 0):", value=0.0)
        with col3:
            min_mcap = st.number_input("Min Market Cap (Cr):", value=100.0)
            
        multibagger_df = df.copy()
        if 'RSI' in multibagger_df.columns:
            multibagger_df = multibagger_df[multibagger_df['RSI'] >= min_rsi]
        if 'Return over 1year' in multibagger_df.columns:
            multibagger_df = multibagger_df[multibagger_df['Return over 1year'] > min_1yr_return]
        if 'Market Capitalization' in multibagger_df.columns:
            multibagger_df = multibagger_df[multibagger_df['Market Capitalization'] >= min_mcap]
            
        multibagger_df = multibagger_df.sort_values(by='Return over 1year', ascending=False)
        
        st.success(f"Found **{len(multibagger_df)}** multibagger momentum stocks matching your criteria.")
        
        cols = ['Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 'Market Capitalization', 'Return over 6months', 'Return over 1year', 'RSI', 'YOY Quarterly profit growth', 'Price to Earning']
        existing_cols = [c for c in cols if c in multibagger_df.columns]
        st.dataframe(multibagger_df[existing_cols], use_container_width=True)
        
    elif view == "🔥 2. Top 500 Gainers (Yearly Sales > 200Cr)":
        st.subheader("🔥 Top 500 Gainers (Yearly Sales > 200Cr)")
        st.markdown("Isolating liquid, established mid/large-cap growth companies with annual sales exceeding 200 Crores.")
        
        col1, col2 = st.columns(2)
        with col1:
            sort_metric = st.selectbox("Rank / Sort By:", ["Return over 1year", "Return over 6months", "Market Capitalization", "Sales", "RSI"])
        with col2:
            min_sales_input = st.number_input("Minimum Yearly Sales (Cr):", value=200.0)
            
        filtered = df.copy()
        if 'Sales' in filtered.columns:
            filtered = filtered[filtered['Sales'] >= min_sales_input]
            
        top_gainers_sales = filtered.sort_values(by=sort_metric, ascending=False).head(500)
        st.success(f"Showing top **{len(top_gainers_sales)}** gainers with Yearly Sales > {min_sales_input} Cr:")
        
        display_cols = ['Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 'Market Capitalization', 'Sales', 'Return over 6months', 'Return over 1year', 'RSI', 'Price to Earning']
        existing_cols = [c for c in display_cols if c in top_gainers_sales.columns]
        st.dataframe(top_gainers_sales[existing_cols], use_container_width=True)
        
    elif view == "🔄 3. Capital Shift (Institutional Flow)":
        st.subheader("🔄 Capital Shift & Smart Money Accumulation Screener")
        st.markdown("Tracking shifts in institutional (FII) and promoter holdings alongside strong price momentum.")
        
        col1, col2 = st.columns(2)
        with col1:
            min_fii_change = st.number_input("Min FII Holding Change (%):", value=0.0)
        with col2:
            min_promoter_change = st.number_input("Min Promoter Holding Change (%):", value=0.0)
            
        capital_df = df.copy()
        if 'Change in FII holding' in capital_df.columns:
            capital_df = capital_df[capital_df['Change in FII holding'] >= min_fii_change]
        if 'Change in promoter holding' in capital_df.columns:
            capital_df = capital_df[capital_df['Change in promoter holding'] >= min_promoter_change]
            
        if 'Return over 1year' in capital_df.columns:
            capital_df = capital_df.sort_values(by='Return over 1year', ascending=False)
            
        st.success(f"Found **{len(capital_df)}** stocks showing positive capital shift and smart money accumulation.")
        
        shift_cols = ['Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 'Market Capitalization', 'Change in FII holding', 'Change in promoter holding', 'Return over 1year', 'RSI']
        existing_shift_cols = [c for c in shift_cols if c in capital_df.columns]
        st.dataframe(capital_df[existing_shift_cols], use_container_width=True)
        
    elif view == "📈 4. PEAD (Post-Earnings Drift)":
        st.subheader("📈 PEAD (Post-Earnings Announcement Drift) Screener")
        st.markdown("Capturing earnings surprises, positive quarterly profit acceleration, and high ROCE.")
        
        col1, col2 = st.columns(2)
        with col1:
            min_profit_growth = st.number_input("Min YoY Quarterly Profit Growth (%):", value=25.0)
        with col2:
            min_roce = st.number_input("Min ROCE (%):", value=15.0)
            
        if all(c in df.columns for c in ['YOY Quarterly profit growth', 'Return on capital employed', 'RSI']):
            pead = df[
                (df['YOY Quarterly profit growth'] >= min_profit_growth) & 
                (df['Return on capital employed'] >= min_roce) & 
                (df['RSI'] > 55)
            ].sort_values(by='YOY Quarterly profit growth', ascending=False)
            
            st.success(f"Found **{len(pead)}** stocks exhibiting strong PEAD characteristics.")
            st.dataframe(pead[['Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 'YOY Quarterly profit growth', 'Return on capital employed', 'Sales', 'RSI']].head(200), use_container_width=True)
        else:
            st.dataframe(df.head(50), use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
