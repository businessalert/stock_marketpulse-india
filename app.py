from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Live Multibagger Funnel & Execution Engine", layout="wide"
)

st.title("🎯 Live Multibagger Funnel & High-Conviction Execution Engine")
st.markdown(
    "Live Online Data Source (Yahoo Finance) ➔ Monthly RSI(14) & ROC(18)"
    " Calculation ➔ Actionable Funnel Shortlist"
)

# Sidebar Configuration for Portfolio Capital & Risk Parameters
st.sidebar.header("Portfolio Risk & Capital Controls")
total_capital = st.sidebar.number_input(
    "Total Portfolio Capital (₹)", value=1000000, step=50000
)
max_single_allocation_pct = st.sidebar.slider(
    "Max Core Allocation Limit (%)", 1, 15, 5
)

st.sidebar.header("Funnel Stage Filter")
selected_phases = st.sidebar.multiselect(
    "Filter Actionable Shortlist by Lifecycle Phase:",
    ["Accumulation", "Growth (Markup)", "Parabolic / Blow-Off"],
    default=["Accumulation", "Growth (Markup)", "Parabolic / Blow-Off"],
)


# Function to calculate RSI
def compute_rsi(series, period=14):
  delta = series.diff()
  gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
  rs = gain / loss
  return 100 - (100 / (1 + rs))


# Function to calculate Rate of Change (ROC)
def compute_roc(series, period=18):
  return ((series - series.shift(period)) / series.shift(period)) * 100


@st.cache_data(ttl=3600)
def fetch_live_market_universe():
  # Representative list of major NSE stocks for live online fetching.
  # You can expand or customize this list anytime.
  tickers = [
      "RELIANCE.NS",
      "TCS.NS",
      "HDFCBANK.NS",
      "INFY.NS",
      "ICICIBANK.NS",
      "HINDUNILVR.NS",
      "ITC.NS",
      "SBIN.NS",
      "BHARTIARTL.NS",
      "LICI.NS",
      "KOTAKBANK.NS",
      "LT.NS",
      "AXISBANK.NS",
      "ASIANPAINT.NS",
      "MARUTI.NS",
      "SUNPHARMA.NS",
      "TITAN.NS",
      "BAJFINANCE.NS",
      "TATAMOTORS.NS",
      "TATASTEEL.NS",
      "NTPC.NS",
      "POWERGRID.NS",
      "M&M.NS",
      "ADANIENT.NS",
      "COALINDIA.NS",
      "ZOMATO.NS",
      "JIOFIN.NS",
      "IRCTC.NS",
      "HAL.NS",
      "BEL.NS",
  ]

  data_rows = []

  # Fetch live monthly history from Yahoo Finance (Online Free Source)
  for ticker in tickers:
    try:
      stock = yf.Ticker(ticker)
      # Fetch 3 years of monthly data to accurately compute 14-period RSI and 18-period ROC on monthly intervals
      hist = stock.history(period="3y", interval="1mo")
      if not hist.empty and len(hist) > 20:
        close_series = hist["Close"]
        current_cmp = float(close_series.iloc[-1])

        # Compute technicals on live data
        monthly_rsi = compute_rsi(close_series, period=14).iloc[-1]
        monthly_roc = compute_roc(close_series, period=18).iloc[-1]

        data_rows.append({
            "ticker": ticker.replace(".NS", ""),
            "name": ticker.replace(".NS", ""),
            "cmp": round(current_cmp, 2),
            "rsi": (
                round(float(monthly_rsi), 2)
                if not pd.isna(monthly_rsi)
                else 50.0
            ),
            "roc": (
                round(float(monthly_roc), 2) if not pd.isna(monthly_roc) else 0.0
            ),
        })
    except Exception:
      continue

  df = pd.DataFrame(data_rows)
  if df.empty:
    return None, "Failed to fetch live data from online source."

  # Funnel Phase Classification Logic based on live calculated technicals
  conditions = [
      (df["rsi"] >= 80) & (df["roc"] > 35),
      (df["rsi"] >= 58) & (df["roc"] > 4),
      (df["rsi"] >= 45) & (df["rsi"] < 58),
  ]
  choices = [
      "Parabolic / Blow-Off",
      "Growth (Markup)",
      "Accumulation",
  ]
  df["detected_phase"] = np.select(conditions, choices, default="Decline / Dead")

  return (
      df,
      f"Successfully fetched live data for {len(df)} stocks from Yahoo Finance.",
  )


