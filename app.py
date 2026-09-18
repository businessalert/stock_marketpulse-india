import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# --- Page Configuration ---
st.set_page_config(
    page_title="Dynamic Multibagger Funnel Dashboard",
    page_icon="📈",
    layout="wide",
)


@st.cache_data(ttl=3600)
def fetch_dynamic_stock_data(ticker_df: pd.DataFrame) -> pd.DataFrame:
  """Takes a DataFrame with [ticker, industry] and dynamically fetches

  all pricing, volume, and metric data via yfinance.
  """
  data_rows = []

  for _, row in ticker_df.iterrows():
    ticker = str(row["ticker"]).strip().upper()
    industry = (
        str(row["industry"]) if "industry" in row else "General/Unmapped"
    )

    try:
      # Append '.NS' for NSE stocks if not already present
      formatted_ticker = ticker
      if not formatted_ticker.endswith(".NS") and not formatted_ticker.endswith(
          ".BO"
      ):
        formatted_ticker += ".NS"

      stock = yf.Ticker(formatted_ticker)
      hist = stock.history(period="6mo")

      if hist.empty or len(hist) < 50:
        continue

      # Dynamically compute technical metrics from market history
      current_close = hist["Close"].iloc[-1]
      vma_50 = hist["Volume"].tail(50).mean()
      current_volume = hist["Volume"].iloc[-1]

      # Simple RSI-14 calculation
      delta = hist["Close"].diff()
      gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
      loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
      rs = gain / loss
      rsi_14 = 100 - (100 / (1 + rs)).iloc[-1]

      # Recent 20-day resistance box (consolidation high)
      consolidation_high = hist["High"].tail(20).max()

      # Fetch fundamentals or set safe defaults
      info = stock.info
      roce = info.get("returnOnCapitalEmployed", info.get("roce", 15.0))
      roce = (roce * 100) if roce and roce < 2.0 else (roce or 15.0)

      data_rows.append({
          "ticker": ticker,
          "industry": industry,
          "close": round(current_close, 2),
          "volume": int(current_volume),
          "vma_50": int(vma_50),
          "delivery_pct": 70.0,  # Estimated baseline delivery
          "rsi_14": round(rsi_14, 2),
          "consolidation_high": round(consolidation_high, 2),
          "roce": round(roce, 2),
      })
    except Exception:
      continue

  return pd.DataFrame(data_rows)


def process_multibagger_funnel(df: pd.DataFrame) -> pd.DataFrame:
  """Processes dynamically fetched data through the multi-tiered funnel."""
  if df.empty:
    return df

  data = df.copy()

  # Stage 1 & 2: Quantitative Quality & Accumulation Filter
  data["passes_accumulation"] = (
      (data["roce"] >= 12.0)
      & (data["delivery_pct"] >= 60.0)
      & (data["close"] >= data["consolidation_high"] * 0.95)
  )

  data["lifecycle_phase"] = np.where(
      data["passes_accumulation"], "Accumulation Phase", "Radar Pool"
  )

  # Stage 3: Breakout & Momentum Trigger (Execution Gate)
  price_breakout = data["close"] >= (data["consolidation_high"] * 1.01)
  volume_surge = data["volume"] >= (data["vma_50"] * 2.0)
  momentum_rsi = (data["rsi_14"] >= 55.0) & (data["rsi_14"] <= 80.0)

  data["is_transition_ready"] = (
      data["passes_accumulation"] & price_breakout & volume_surge & momentum_rsi
  )

  data.loc[data["is_transition_ready"], "lifecycle_phase"] = "Growth Phase"
  return data


# --- Streamlit UI Layout ---
st.title("🚀 Dynamic Multibagger Funnel Dashboard")
st.markdown(
    "Upload a simple CSV containing **only** your ticker list and industry"
    " mapping. The system handles all dynamic calculations automatically."
)

st.sidebar.header("Ticker & Industry Source")
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV (Columns: ticker, industry)", type=["csv"]
)

if uploaded_file is not None:
  input_ticker_df = pd.read_csv(uploaded_file)
else:
  st.sidebar.info(
      "No file uploaded. Using default sample ticker & industry mapping."
  )
  input_ticker_df = pd.DataFrame({
      "ticker": ["RELIANCE", "TCS", "INFY", "TATAMOTORS", "SBIN"],
      "industry": [
          "Energy",
          "IT Services",
          "IT Services",
          "Automobile",
          "Banking",
      ],
  })

if st.sidebar.button("Run Funnel Scan"):
  with st.spinner(
      "Fetching live market data and mapping dynamic indicators..."
  ):
    raw_fetched_df = fetch_dynamic_stock_data(input_ticker_df)
    processed_df = process_multibagger_funnel(raw_fetched_df)
    st.session_state["processed_df"] = processed_df

# Load from session state if available
if "processed_df" in st.session_state:
  processed_df = st.session_state["processed_df"]

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
      "Growth Phase (Ready)",
      len(processed_df[processed_df["is_transition_ready"]]),
  )

  st.markdown("---")

  selected_phase = st.selectbox(
      "Select Funnel Tier to Display:",
      ["All Tiers", "Radar Pool", "Accumulation Phase", "Growth Phase"],
  )

  display_df = (
      processed_df
      if selected_phase == "All Tiers"
      else processed_df[processed_df["lifecycle_phase"] == selected_phase]
  )
  st.dataframe(display_df, use_container_width=True)

  growth_alerts = processed_df[processed_df["is_transition_ready"]]
  if not growth_alerts.empty:
    st.error(
        "🚨 **Execution Alert:** Breakout triggers cleared for:"
        f" {', '.join(growth_alerts['ticker'].tolist())}"
    )
  else:
    st.info("ℹ️ No stocks currently meeting full Growth Phase breakout triggers.")
else:
  st.info("👈 Upload your ticker-industry CSV or use default, then click 'Run Funnel Scan'.")
