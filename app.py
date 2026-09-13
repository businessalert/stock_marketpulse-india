import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="MarketPulse India: Institutional & PEAD Dashboard",
    page_icon="📈",
    layout="wide"
)

# --- Mock Data Generation with Sales & Multi-Horizon Metrics ---
@st.cache_data
def load_market_data():
    np.random.seed(42)
    n_stocks = 1200
    tickers = [f"STOCK{i}" for i in range(1, n_stocks + 1)]
    sectors = ['IT', 'Auto', 'Pharma', 'Banking', 'Metal', 'FMCG', 'Energy', 'Infra']
    industries = ['Software Services', 'Passenger Vehicles', 'Formulations', 'Private Banks', 'Steel', 'Packaged Foods', 'Oil & Gas', 'Construction']
    
    df = pd.DataFrame({
        'ticker': tickers,
        'company': [f"Company {i} Ltd" for i in range(1, n_stocks + 1)],
        'sector': np.random.choice(sectors, n_stocks),
        'industry': np.random.choice(industries, n_stocks),
        'sales_cr': np.random.uniform(50, 15000, n_stocks), # Annual sales in Crores INR
        'market_cap_cr': np.random.uniform(500, 100000, n_stocks), # Market Cap in Crores INR
        'ltp': np.random.uniform(150, 6000, n_stocks),
    })
    df['prev_close'] = df['ltp'] / np.random.uniform(0.92, 1.12, n_stocks)
    df['volume'] = np.random.randint(100000, 8000000, n_stocks)
    df['avg_volume_20d'] = df['volume'] / np.random.uniform(0.5, 5.0, n_stocks)
    df['day_low'] = df['prev_close'] * np.random.uniform(0.98, 1.03, n_stocks)
    df['day_high'] = df['ltp'] * np.random.uniform(1.0, 1.04, n_stocks)
    
    # Percentage changes
    df['pct_change'] = ((df['ltp'] - df['prev_close']) / df['prev_close']) * 100
    df['pct_1m'] = np.random.uniform(-15, 35, n_stocks)
    df['pct_3m'] = np.random.uniform(-25, 60, n_stocks)
    df['pct_6m'] = np.random.uniform(-40, 100, n_stocks)
    
    return df

@st.cache_data
def load_fundamental_data(tickers):
    n = len(tickers)
    return pd.DataFrame({
        'ticker': tickers,
        'eps_actual': np.random.uniform(5, 50, n),
        'eps_consensus': np.random.uniform(4, 45, n),
        'eps_std_dev': np.random.uniform(1, 5, n),
        'rev_actual': np.random.uniform(1000, 50000, n),
        'rev_consensus': np.random.uniform(900, 48000, n),
        'guidance_raised': np.random.choice([True, False], n, p=[0.25, 0.75])
    })

market_df = load_market_data()
fund_df = load_fundamental_data(market_df['ticker'].tolist())

# --- Dashboard Header ---
st.title("🇮🇳 MarketPulse India: Institutional & Positional Tracker")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Universe:** Filtered NSE/BSE Equities")

# --- Sidebar Controls & Filters ---
st.sidebar.header("Dashboard Filters")
min_sales = st.sidebar.slider("Min Annual Sales (₹ Crores)", min_value=0, max_value=2000, value=200, step=50)
selected_sector = st.sidebar.multiselect("Filter by Sector", options=market_df['sector'].unique(), default=market_df['sector'].unique())

# Apply Master Filters
filtered_market_df = market_df[(market_df['sales_cr'] >= min_sales) & (market_df['sector'].isin(selected_sector))]

# --- Navigation Tabs ---
tab1, tab2, tab3 = st.tabs(["🚀 Top 500 Gainers (Filtered)", "📊 Capital Shift Analyzer (1M/3M/6M)", "⚡ PEAD Intelligence Screener"])

# --- TAB 1: Top Gainers ---
with tab1:
    st.subheader("Top Daily Gainers (Sales ≥ ₹{} Cr)".format(min_sales))
    st.markdown("Tracks liquid mid-to-large cap momentum leaders with multi-horizon performance metrics.")
    
    top_gainers = filtered_market_df.sort_values(by='pct_change', ascending=False).head(500)
    
    display_gainers = top_gainers[[
        'ticker', 'company', 'sector', 'industry', 'market_cap_cr', 'sales_cr', 
        'ltp', 'pct_change', 'pct_1m', 'pct_3m', 'pct_6m', 'volume'
    ]].copy()
    
    # Rounding for clean display
    for col in ['market_cap_cr', 'sales_cr', 'ltp', 'pct_change', 'pct_1m', 'pct_3m', 'pct_6m']:
        display_gainers[col] = display_gainers[col].round(2)
        
    display_gainers = display_gainers.rename(columns={
        'market_cap_cr': 'Market Cap (₹ Cr)',
        'sales_cr': 'Sales (₹ Cr)',
        'ltp': 'Price (₹)',
        'pct_change': '1D %',
        'pct_1m': '1M %',
        'pct_3m': '3M %',
        'pct_6m': '6M %'
    })
    
    st.dataframe(display_gainers, use_container_width=True, height=550)

