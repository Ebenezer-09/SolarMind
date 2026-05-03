"""
Image Router — Image Generation API Endpoint
POST /api/image — Generate image from prompt
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.api_client import ImageClient

router = APIRouter()


class ImageRequest(BaseModel):
    prompt: str
    guidance_scale: float = 8.5
    num_inference_steps: int = 25


class ImageResponse(BaseModel):
    image: str


@router.post("/image", response_model=ImageResponse)
async def generate_image(req: ImageRequest):
    """
    Proxy request to Image Generation API
    Returns base64 encoded image or data URI
    """
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    # Validate parameters
    if req.guidance_scale < 1 or req.guidance_scale > 20:
        raise HTTPException(status_code=400, detail="Guidance scale must be between 1 and 20")
    
    if req.num_inference_steps < 10 or req.num_inference_steps > 50:
        raise HTTPException(status_code=400, detail="Inference steps must be between 10 and 50")
    
    result = ImageClient.generate(
        req.prompt,
        req.guidance_scale,
        req.num_inference_steps
    )
    
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    
    if "image" not in result:
        raise HTTPException(status_code=502, detail="No image in API response")
    
    return ImageResponse(image=result["image"])