df_universe, status_msg = fetch_live_market_universe()

if df_universe is not None and not df_universe.empty:
  st.sidebar.success(f"🌐 {status_msg}")


  def calculate_execution_details(row):
    phase = row["detected_phase"]
    base_alloc = 0.0
    strategy = ""
    pyramiding = ""
    exit_rule = ""

    if phase == "Accumulation":
      base_alloc = 1.5
      strategy = "Probe Entry. Quiet base building under the surface."
      pyramiding = "Add 1.5% tranche on breakout from base with 3x volume."
      exit_rule = "Stop loss below structural base support."
    elif phase == "Growth (Markup)":
      base_alloc = min(4.0, float(max_single_allocation_pct))
      strategy = "Core Allocation. Active trend with steady upward trajectory."
      pyramiding = "Pyramid +2% on every 15% gain, move stop to break-even."
      exit_rule = "Trail stop loss using 20-day EMA."
    elif phase == "Parabolic / Blow-Off":
      base_alloc = min(5.0, float(max_single_allocation_pct))
      strategy = (
          "🚨 PARABOLIC PHASE: Maximum velocity. High risk of exhaustion."
      )
      pyramiding = "FREEZE NEW TRANCHES. Do not add fresh capital."
      exit_rule = "Aggressive Trailing Stop: Exit on close below prior day low."
    else:
      base_alloc = 0.0
      strategy = "Filtered out (Dead/Decline)."
      pyramiding = "None"
      exit_rule = "No allocation."

    allocated_amt = total_capital * (base_alloc / 100.0)
    return pd.Series(
        [base_alloc, allocated_amt, strategy, pyramiding, exit_rule]
    )


  df_universe[[
      "Recommended_Alloc_Pct",
      "Allocation_INR",
      "Strategy",
      "Pyramiding_Blueprint",
      "Exit_Rule",
  ]] = df_universe.apply(calculate_execution_details, axis=1)

  actionable_df = df_universe[
      df_universe["detected_phase"].isin(selected_phases)
  ].sort_values(by="rsi", ascending=False)

  # Dashboard Layout Tabs
  tab1, tab2, tab3, tab4 = st.tabs([
      "📥 1. Master Radar (Live Online Universe)",
      "🎯 2. Funnel Shortlist (Potential Big Movers)",
      "🚀 3. Pyramiding & Scaling Blueprint",
      "🛑 4. Exit & Risk Management Protocols",
  ])

  with tab1:
    st.subheader(
        f"Master Live Universe ({len(df_universe)} Stocks Fetched Online)"
    )
    st.markdown(
        "Real-time prices and monthly technicals pulled directly from online"
        " sources."
    )

    search_radar = st.text_input("Search Ticker:", "").strip()
    radar_display = df_universe
    if search_radar:
      radar_display = df_universe[
          df_universe["ticker"]
          .astype(str)
          .str.contains(search_radar, case=False, na=False)
      ]

    st.dataframe(
        radar_display[["name", "ticker", "cmp", "detected_phase", "rsi", "roc"]],
        use_container_width=True,
    )

  with tab2:
    st.subheader(
        f"Filtered Multibagger Funnel Shortlist ({len(actionable_df)} High-Conviction Stocks)"
    )
    st.metric("Actionable Shortlist Count", len(actionable_df))
    st.dataframe(
        actionable_df[[
            "name",
            "ticker",
            "cmp",
            "detected_phase",
            "Recommended_Alloc_Pct",
            "Allocation_INR",
            "Strategy",
            "rsi",
            "roc",
        ]],
        use_container_width=True,
    )

  with tab3:
    st.subheader("Pyramiding Structure for Funnel Shortlist")
    st.dataframe(
        actionable_df[["name", "ticker", "detected_phase", "Pyramiding_Blueprint"]],
        use_container_width=True,
    )

  with tab4:
    st.subheader("Trailing Stops & Exit Protocols for Active Positions")
    st.dataframe(
        actionable_df[["name", "ticker", "detected_phase", "Exit_Rule"]],
        use_container_width=True,
    )

else:
  st.error(f"❌ {status_msg}")
