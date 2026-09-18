import numpy as np
import pandas as pd
import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Multibagger Funnel Dashboard", page_icon="📈", layout="wide"
)


# --- Core Pipeline Logic ---
def process_multibagger_funnel(df: pd.DataFrame) -> pd.DataFrame:
  """Processes raw stock market data through the multi-tiered funnel approach."""
  data = df.copy()

  # Stage 1 & 2: Quantitative Quality & Accumulation Filter
  roce_threshold = 15.0
  delivery_threshold = 65.0

  data["passes_accumulation"] = (
      (data["roce"] >= roce_threshold)
      & (data["delivery_pct"] >= delivery_threshold)
      & (data["close"] >= data["consolidation_high"] * 0.95)
  )

  data["lifecycle_phase"] = np.where(
      data["passes_accumulation"], "Accumulation Phase", "Radar Pool"
  )

  # Stage 3: Breakout & Momentum Trigger (Execution Gate)
  price_breakout = data["close"] >= (data["consolidation_high"] * 1.015)
  volume_surge = data["volume"] >= (data["vma_50"] * 3.0)
  momentum_rsi = (data["rsi_14"] >= 60.0) & (data["rsi_14"] <= 75.0)

  data["is_transition_ready"] = (
      data["passes_accumulation"] & price_breakout & volume_surge & momentum_rsi
  )

  data.loc[data["is_transition_ready"], "lifecycle_phase"] = "Growth Phase"

  return data


# --- Streamlit UI Layout ---
st.title("🚀 Multibagger Funnel & Lifecycle Dashboard")
st.markdown(
    "Automated pipeline filtering raw market data into high-conviction"
    " Accumulation and Growth phases."
)

# Sidebar for controls and file upload simulation
st.sidebar.header("Pipeline Controls")
uploaded_file = st.sidebar.file_uploader(
    "Upload Market Data (CSV)", type=["csv"]
)

# Use mock data if no file is uploaded
if uploaded_file is not None:
  raw_df = pd.read_csv(uploaded_file)
else:
  st.sidebar.info("Using sample mock dataset for demonstration.")
  raw_df = pd.DataFrame({
      "ticker": ["STOCK_A", "STOCK_B", "STOCK_C", "STOCK_D"],
      "close": [105.0, 45.0, 210.0, 88.0],
      "high": [106.0, 46.0, 212.0, 90.0],
      "low": [101.0, 44.0, 205.0, 85.0],
      "volume": [3500000, 900000, 4500000, 2800000],
      "vma_50": [1000000, 800000, 1200000, 950000],
      "delivery_pct": [72.5, 55.0, 68.0, 66.0],
      "rsi_14": [64.5, 48.0, 71.2, 58.0],
      "consolidation_high": [103.0, 47.0, 200.0, 85.0],
      "roce": [18.5, 12.0, 22.0, 16.0],
  })

# Process data through the funnel
processed_df = process_multibagger_funnel(raw_df)

# --- Metric Summary Cards ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Universe Scanned", len(processed_df))
col2.metric(
    "Accumulation Phase",
    len(
        processed_df[
            processed_df["lifecycle_phase"] == "Accumulation Phase"
        ]
    ),
)
col3.metric(
    "Growth Phase (Ready)", len(processed_df[processed_df["is_transition_ready"]])
)

st.markdown("---")

# --- Interactive Filter View ---
st.subheader("Lifecycle Phase Filter")
selected_phase = st.selectbox(
    "Select Funnel Tier to Display:",
    ["All Tiers", "Radar Pool", "Accumulation Phase", "Growth Phase"],
)

if selected_phase != "All Tiers":
  display_df = processed_df[processed_df["lifecycle_phase"] == selected_phase]
else:
  display_df = processed_df

# --- Data Table Presentation ---
st.dataframe(display_df, use_container_width=True)

# Highlight immediate trade execution alerts
growth_alerts = processed_df[processed_df["is_transition_ready"]]
if not growth_alerts.empty:
  st.error(
      "🚨 **Execution Alert:** The following tickers have cleared Stage 3"
      f" breakout triggers: {', '.join(growth_alerts['ticker'].tolist())}"
  )
else:
  st.info("ℹ️ No stocks currently meeting full Growth Phase breakout triggers.")
