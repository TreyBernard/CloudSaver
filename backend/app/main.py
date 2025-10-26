# app/main.py
import os
import logging
import traceback
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.analyzer import analyze_billing_csv 
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("app.main")
logging.basicConfig(level=logging.INFO)
app = FastAPI(title="CloudSaver Cost Advisor")

origins = [
    "http://localhost",
    "http://localhost:5173", 
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Cloud Cost Analyzer Backend is running."}

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")
    try:
        content = await file.read()
        csv_text = content.decode("utf-8", errors="replace") 
        logger.info(f"Received file: {file.filename}")
        result = await analyze_billing_csv(csv_text)
        return result
    
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Analysis failed: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
