import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Master Multibagger & Portfolio Execution Engine", layout="wide"
)

st.title("🎯 Master Multibagger Zero-Miss & Parabolic Execution Dashboard")
st.markdown(
    "Omnidirectional Funnel: Wide Net Ingestion + Life-Cycle Tagging (Incl."
    " Parabolic) + Dynamic Sizing + Pyramiding"
)

# Sidebar Configuration for Portfolio Capital & Risk Parameters
st.sidebar.header("Portfolio Risk & Capital Controls")
total_capital = st.sidebar.number_input(
    "Total Portfolio Capital (₹)", value=1000000, step=50000
)
max_single_allocation_pct = st.sidebar.slider(
    "Max Core Allocation Limit (%)", 1, 15, 5
)
enable_pyramiding = st.sidebar.checkbox(
    "Enable Pyramiding Rules Engine", value=True
)


# Master Data Loader with Life-Cycle Analysis & Reasons
@st.cache_data
def load_master_universe():
  data = {
      "Name": [
          "Fonebox Retail",
          "Anand Rathi Wealth",
          "CP Capital",
          "Castrol India",
          "Foseco India",
          "Arrow Greentech",
          "ACME Solar Hold.",
          "Anthem Bioscience",
          "AMD Industries",
          "GNFC",
      ],
      "Ticker": [
          "FONEBOX",
          "ANANDRATHI",
          "CPCAP",
          "CASTROLIND",
          "FOSECOIND",
          "ARROWGREEN",
          "ACMESOLAR",
          "ANTHEM",
          "AMDIND",
          "GNFC",
      ],
      "CMP": [180.0, 2400.0, 115.0, 210.0, 3200.0, 450.0, 290.0, 650.0, 95.0, 780.0],
      "Life_Cycle_Phase": [
          "Growth (Markup)",
          "Growth (Markup)",
          "Accumulation",
          "Decline",
          "Growth (Markup)",
          "Accumulation",
          "Accumulation",
          "Growth (Markup)",  # Will be dynamically upgraded to Parabolic if RSI/ROC criteria hit
          "Decline",
          "Growth (Markup)",
      ],
      "Trigger_Reason": [
          "High volume breakout + OBV rising near resistance",
          "Strong institutional buying + consistent earnings expansion",
          "Tight base compression (6 weeks) + zero promoter pledging",
          "Falling momentum + contracting operating cash flows",
          "Spike in ROC + major order book win announcement",
          "Rising OBV during sideways channel + high promoter holding",
          "New renewable energy capacity addition + quiet accumulation",
          "RSI overbought + massive volume vertical expansion",
          "Negative operating margins + breakdown of key moving average",
          "Breakout with volume surge + positive cash flow conversion",
      ],
      "RSI": [72.5, 68.0, 52.1, 41.0, 78.4, 49.0, 55.0, 84.5, 38.0, 70.2],
      "ROC": [15.2, 8.1, 4.2, -3.2, 38.5, 2.1, 1.5, 42.0, -2.0, 12.4],
      "Volume_Surge": [
          True,
          False,
          False,
          False,
          True,
          False,
          False,
          True,
          False,
          True,
      ],
      "Promoter_Holding": [72.0, 65.0, 55.0, 51.0, 75.0, 68.0, 80.0, 60.0, 58.0, 57.0],
      "CFO_Positive": [
          True,
          True,
          True,
          True,
          True,
          True,
          False,
          True,
          True,
          True,
      ],
  }
  return pd.DataFrame(data)


df_universe = load_master_universe()


