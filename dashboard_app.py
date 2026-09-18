import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Advanced Multibagger & Breakout Screener", layout="wide"
)

st.title("🎯 Advanced Multibagger Breakout & Accumulation Dashboard")
st.markdown(
    "Combined Engine: Active Momentum Breakouts + Pre-Breakout Accumulation Radar"
)

# Sidebar Configuration for Thresholds
st.sidebar.header("Engine Parameters")
rsi_min = st.sidebar.slider("RSI Min (Active Breakout)", 50, 75, 69)
rsi_max = st.sidebar.slider("RSI Max (Active Breakout)", 75, 95, 80)
min_promoter_holding = st.sidebar.slider(
    "Min Promoter Holding (%)", 0, 90, 50
)
min_consolidation_weeks = st.sidebar.slider(
    "Min Consolidation Weeks (Accumulation)", 1, 12, 4
)


# Mock data loader or CSV connector function
@st.cache_data
def load_screener_data():
  # In your actual implementation, replace this with your CSV loading logic:
  # df = pd.read_csv("your_master_list.csv")
  # Below is the schema structure required to drive both engines:
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
      "Industry": [
          "Specialty Retail",
          "Financial Products",
          "NBFC",
          "Lubricants",
          "Specialty Chemicals",
          "Packaging",
          "Power Generation",
          "Biotechnology",
          "Packaging",
          "Commodity Chemicals",
      ],
      "RSI": [72.5, 68.0, 75.1, 45.0, 78.4, 62.0, 55.0, 81.0, 48.0, 70.2],
      "Volume_Surge": [True, False, True, False, True, False, False, True, False, True],
      "ROC": [5.2, -1.1, 12.4, -3.2, 8.5, 1.2, 0.5, 14.1, -2.0, 3.4],
      "OBV_Trend": [
          "Rising",
          "Flat",
          "Rising",
          "Falling",
          "Rising",
          "Rising",
          "Flat",
          "Rising",
          "Falling",
          "Rising",
      ],
      "Price_Consolidation_Weeks": [5, 2, 6, 1, 4, 6, 3, 2, 1, 5],
      "Promoter_Holding": [72.0, 65.0, 55.0, 51.0, 75.0, 68.0, 80.0, 60.0, 58.0, 57.0],
      "Pledged_Percentage": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
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


df_master = load_screener_data()

# Tabs to separate Active Momentum vs Pre-Breakout Accumulation
tab1, tab2 = st.tabs(
    ["🚀 Active Breakout Candidates", "🔍 Pre-Breakout Accumulation Radar"]
)

with tab1:
  st.subheader("Active Momentum Engine (RSI + Volume Surge + ROC)")
  active_breakouts = df_master[
      (df_master["RSI"] >= rsi_min)
      & (df_master["RSI"] <= rsi_max)
      & (df_master["Volume_Surge"] == True)
      & (df_master["ROC"] > 0)
  ]
  st.info(f"Found {len(active_breakouts)} stocks matching active parameters.")
  st.dataframe(active_breakouts, use_container_width=True)

with tab2:
  st.subheader("Accumulation Radar (Catching Runners Before the Breakout)")
  accumulation_radar = df_master[
      (df_master["OBV_Trend"] == "Rising")
      & (
          df_master["Price_Consolidation_Weeks"]
          >= min_consolidation_weeks
      )
      & (df_master["Promoter_Holding"] >= min_promoter_holding)
      & (df_master["Pledged_Percentage"] == 0.0)
      & (df_master["CFO_Positive"] == True)
  ]
  st.success(
      f"Found {len(accumulation_radar)} stocks quietly accumulating under the"
      " surface."
  )
  st.dataframe(accumulation_radar, use_container_width=True)
