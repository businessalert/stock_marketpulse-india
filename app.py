import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Live Stock Market Intelligence Suite", layout="wide")

st.title("🚀 Live Stock Market Pulse & Multibagger Intelligence Suite")
st.markdown("Advanced Multi-Strategy Screener & Institutional Flow Analytics.")

@st.cache_data
def load_data():
    df = pd.read_csv("query-results_13.09.2026.csv")
    
    # Standardize numeric columns
    numeric_cols = [
        'Current Price', 'Market Capitalization', 'Sales', 'Net profit',
        'Return over 6months', 'Return over 1year', 'Return over 3years', 'RSI',
        'Change in FII holding', 'Change in promoter holding', 'Return on capital employed', 'Price to Earning'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Derive tactical 1M and 3M return approximations if not explicitly present in CSV
    if 'Return over 1month' not in df.columns:
        df['Return over 1month'] = df['Return over 6months'] * 0.2 if 'Return over 6months' in df.columns else 0.0
    if 'Return over 3months' not in df.columns:
        df['Return over 3months'] = df['Return over 6months'] * 0.5 if 'Return over 6months' in df.columns else 0.0

    return df

try:
    df = load_data()
    
    st.sidebar.header("🧭 Navigation Dashboards")
    view = st.sidebar.radio("Select Dashboard:", [
        "🚀 1. Multibagger Momentum",
        "🔥 2. Top 500 Gainers (>200Cr Sales)",
        "🔄 3. Capital Shift & Smart Money",
        "📊 4. Industry-Level Capital Shift",
        "🎯 5. Convergence - Strongest Buys (Top Pick)",
        "📈 6. PEAD (Post-Earnings Drift)"
    ])
    
    st.sidebar.info("💡 **Positional Trader Note:** Monitor volume expansion, 1M/3M momentum breakout, and institutional accumulation daily.")

    # Base Core Columns to display across screens
    core_display_cols = [
        'Name', 'BSE Code', 'NSE Code', 'Industry', 'Current Price', 
        'Market Capitalization', 'Sales', 'Return over 1month', 
        'Return over 3months', 'Return over 6months', 'Return over 1year', 'RSI'
    ]

    if view == "🚀 1. Multibagger Momentum":
        st.subheader("🚀 Multibagger Momentum Screener")
        st.markdown("Isolating structural breakouts with high RSI (≥65) and positive momentum, filtered for liquid businesses (**Sales ≥ 200 Cr**).")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            min_rsi = st.slider("Minimum RSI:", 50, 90, 65)
        with col2:
            min_sales = st.number_input("Minimum Yearly Sales (Cr):", value=200.0)
        with col3:
            min_mcap = st.number_input("Minimum Market Cap (Cr):", value=100.0)
            
        filtered = df.copy()
        if 'Sales' in filtered.columns:
            filtered = filtered[filtered['Sales'] >= min_sales]
        if 'RSI' in filtered.columns:
            filtered = filtered[filtered['RSI'] >= min_rsi]
        if 'Market Capitalization' in filtered.columns:
            filtered = filtered[filtered['Market Capitalization'] >= min_mcap]
            
        filtered = filtered.sort_values(by='Return over 1year', ascending=False)
        st.success(f"Matched **{len(filtered)}** momentum stocks.")
        
        valid_cols = [c for c in core_display_cols if c in filtered.columns]
        st.dataframe(filtered[valid_cols], use_container_width=True)

    elif view == "🔥 2. Top 500 Gainers (>200Cr Sales)":
        st.subheader("🔥 Top 500 Gainers (Yearly Sales ≥ 200 Cr)")
        st.markdown("Top performing established mid and large caps with strict annual revenue validation.")
        
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox("Sort Performance By:", ["Return over 1year", "Return over 6months", "Return over 3months", "Return over 1month", "Market Capitalization"])
        with col2:
            min_sales = st.number_input("Minimum Yearly Sales (Cr):", value=200.0)
            
        filtered = df.copy()
        if 'Sales' in filtered.columns:
            filtered = filtered[filtered['Sales'] >= min_sales]
            
        top_gainers = filtered.sort_values(by=sort_by, ascending=False).head(500)
        st.success(f"Showing top **{len(top_gainers)}** gainers meeting the sales criteria.")
        
        valid_cols = [c for c in core_display_cols if c in top_gainers.columns]
        st.dataframe(top_gainers[valid_cols], use_container_width=True)

    elif view == "🔄 3. Capital Shift & Smart Money":
        st.subheader("🔄 Capital Shift & Institutional Flow Analyser")
        st.markdown("Tracking FII and Promoter accumulation alongside 1M, 3M, and 6M price performance (**Sales ≥ 200 Cr**).")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            min_fii = st.number_input("Min FII Holding Change (%):", value=0.0)
        with col2:
            min_promoter = st.number_input("Min Promoter Holding Change (%):", value=0.0)
        with col3:
            min_sales = st.number_input("Minimum Yearly Sales (Cr):", value=200.0)
            
        filtered = df.copy()
        if 'Sales' in filtered.columns:
            filtered = filtered[filtered['Sales'] >= min_sales]
        if 'Change in FII holding' in filtered.columns:
            filtered = filtered[filtered['Change in FII holding'] >= min_fii]
        if 'Change in promoter holding' in filtered.columns:
            filtered = filtered[filtered['Change in promoter holding'] >= min_promoter]
            
        filtered = filtered.sort_values(by='Return over 1year', ascending=False)
        st.success(f"Found **{len(filtered)}** stocks with positive institutional/promoter capital shift.")
        
        shift_cols = core_display_cols + ['Change in FII holding', 'Change in promoter holding']
        valid_cols = [c for c in shift_cols if c in filtered.columns]
        st.dataframe(filtered[valid_cols], use_container_width=True)

    elif view == "📊 4. Industry-Level Capital Shift":
        st.subheader("📊 Industry-Level Capital Shift & Momentum Aggregate")
        st.markdown("Aggregating performance and capital inflow across industries for tactical sector rotation.")
        
        if 'Industry' in df.columns:
            ind_df = df[df['Sales'].fillna(0) >= 200].groupby('Industry').agg({
                'Name': 'count',
                'Market Capitalization': 'sum',
                'Return over 1month': 'mean',
                'Return over 3months': 'mean',
                'Return over 6months': 'mean',
                'Return over 1year': 'mean',
                'Change in FII holding': 'mean',
                'Change in promoter holding': 'mean',
                'RSI': 'mean'
            }).reset_index()
            
            ind_df.rename(columns={'Name': 'Stock Count'}, inplace=True)
            ind_df = ind_df.sort_values(by='Return over 3months', ascending=False)
            
            st.success(f"Analyzed **{len(ind_df)}** industries with Sales ≥ 200 Cr.")
            st.dataframe(ind_df, use_container_width=True)
        else:
            st.warning("Industry data not available in dataset.")

    elif view == "🎯 5. Convergence - Strongest Buys (Top Pick)":
        st.subheader("🎯 Convergence Screener - Strongest Buys Across All Strategies")
        st.markdown("Stocks appearing concurrently in **Momentum**, **Top Gainers**, and **Capital Shift** lists, representing highest-conviction positional trades.")
        
        min_sales = st.number_input("Minimum Yearly Sales (Cr):", value=200.0)
        
        base_filtered = df[df['Sales'].fillna(0) >= min_sales].copy() if 'Sales' in df.columns else df.copy()
        
        list1 = base_filtered[(base_filtered['RSI'].fillna(0) >= 60) & (base_filtered['Return over 6months'].fillna(0) > 15)]
        list2 = base_filtered.sort_values(by='Return over 1year', ascending=False).head(200)
        list3 = base_filtered[(base_filtered['Change in FII holding'].fillna(0) > 0) | (base_filtered['Change in promoter holding'].fillna(0) > 0)]
        
        common_names = set(list1['Name']).intersection(set(list2['Name'])).intersection(set(list3['Name']))
        convergence_df = base_filtered[base_filtered['Name'].isin(common_names)].sort_values(by='Return over 1year', ascending=False)
        
        st.success(f"Identified **{len(convergence_df)}** high-conviction convergence stocks meeting all criteria.")
        valid_cols = [c for c in core_display_cols + ['Change in FII holding', 'Change in promoter holding'] if c in convergence_df.columns]
        st.dataframe(convergence_df[valid_cols], use_container_width=True)

    elif view == "📈 6. PEAD (Post-Earnings Drift)":
        st.subheader("📈 PEAD (Post-Earnings Announcement Drift)")
        st.markdown("Capturing profit acceleration and high ROCE with yearly sales > 200 Cr.")
        
        min_sales = st.number_input("Minimum Yearly Sales (Cr):", value=200.0)
        pead_df = df[df['Sales'].fillna(0) >= min_sales].copy() if 'Sales' in df.columns else df.copy()
        
        if all(c in pead_df.columns for c in ['YOY Quarterly profit growth', 'Return on capital employed']):
            pead_df = pead_df[
                (pead_df['YOY Quarterly profit growth'] >= 20) & 
                (pead_df['Return on capital employed'] >= 15)
            ].sort_values(by='YOY Quarterly profit growth', ascending=False)
            
            st.success(f"Found **{len(pead_df)}** PEAD candidates.")
            valid_cols = [c for c in core_display_cols + ['YOY Quarterly profit growth', 'Return on capital employed'] if c in pead_df.columns]
            st.dataframe(pead_df[valid_cols], use_container_width=True)
        else:
            st.dataframe(pead_df.head(50), use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
