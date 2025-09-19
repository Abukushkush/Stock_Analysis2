import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from stock_analyzer import main as analyze_stock

app = FastAPI(
    title="Stock Analysis Dashboard API", # Changed title to reflect API focus
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now, for easier testing. Consider tightening in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Removed the @app.get("/", response_class=HTMLResponse) endpoint
# This simplifies the API and focuses it on data, reducing potential conflicts.

@app.get("/analysis")
def analysis_endpoint(ticker: str = Query(..., min_length=1, max_length=10)):
    # Call the main analysis function
    analysis_result = analyze_stock(ticker)

    # If the analysis_result contains an error status, return an HTTPException
    if analysis_result.get("status") == "error":
        # Raise an HTTPException with a 400 Bad Request or 500 Internal Server Error
        # depending on the nature of the error
        if "TWELVEDATA_API_KEY" in analysis_result["message"] or "network error" in analysis_result["message"].lower():
            raise HTTPException(status_code=500, detail=analysis_result["message"])
        else:
            raise HTTPException(status_code=400, detail=analysis_result["message"])

    # Otherwise, return the successful analysis result
    return JSONResponse(content=analysis_result)
