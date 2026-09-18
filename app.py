import glob
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# --- Page Configuration ---
st.set_page_config(
    page_title="Multibagger Funnel Dashboard", page_icon="📈", layout="wide"
)


@st.cache_data
def load_master_directory():
  """Loads ONLY ticker and industry mapping from the repository CSV."""
  csv_files = glob.glob("*.csv")
  if not csv_files:
    return None
  df = pd.read_csv(csv_files[0])
  df.columns = df.columns.str.strip().str.lower()

  if "symbol" in df.columns and "ticker" not in df.columns:
    df.rename(columns={"symbol": "ticker"}, inplace=True)
  if "sector" in df.columns and "industry" not in df.columns:
    df.rename(columns={"sector": "industry"}, inplace=True)

  # Keep only clean ticker and industry columns as the master directory
  if "ticker" in df.columns:
    master_df = df[["ticker", "industry"]].copy()
    master_df["ticker"] = master_df["ticker"].str.strip().str.upper()
    master_df["industry"] = (
        master_df["industry"].fillna("General").str.strip()
    )
    return master_df.drop_duplicates(subset=["ticker"])
  return None


@st.cache_data(ttl=1800)
def fetch_live_stock_triggers(ticker: str) -> dict:
  """Dynamically fetches live pricing, volume, RSI, and fundamental triggers for a given ticker."""
  try:
    formatted_ticker = ticker
    if not formatted_ticker.endswith(".NS") and not formatted_ticker.endswith(
        ".BO"
    ):
      formatted_ticker += ".NS"

    stock = yf.Ticker(formatted_ticker)
    hist = stock.history(period="6mo")

    if hist.empty or len(hist) < 30:
      return None

    current_close = float(hist["Close"].iloc[-1])
    current_volume = int(hist["Volume"].iloc[-1])
    vma_50 = (
        int(hist["Volume"].tail(50).mean())
        if len(hist) >= 50
        else int(hist["Volume"].mean())
    )

    # 14-day RSI calculation
    delta = hist["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi_val = 100 - (100 / (1 + rs))
    rsi_14 = float(rsi_val.iloc[-1]) if not rsi_val.empty else 50.0

    consolidation_high = float(
        hist["High"].tail(20).max() if len(hist) >= 20 else hist["High"].max()
    )

    # Fundamental fetch (ROCE / Info)
    info = stock.info
    roce = info.get("returnOnCapitalEmployed", info.get("roce", 15.0))
    if roce is not None and roce < 2.0:
      roce = roce * 100

    # Funnel Trigger Logic
    passes_accumulation = (
        roce >= 12.0 and current_close >= consolidation_high * 0.90
    )
    price_breakout = current_close >= (consolidation_high * 1.005)
    volume_surge = current_volume >= (vma_50 * 1.5)
    momentum_rsi = 50.0 <= rsi_14 <= 85.0

    is_growth_ready = (
        passes_accumulation and price_breakout and volume_surge and momentum_rsi
    )

    return {
        "ticker": ticker,
        "close": round(current_close, 2),
        "volume": current_volume,
        "vma_50": vma_50,
        "rsi_14": round(rsi_14, 2),
        "consolidation_high": round(consolidation_high, 2),
        "roce": round(roce, 2),
        "phase": (
            "Growth Phase (Breakout)"
            if is_growth_ready
            else ("Accumulation Phase" if passes_accumulation else "Radar Pool")
        ),
    }
  except Exception:
    return None


# --- UI Layout ---
st.title("🚀 Dynamic Multibagger Funnel Dashboard")
st.markdown(
    "Master directory loaded from repository CSV. Live triggers computed via"
    " live market data."
)

master_df = load_master_directory()

if master_df is not None:
  st.sidebar.success(
      f"📂 Master Directory Loaded: {len(master_df)} tickers from CSV."
  )

  # Industry filter
  industries = ["All Industries"] + sorted(
      master_df["industry"].unique().tolist()
  )
  selected_industry = st.sidebar.selectbox("Filter by Industry:", industries)

  filtered_master = master_df
  if selected_industry != "All Industries":
    filtered_master = master_df[master_df["industry"] == selected_industry]

  st.metric("Filtered Universe Count", len(filtered_master))

  # Selection for deep live scan
  st.markdown("### Select Tickers for Live Trigger Scan")
  selected_tickers = st.multiselect(
      "Choose stocks to evaluate live (or pick from filtered list):",
      filtered_master["ticker"].tolist(),
      default=filtered_master["ticker"].tolist()[:5],
  )

  if st.button("Run Live Trigger Analysis on Selected Tickers"):
    if not selected_tickers:
      st.warning("Please select at least one ticker.")
    else:
      results = []
      progress = st.progress(0)
      for i, tkr in enumerate(selected_tickers):
        progress.progress(
            (i + 1) / len(selected_tickers),
            text=f"Fetching live metrics for {tkr}...",
        )
        res = fetch_live_stock_triggers(tkr)
        if res:
          # Merge industry info
          ind_row = filtered_master[filtered_master["ticker"] == tkr]
          res["industry"] = (
              ind_row["industry"].values[0]
              if not ind_row.empty
              else "General"
          )
          results.append(res)
      progress.empty()

      if results:
        res_df = pd.DataFrame(results)
        st.success(
            f"Successfully evaluated {len(res_df)} stocks with live data."
        )
        st.dataframe(res_df, use_container_width=True)
      else:
        st.error("Could not fetch live data for the selected tickers.")
else:
  st.error("❌ Repository CSV not found.")
