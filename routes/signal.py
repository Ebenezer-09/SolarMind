"""
Signal Router — AI Prediction API Endpoint
POST /api/signal/predict — Send data points to predict
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from services.api_client import SignalClient

router = APIRouter()


class DataPoint(BaseModel):
    datetime: str
    ALLSKY_SFC_SW_DWN: float
    T2M: float


class PredictRequest(BaseModel):
    history: List[DataPoint]


@router.post("/signal/predict")
async def predict_signal(req: PredictRequest):
    """
    Proxy request to AI Signal Prediction API
    """
    if len(req.history) != 24:
        raise HTTPException(status_code=400, detail="History must contain exactly 24 points.")
    
    # Convert list of DataPoint models to list of dicts directly
    history_dicts = [item.dict() for item in req.history]
    
    result = SignalClient.predict(history_dicts)
    
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    
    # Validation error from FastAPI is handled automatically if the type mismatch
    # Validation error from remote HF API is handled here if 502 occurs (or error key)
    
    return result
