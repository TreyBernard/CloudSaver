# app/main.py (trimmed for production/dev, no debug prints)
import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.analyzer import analyze_billing_csv
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("app.main")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="CloudSaver Cost Advisor")

# Allow local dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")
    
    content = await file.read()
    csv_text = content.decode("utf-8", errors="replace")

    try:
        result = analyze_billing_csv(csv_text)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.exception("Analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