# Advanced Execution Plan with Parabolic Override Logic
def calculate_advanced_execution_plan(row):
  phase = row["Life_Cycle_Phase"]
  rsi = row["RSI"]
  roc = row["ROC"]

  # Parabolic Override Detection (Vertical momentum squeeze)
  if rsi >= 80 and roc > 35:
    phase = "Parabolic / Blow-Off"

  base_alloc_pct = 0.0
  strategy = ""
  pyramiding_rule = ""
  exit_rule = ""

  if phase == "Accumulation":
    base_alloc_pct = 1.5
    strategy = "Initial Probe Entry. Quiet base building under the surface."
    pyramiding_rule = (
        "Add 1.5% tranche only when price breaks out of base with 3x volume."
    )
    exit_rule = "Stop loss below structural base support."

  elif phase == "Growth (Markup)":
    base_alloc_pct = 4.0
    strategy = "Core Allocation. Trend is active; steady upward trajectory."
    pyramiding_rule = (
        "Pyramid +2% on every 15% gain, shifting initial stop-loss to break-even."
    )
    exit_rule = "Trail stop loss using 20-day EMA."

  elif phase == "Parabolic / Blow-Off":
    base_alloc_pct = (
        5.0  # Max exposure if already riding, but strict harvesting rules
    )
    strategy = (
        "🚨 PARABOLIC PHASE: Maximum velocity. High risk of near-term"
        " exhaustion."
    )
    pyramiding_rule = (
        "DO NOT ADD FRESH CAPITAL. Freeze new tranches immediately."
    )
    exit_rule = (
        "Aggressive Trailing Stop: Exit 30% on every 10% extension or if price"
        " closes below prior day low."
    )

  elif phase == "Distribution":
    base_alloc_pct = 1.0
    strategy = "Profit Booking / Warning Phase. Momentum fading."
    pyramiding_rule = "None. Liquidate positions systematically."
    exit_rule = "Exit remaining position."

  elif phase == "Decline":
    base_alloc_pct = 0.0
    strategy = "Capital preservation. Trend broken."
    pyramiding_rule = "None."
    exit_rule = "Zero allocation."

  allocated_funds = total_capital * (base_alloc_pct / 100.0)
  return pd.Series([
      phase,
      base_alloc_pct,
      allocated_funds,
      strategy,
      pyramiding_rule,
      exit_rule,
  ])


# Apply advanced logic to dataset
df_universe[[
    "Detected_Phase",
    "Recommended_Alloc_Pct",
    "Allocation_Amount_INR",
    "Execution_Strategy",
    "Pyramiding_Blueprint",
    "Exit_Management_Rule",
]] = df_universe.apply(calculate_advanced_execution_plan, axis=1)

# Dashboard Layout Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📥 Master Radar (Zero-Miss Pool)",
    "🎯 Core Allocation & Phase Matrix",
    "🚀 Parabolic & Pyramiding Blueprint",
    "🛑 Exit & Risk Management Rules",
])

with tab1:
  st.subheader("Master Omnidirectional Database (All Potential Movers)")
  st.markdown(
      "Every single stock captured via accumulation, special situations, or"
      " momentum. Nothing is hidden."
  )
  st.dataframe(
      df_universe[
          [
              "Name",
              "Ticker",
              "CMP",
              "Detected_Phase",
              "Trigger_Reason",
              "RSI",
              "ROC",
          ]
      ],
      use_container_width=True,
  )

with tab2:
  st.subheader("Actionable Allocation Plan Based on Life-Cycle & Parabolic Stage")
  st.markdown(
      "Positions scale up dynamically based on cycle maturity to avoid dead"
      " capital."
  )
  active_portfolio_view = df_universe[
      df_universe["Recommended_Alloc_Pct"] > 0
  ].sort_values(by="Recommended_Alloc_Pct", ascending=False)
  st.dataframe(
      active_portfolio_view[
          [
              "Name",
              "Ticker",
              "Detected_Phase",
              "Recommended_Alloc_Pct",
              "Allocation_Amount_INR",
              "Execution_Strategy",
          ]
      ],
      use_container_width=True,
  )

with tab3:
  st.subheader("Pyramiding Structure & Profit Optimization Blueprint")
  st.markdown(
      "Ensures profits are locked in and scaled systematically as positions run"
      " through markup and parabolic stages."
  )
  st.dataframe(
      df_universe[
          [
              "Name",
              "Ticker",
              "Detected_Phase",
              "Pyramiding_Blueprint",
          ]
      ],
      use_container_width=True,
  )

with tab4:
  st.subheader("Trailing Stops & Exit Protocols")
  st.markdown(
      "Guards against giving back open profits during parabolic blow-offs or"
      " structural trend breakdowns."
  )
  st.dataframe(
      df_universe[
          [
              "Name",
              "Ticker",
              "Detected_Phase",
              "Exit_Management_Rule",
          ]
      ],
      use_container_width=True,
  )
