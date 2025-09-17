from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

app = FastAPI()

# Allow CORS for all origins (you can restrict to your Base44 domain later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check for API key
@app.get("/check_key")
def check_key():
    key = os.getenv("TWELVEDATA_API_KEY")
    return {
        "key_loaded": bool(key),
        "key_length": len(key) if key else 0
    }

# Example endpoint to fetch stock data from Twelve Data
@app.get("/stock")
def get_stock(symbol: str = Query(..., description="Stock ticker symbol, e.g., AAPL")):
    api_key = os.getenv("TWELVEDATA_API_KEY")
    if not api_key:
        return {"error": "Twelve Data API key not found in environment variables."}

    url = f"https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": "1min",
        "apikey": api_key
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Root endpoint
@app.get("/")
def root():
    return {"message": "Stock Analysis API is running"}