# --- TAB 2: Capital Shift Analyzer ---
with tab2:
    st.subheader("Industry Capital Shift & Multi-Horizon Momentum")
    st.markdown("Maps capital inflows, total traded turnover, and average momentum across 1M, 3M, and 6M timeframes.")
    
    filtered_market_df['value_traded'] = filtered_market_df['ltp'] * filtered_market_df['volume']
    
    capital_shift = filtered_market_df.groupby('industry').agg(
        total_capital_flow_inr=('value_traded', 'sum'),
        avg_1d=('pct_change', 'mean'),
        avg_1m=('pct_1m', 'mean'),
        avg_3m=('pct_3m', 'mean'),
        avg_6m=('pct_6m', 'mean'),
        gainer_count=('pct_change', lambda x: (x > 0).sum())
    ).reset_index()
    
    capital_shift['total_capital_flow_inr'] = (capital_shift['total_capital_flow_inr'] / 1e7).round(2)
    
    for col in ['avg_1d', 'avg_1m', 'avg_3m', 'avg_6m']:
        capital_shift[col] = capital_shift[col].round(2)
        
    capital_shift = capital_shift.rename(columns={
        'total_capital_flow_inr': 'Total Turnover (₹ Cr)',
        'avg_1d': 'Avg 1D %',
        'avg_1m': 'Avg 1M %',
        'avg_3m': 'Avg 3M %',
        'avg_6m': 'Avg 6M %',
        'gainer_count': 'Gainers Count'
    })
    
    capital_shift = capital_shift.sort_values(by='Total Turnover (₹ Cr)', ascending=False)
    st.dataframe(capital_shift, use_container_width=True, height=500)

# --- TAB 3: PEAD Screener ---
with tab3:
    st.subheader("Post-Earnings Announcement Drift (PEAD) Engine")
    st.markdown("Filters for Triple Beats, institutional opening gaps, and high volume velocity.")
    
    merged = pd.merge(filtered_market_df, fund_df, on='ticker', how='inner')
    merged['eps_sue'] = (merged['eps_actual'] - merged['eps_consensus']) / merged['eps_std_dev']
    
    triple_beat = (
        (merged['eps_sue'] >= 1.0) & 
        (merged['rev_actual'] > merged['rev_consensus']) & 
        (merged['guidance_raised'] == True)
    )
    
    merged['gap_pct'] = ((merged['day_low'] - merged['prev_close']) / merged['prev_close']) * 100
    merged['volume_multiple'] = merged['volume'] / merged['avg_volume_20d']
    
    institutional_footprint = (
        (merged['gap_pct'] >= 2.5) & 
        (merged['volume_multiple'] >= 2.5)
    )
    
    pead_candidates = merged[triple_beat & institutional_footprint].copy()
    pead_candidates['suggested_stop_loss'] = (pead_candidates['day_low'] * 0.99).round(2)
    pead_candidates['setup_classification'] = np.select(
        [
            pead_candidates['volume_multiple'] >= 4.0,
            pead_candidates['gap_pct'] >= 5.0
        ],
        ['High Tight Flag / Breakout Watch', 'Day 1 High Breakout Priority'],
        default='3-to-5 Day Pullback Candidate'
    )
    
    display_pead = pead_candidates[[
        'ticker', 'company', 'sector', 'market_cap_cr', 'sales_cr', 
        'pct_change', 'volume_multiple', 'gap_pct', 'setup_classification', 'suggested_stop_loss'
    ]].copy()
    
    for col in ['market_cap_cr', 'sales_cr', 'pct_change', 'volume_multiple', 'gap_pct']:
        display_pead[col] = display_pead[col].round(2)
        
    display_pead = display_pead.rename(columns={
        'market_cap_cr': 'Market Cap (₹ Cr)',
        'sales_cr': 'Sales (₹ Cr)',
        'pct_change': '1D %',
        'volume_multiple': 'Vol Multiple',
        'gap_pct': 'Gap %'
    })
    
    if len(display_pead) > 0:
        st.success(f"Found {len(display_pead)} high-probability PEAD setups meeting institutional criteria today.")
        st.dataframe(display_pead, use_container_width=True, height=450)
    else:
        st.warning("No stocks met the strict institutional PEAD criteria under current filters.")
