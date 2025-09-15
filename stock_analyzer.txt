import os
import requests
import pandas as pd
import pandas_ta as ta

API_KEY = os.getenv("TWELVEDATA_API_KEY")
BASE_URL = "https://api.twelvedata.com"

def _safe_float(x, default=None):
    if x is None:
        return default
    try:
        s = str(x).replace("%", "").replace(",", "").strip()
        return float(s)
    except Exception:
        return default

def _safe_int(x, default=None):
    if x is None:
        return default
    try:
        s = str(x).replace(",", "").strip()
        return int(float(s))
    except Exception:
        return default

def _last_valid(series):
    # Return the last non-NaN value in a pandas Series, or None
    try:
        val = series.dropna().iloc[-1]
        return float(val)
    except Exception:
        return None

def main(ticker: str):
    if not API_KEY:
        raise ValueError("TWELVEDATA_API_KEY not set in environment.")

    ticker = ticker.upper()

    # --- 1) Quote data (price, volume, market cap, percent change) ---
    quote_url = f"{BASE_URL}/quote"
    quote_params = {"symbol": ticker, "apikey": API_KEY}
    quote_data = requests.get(quote_url, params=quote_params).json()

    if isinstance(quote_data, dict) and quote_data.get("status") == "error":
        raise ValueError(f"Error fetching quote for {ticker}: {quote_data}")

    # --- 2) Time series for indicators ---
    ts_url = f"{BASE_URL}/time_series"
    ts_params = {
        "symbol": ticker,
        "interval": "1day",
        "outputsize": 200,
        "apikey": API_KEY
    }
    ts_data = requests.get(ts_url, params=ts_params).json()
    if "values" not in ts_data:
        raise ValueError(f"Error fetching time series for {ticker}: {ts_data}")

    df = pd.DataFrame(ts_data["values"])
    # Ensure required columns exist and are numeric
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            raise ValueError(f"Time series missing required column '{col}' for {ticker}")
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    # volume from Twelve Data often comes as string
    try:
        df["volume"] = df["volume"].astype(float)
    except Exception:
        df["volume"] = df["volume"].apply(_safe_float)

    df = df[::-1].reset_index(drop=True)  # oldest first

    # --- 3) Technical indicators ---
    df["sma_20"] = ta.sma(df["close"], length=20)
    df["rsi_14"] = ta.rsi(df["close"], length=14)
    macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)  # returns multiple columns
    adx_df = ta.adx(high=df["high"], low=df["low"], close=df["close"], length=14)

    # Extract last values safely
    last_close = float(df["close"].iloc[-1])
    sma_20 = _last_valid(df["sma_20"])
    rsi_14 = _last_valid(df["rsi_14"])
    macd_val = None
    if isinstance(macd_df, pd.DataFrame) and "MACD_12_26_9" in macd_df.columns:
        macd_val = _last_valid(macd_df["MACD_12_26_9"])
    adx_val = None
    if isinstance(adx_df, pd.DataFrame) and "ADX_14" in adx_df.columns:
        adx_val = _last_valid(adx_df["ADX_14"])

    # --- 4) Trend & signal logic (simple, deterministic) ---
    trend = None
    signal = None
    if sma_20 is not None:
        trend = "Up" if last_close > sma_20 else "Down"
        # Narrow band for HOLD to reduce churn; tweak threshold as you like
        threshold = max(0.0025 * last_close, 0.25)  # 0.25% of price or $0.25 minimum
        if abs(last_close - sma_20) <= threshold:
            signal = "HOLD"
        else:
            signal = "BUY" if last_close > sma_20 else "SELL"

    # --- 5) Quote parsing with safe conversions ---
    company_name = quote_data.get("name") or quote_data.get("symbol") or ticker
    price_from_quote = _safe_float(quote_data.get("close"))
    change_percent = _safe_float(quote_data.get("percent_change"))
    volume = _safe_int(quote_data.get("volume"))
    market_cap = quote_data.get("market_cap")  # keep as provided (often already formatted)

    # Fallbacks if quote is missing pieces
    final_price = price_from_quote if price_from_quote is not None else last_close

    return {
        "company": company_name,
        "price": final_price,
        "sma_20": sma_20,
        "rsi": rsi_14,
        "signal": signal,
        "change_percent": change_percent,
        "volume": volume,
        "market_cap": market_cap,
        "macd": macd_val,
        "adx": adx_val,
        "trend": trend
    }