"""
Smart Assistant Router — Auto-routing between RAG, Image, and Signal APIs
POST /api/assistant — Smart router that detects content type
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from services.api_client import RAGClient, ImageClient, SignalClient
import datetime

router = APIRouter()


class AssistantRequest(BaseModel):
    message: str


class AssistantResponse(BaseModel):
    type: str  # "text", "image", or "signal"
    response: Optional[str] = None
    message: Optional[str] = None
    image: Optional[str] = None
    predictions: Optional[List[Any]] = None
    unit: Optional[str] = None


# Keywords that trigger image generation
IMAGE_KEYWORDS = [
    'image', 'draw', 'diagram', 'schema', 'generate', 'illustrate',
    'picture', 'photo', 'sketch', 'visual', 'render',
    'create image', 'make image', 'show image', 'design', 'blueprint'
]

# Keywords that trigger signal prediction
SIGNAL_KEYWORDS = [
    'predict', 'forecast', 'signal', 'production', 'prédiction',
    'prévision', 'courbe', 'prediction', 'prédire', 'prévoir',
    'energy forecast', 'solar forecast', 'generation forecast',
    'puissance', 'kilowatt', 'kw'
]


def detect_image_request(message: str) -> bool:
    lower_msg = message.lower()
    return any(keyword in lower_msg for keyword in IMAGE_KEYWORDS)


def detect_signal_request(message: str) -> bool:
    lower_msg = message.lower()
    return any(keyword in lower_msg for keyword in SIGNAL_KEYWORDS)


def generate_mock_history():
    """Generate 24 hours of simulated weather history for prediction"""
    history = []
    now = datetime.datetime.now()
    for i in range(24):
        d = now - datetime.timedelta(hours=24 - i)
        hour = d.hour
        is_day = 6 < hour < 18
        radiation = (500.0 + (hour - 6) * 50) if is_day else 0.0
        temp = 25.0 + (5.0 if is_day else -3.0)
        history.append({
            "datetime": d.strftime("%Y-%m-%dT%H:%M:%S"),
            "ALLSKY_SFC_SW_DWN": radiation,
            "T2M": temp
        })
    return history


@router.post("/assistant", response_model=AssistantResponse)
async def smart_assistant(req: AssistantRequest):
    """
    Smart auto-router:
    - If message contains signal keywords → call Signal API
    - If message contains image keywords → call Image API
    - Otherwise → call RAG API for text response
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Check signal first (more specific), then image, then default to RAG
    if detect_signal_request(req.message):
        history = generate_mock_history()
        result = SignalClient.predict(history)

        if "error" in result:
            raise HTTPException(status_code=502, detail=result["error"])

        return AssistantResponse(
            type="signal",
            predictions=result.get("predictions", []),
            unit=result.get("unit", "kilowatts"),
            response="Voici la prédiction de production solaire pour les prochaines 24 heures."
        )

    elif detect_image_request(req.message):
        result = ImageClient.generate(req.message)

        if "error" in result:
            raise HTTPException(status_code=502, detail=result["error"])

        if "image" not in result:
            raise HTTPException(status_code=502, detail="No image generated")

        return AssistantResponse(
            type="image",
            image=result["image"]
        )

    else:
        result = RAGClient.chat(req.message)

        if "error" in result:
            raise HTTPException(status_code=502, detail=result["error"])

        response_text = result.get("response") or result.get("message") or str(result)

        return AssistantResponse(
            type="text",
            response=response_text,
            message=response_text
        )
