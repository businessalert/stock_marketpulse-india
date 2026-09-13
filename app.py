import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="MarketPulse India: Gainers, Capital Shift & PEAD Dashboard",
    page_icon="📈",
    layout="wide"
)

# --- Mock Data Generation (Replace with live API / DB fetch later) ---
@st.cache_data
def load_market_data():
    np.random.seed(42)
    n_stocks = 1200
    tickers = [f"STOCK{i}" for i in range(1, n_stocks + 1)]
    sectors = ['IT', 'Auto', 'Pharma', 'Banking', 'Metal', 'FMCG', 'Energy', 'Infra']
    industries = ['Software Services', 'Passenger Vehicles', 'Formulations', 'Private Banks', 'Steel', 'Packaged Foods', 'Oil & Gas', 'Construction']
    
    data = {
        'ticker': tickers,
        'company': [f"Company {i} Ltd" for i in range(1, n_stocks + 1)],
        'sector': np.random.choice(sectors, n_stocks),
        'industry': np.random.choice(industries, n_stocks),
        'ltp': np.random.uniform(100, 5000, n_stocks),
        'prev_close': lambda df: df['ltp'] * np.random.uniform(0.90, 1.12, n_stocks),
    }
    df = pd.DataFrame({
        'ticker': tickers,
        'company': [f"Company {i} Ltd" for i in range(1, n_stocks + 1)],
        'sector': np.random.choice(sectors, n_stocks),
        'industry': np.random.choice(industries, n_stocks),
        'ltp': np.random.uniform(100, 5000, n_stocks),
    })
    df['prev_close'] = df['ltp'] / np.random.uniform(0.92, 1.15, n_stocks)
    df['volume'] = np.random.randint(50000, 5000000, n_stocks)
    df['avg_volume_20d'] = df['volume'] / np.random.uniform(0.5, 6.0, n_stocks)
    df['day_low'] = df['prev_close'] * np.random.uniform(0.98, 1.05, n_stocks)
    df['day_high'] = df['ltp'] * np.random.uniform(1.0, 1.04, n_stocks)
    df['pct_change'] = ((df['ltp'] - df['prev_close']) / df['prev_close']) * 100
    
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
        'guidance_raised': np.random.choice([True, False], n, p=[0.2, 0.8])
    })

market_df = load_market_data()
fund_df = load_fundamental_data(market_df['ticker'].tolist())

# --- Dashboard Header ---
st.title("🇮🇳 MarketPulse India: Daily Institutional Tracking Dashboard")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Universe:** NSE/BSE All Listed Equities")

# --- Sidebar Filters ---
st.sidebar.header("Dashboard Controls")
selected_sector = st.sidebar.multiselect("Filter by Sector", options=market_df['sector'].unique(), default=market_df['sector'].unique())

# Filter data based on sidebar
filtered_market_df = market_df[market_df['sector'].isin(selected_sector)]

# --- Navigation Tabs ---
tab1, tab2, tab3 = st.tabs(["🚀 Top 500 Daily Gainers", "📊 Capital Shift Analyzer", "⚡ PEAD Intelligence Screener"])

# --- TAB 1: Top 500 Gainers ---
with tab1:
    st.subheader("Top 500 Daily Gainers Leaderboard")
    st.markdown("Tracks the strongest momentum stocks across the Indian stock market sorted by highest daily percentage change.")
    
    top_gainers = filtered_market_df.sort_values(by='pct_change', ascending=False).head(500)
    
    # Format display columns
    display_gainers = top_gainers[['ticker', 'company', 'sector', 'industry', 'ltp', 'pct_change', 'volume']].copy()
    display_gainers['pct_change'] = display_gainers['pct_change'].round(2)
    display_gainers['ltp'] = display_gainers['ltp'].round(2)
    
    st.dataframe(display_gainers, use_container_width=True, height=500)

# --- TAB 2: Capital Shift Analyzer ---
with tab2:
    st.subheader("Industry & Product Segment Capital Shift")
    st.markdown("Maps capital allocation inflows, average price momentum, and breakout breadth across sectors and sub-industries.")
    
    filtered_market_df['value_traded'] = filtered_market_df['ltp'] * filtered_market_df['volume']
    
    capital_shift = filtered_market_df.groupby('industry').agg(
        total_capital_flow_inr=('value_traded', 'sum'),
        avg_industry_pct_change=('pct_change', 'mean'),
        gainer_count=('pct_change', lambda x: (x > 0).sum())
    ).reset_index()
    
    capital_shift['total_capital_flow_inr'] = (capital_shift['total_capital_flow_inr'] / 1e7).round(2) # in Crores INR
    capital_shift = capital_shift.rename(columns={'total_capital_flow_inr': 'Total Value Traded (₹ Crores)'})
    capital_shift = capital_shift.sort_values(by='Total Value Traded (₹ Crores)', ascending=False)
    
    st.dataframe(capital_shift, use_container_width=True, height=450)

# --- TAB 3: PEAD Intelligence Screener ---
with tab3:
    st.subheader("Post-Earnings Announcement Drift (PEAD) Engine")
    st.markdown("Filters for Triple Beats (EPS + Revenue + Guidance), massive opening gaps, and high institutional volume accumulation.")
    
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
        (merged['gap_pct'] >= 3.0) & 
        (merged['volume_multiple'] >= 2.5)
    )
    
    pead_candidates = merged[triple_beat & institutional_footprint].copy()
    pead_candidates['suggested_stop_loss'] = (pead_candidates['day_low'] * 0.99).round(2)
    pead_candidates['setup_classification'] = np.select(
        [
            pead_candidates['volume_multiple'] >= 4.0,
            pead_candidates['gap_pct'] >= 6.0
        ],
        ['High Tight Flag / Breakout Watch', 'Day 1 High Breakout Priority'],
        default='3-to-5 Day Pullback Candidate'
    )
    
    display_pead = pead_candidates[[
        'ticker', 'company', 'sector', 'pct_change', 'volume_multiple', 
        'gap_pct', 'setup_classification', 'suggested_stop_loss'
    ]].copy()
    
    display_pead['pct_change'] = display_pead['pct_change'].round(2)
    display_pead['volume_multiple'] = display_pead['volume_multiple'].round(2)
    display_pead['gap_pct'] = display_pead['gap_pct'].round(2)
    
    if len(display_pead) > 0:
        st.success(f"Found {len(display_pead)} high-probability PEAD setups meeting institutional criteria today.")
        st.dataframe(display_pead, use_container_width=True, height=450)
    else:
        st.warning("No stocks met the strict institutional PEAD criteria under current filters.")
