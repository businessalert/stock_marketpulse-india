import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# Exact Wilder's RSI matching TradingView / Zerodha charting standards
def compute_zerodha_style_rsi(series, period=14):
  delta = series.diff()
  gain = delta.clip(lower=0)
  loss = -1 * delta.clip(upper=0)

  # Wilder's smoothing using ewm with adjust=False
  avg_gain = gain.ewm(
      alpha=1 / period, min_periods=period, adjust=False
  ).mean()
  avg_loss = loss.ewm(
      alpha=1 / period, min_periods=period, adjust=False
  ).mean()

  rs = avg_gain / avg_loss
  return 100 - (100 / (1 + rs))


def compute_roc(series, period=18):
  return ((series - series.shift(period)) / series.shift(period)) * 100
