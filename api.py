from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from stock_analyzer import main as analyze_stock

app = FastAPI(
    title="Stock Analysis API",
    version="1.0",
    description="Backend for multi-ticker stock dashboard"
)

@app.get("/analysis")
def get_analysis(tickers: str = Query("AAPL", description="Comma-separated stock tickers")):
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
    return {"status": "ok"}

# Serve static HTML dashboard
app.mount("/", StaticFiles(directory="static", html=True), name="static")