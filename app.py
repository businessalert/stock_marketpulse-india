import glob
import pandas as pd
import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Multibagger Funnel Dashboard", page_icon="📈", layout="wide"
)


@st.cache_data
def load_data():
  csv_files = glob.glob("*.csv")
  if not csv_files:
    return None
  df = pd.read_csv(csv_files[0])
  df.columns = df.columns.str.strip().str.lower()
  if "symbol" in df.columns and "ticker" not in df.columns:
    df.rename(columns={"symbol": "ticker"}, inplace=True)
  if "sector" in df.columns and "industry" not in df.columns:
    df.rename(columns={"sector": "industry"}, inplace=True)
  return df


st.title("🚀 Multibagger Funnel Dashboard")
st.markdown("Institutional screening engine for your stock universe.")

df = load_data()

if df is not None:
  st.success(f"📂 Successfully loaded **{len(df)}** stocks from repository.")

  # Quick metrics & filters
  col1, col2 = st.columns(2)
  col1.metric("Total Universe", len(df))

  if "industry" in df.columns:
    industries = ["All Industries"] + list(df["industry"].dropna().unique())
    selected_industry = st.selectbox("Filter by Industry / Sector:", industries)
    if selected_industry != "All Industries":
      df = df[df["industry"] == selected_industry]
      col2.metric("Filtered Universe", len(df))
    else:
      col2.metric("Filtered Universe", len(df))

  st.markdown("---")
  st.dataframe(df, use_container_width=True)
else:
  st.error(
      "❌ No CSV file found in the repository. Please check your file name."
  )
