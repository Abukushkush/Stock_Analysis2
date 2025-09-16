import os
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from stock_analyzer import main as analyze_stock  # Make sure this folder exists in your repo

app = FastAPI(
    title="Stock Analysis API",
    version="1.0",
    description="Backend for multi-ticker stock dashboard"
)

# Allow cross-origin requests (so your frontend can call the API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/analysis")
def get_analysis(tickers: str = Query("AAPL", description="Comma-separated stock tickers")):
    """
    Returns analysis for one or more comma-separated tickers.
    Example: /analysis?tickers=AAPL,MSFT
    """
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        results = [analyze_stock(t) for t in ticker_list]
        return JSONResponse(content=results)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error processing tickers {tickers}: {str(e)}"},
            status_code=500
        )

@app.get("/health")
def health():
    """Simple health check endpoint."""
    return {"status": "ok"}

# Serve static HTML dashboard if the 'static' folder exists
if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")