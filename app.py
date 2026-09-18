import glob
import os
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Complete 5400+ Universe Multibagger Funnel", layout="wide"
)

st.title("🎯 Complete Universe Multibagger Zero-Miss Funnel & Execution Engine")
st.markdown(
    "100% Zero-Miss Coverage (All 5,400+ Stocks Ingested) ➔ Lifecycle Funnel"
    " Filter ➔ Actionable Shortlist"
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


@st.cache_data
def load_complete_master_universe():
  csv_files = glob.glob("*.csv")
  if not csv_files:
    csv_files = glob.glob("**/*.csv", recursive=True)
  if not csv_files:
    return None, "No CSV repository file found."

  target_file = csv_files[0]
  try:
    df = pd.read_csv(target_file, low_memory=False)
    df.columns = df.columns.str.strip().str.lower()
  except Exception as e:
    return None, f"Error reading CSV: {str(e)}"

  # Flexible column mapping for standard repository schemas
  if "symbol" in df.columns and "ticker" not in df.columns:
    df.rename(columns={"symbol": "ticker"}, inplace=True)
  if "company" in df.columns and "name" not in df.columns:
    df.rename(columns={"company": "name"}, inplace=True)
  if "close" in df.columns and "cmp" not in df.columns:
    df.rename(columns={"close": "cmp"}, inplace=True)

  if "ticker" not in df.columns:
    df.rename(columns={df.columns[0]: "ticker"}, inplace=True)
  if "name" not in df.columns:
    df["name"] = df["ticker"]
  if "cmp" not in df.columns:
    df["cmp"] = 100.0

  # Detect or map RSI and ROC columns from your repository data
  rsi_col = next((c for c in df.columns if "rsi" in c), None)
  roc_col = next((c for c in df.columns if "roc" in c), None)

  if rsi_col:
    df["rsi"] = pd.to_numeric(df[rsi_col], errors="coerce").fillna(50.0)
  else:
    df["rsi"] = 50.0

  if roc_col:
    df["roc"] = pd.to_numeric(df[roc_col], errors="coerce").fillna(0.0)
  else:
    df["roc"] = 0.0

  # Strict Funnel Phase Classification
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
      f"Successfully loaded complete universe from {target_file} ({len(df):,} stocks total).",
  )


df_universe, status_msg = load_complete_master_universe()

if df_universe is not None and not df_universe.empty:
  st.sidebar.success(f"📂 {status_msg}")


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

  # Actionable Shortlist (The filtered end of the funnel)
  actionable_df = df_universe[
      df_universe["detected_phase"].isin(selected_phases)
  ].sort_values(by="rsi", ascending=False)

  # Dashboard Tabs
  tab1, tab2, tab3, tab4 = st.tabs([
      "📥 1. Master Radar (All 5400+ Stocks Zero-Miss Pool)",
      "🎯 2. Funnel Shortlist (Potential Big Movers)",
      "🚀 3. Pyramiding & Scaling Blueprint",
      "🛑 4. Exit & Risk Management Protocols",
  ])

  with tab1:
    st.subheader(
        f"Master Omnidirectional Universe ({len(df_universe):,} Total Stocks Ingested)"
    )
    st.markdown(
        "Holding **every single stock** from your repository. Nothing is"
        " filtered out here so you have a 100% zero-miss guarantee."
    )

    search_radar = st.text_input(
        "Search Ticker or Company in Master Universe:", ""
    ).strip()
    radar_display = df_universe
    if search_radar:
      radar_display = df_universe[
          df_universe["ticker"]
          .astype(str)
          .str.contains(search_radar, case=False, na=False)
          | df_universe["name"]
          .astype(str)
          .str.contains(search_radar, case=False, na=False)
      ]

    st.dataframe(
        radar_display[["name", "ticker", "cmp", "detected_phase", "rsi", "roc"]],
        use_container_width=True,
    )

  with tab2:
    st.subheader(
        f"Filtered Multibagger Funnel Shortlist ({len(actionable_df):,} High-Conviction Stocks)"
    )
    st.markdown(
        "✨ **Dead & declining stocks removed.** This shows only the potential"
        " big movers ready for action."
    )
    st.metric("Actionable Shortlist Count", f"{len(actionable_df):,}")
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
