import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.analyzer import analyze_billing_csv
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="CloudSaver Cost Advisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Invalid file type. Please upload a CSV file.")

    content = await file.read()
    csv_text = content.decode("utf-8", errors="replace")

    try:
        result = analyze_billing_csv(csv_text)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("Error processing CSV:\n", tb)
        raise HTTPException(500, f"Analysis failed: {e}")

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
