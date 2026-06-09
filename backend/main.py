from fastapi import FastAPI, File, UploadFile, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import cv2
import numpy as np
from datetime import datetime

from database import engine, SessionLocal, Base, User, Scan, init_db
from ai_models import predict_lesion, process_feedback, train_feedback_sidecar, init_models

app = FastAPI(title="Melanoma AI Clinical Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and models on startup
@app.on_event("startup")
def startup_event():
    init_db()
    # Initialize the Dropbox cluster models
    init_models()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/scan")
async def scan_image(
    file: UploadFile = File(...), 
    user_id: int = Form(1),
    db: Session = Depends(get_db)
):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    image_rgb = cv2.cvtColor(image_rgb, cv2.COLOR_BGR2RGB)
    
    # 1. Save new scan to DB
    image_name = f"scan_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    
    # Predict the current image
    cleaned_image, final_prob, pred_class, breakdown = predict_lesion(image_rgb)
    
    if final_prob is None:
        return {"error": breakdown}
        
    scan = Scan(
        user_id=user_id,
        image_name=image_name,
        prediction_score=final_prob,
        final_verdict=pred_class
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    
    # 2. Fetch previous scans from Neon DB to map growth timeline (up to 7 days)
    previous_scans = db.query(Scan).filter(Scan.user_id == user_id).order_by(Scan.timestamp.asc()).limit(7).all()
    
    timeline = []
    base_score = previous_scans[0].prediction_score if previous_scans else final_prob
    
    for idx, p_scan in enumerate(previous_scans):
        # Calculate growth factor relative to day 1
        growth = (p_scan.prediction_score - base_score) * 100
        growth_str = f"+{growth:.1f}% Growth Detected" if growth > 0 else "Baseline" if idx == 0 else f"{growth:.1f}% Reduction"
        
        timeline.append({
            "day": idx + 1,
            "date": p_scan.timestamp.strftime('%b %d, %Y'),
            "verdict": p_scan.final_verdict,
            "confidence": round(p_scan.prediction_score * 100, 1),
            "growth": growth_str
        })
    
    return {
        "id": scan.id,
        "timeline": timeline,
        "current_breakdown": breakdown
    }

@app.post("/api/feedback")
async def handle_feedback(
    file: UploadFile = File(...),
    diagnosis: str = Form(...),
    image_name: str = Form(...)
):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image_rgb = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    image_rgb = cv2.cvtColor(image_rgb, cv2.COLOR_BGR2RGB)
    
    result = process_feedback(image_rgb, image_name, diagnosis)
    return {"message": result}

@app.post("/api/retrain")
async def handle_retrain():
    result = train_feedback_sidecar()
    return {"message": result}

@app.get("/api/history")
async def get_history(user_id: int = 1, db: Session = Depends(get_db)):
    scans = db.query(Scan).filter(Scan.user_id == user_id).order_by(Scan.timestamp.desc()).all()
    return scans

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
