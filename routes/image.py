"""
Image Router — Image Generation API Endpoint
POST /api/image — Generate image from prompt using k2mar-mon-api-sd
Returns raw PNG bytes via StreamingResponse (avoids base64 timeout issues)
"""
import asyncio
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter()

IMAGE_API_URL = "https://k2mar-mon-api-sd.hf.space/generate"


class ImageRequest(BaseModel):
    prompt: str
    steps: int = 20


@router.post("/image")
async def generate_image(req: ImageRequest):
    """
    Proxy request to Image Generation API.
    Streams raw PNG bytes directly to the client — no base64 encoding,
    no timeout risk from holding a giant JSON payload in memory.
    """
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    if req.steps < 1 or req.steps > 100:
        raise HTTPException(status_code=400, detail="Steps must be between 1 and 100")

    try:
        # Use httpx with a long timeout (image generation takes ~5 min)
        # HuggingFace drops python-httpx user-agents, so force curl UA
        async with httpx.AsyncClient(timeout=600.0, headers={"User-Agent": "curl/7.81.0"}) as client:
            max_retries = 6  # 1 minute wait total (10s * 6)
            for attempt in range(max_retries):
                response = await client.post(
                    IMAGE_API_URL,
                    json={"prompt": req.prompt, "steps": req.steps}
                )
                
                # If API is busy, wait and try again
                if response.status_code in [503, 429]:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(10)
                        continue
                    else:
                        raise HTTPException(
                            status_code=502,
                            detail=f"L'API est actuellement très occupée. Veuillez patienter un instant et réessayer."
                        )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Image API returned {response.status_code}: {response.text[:200]}"
                    )
                
                break # Success!

        # Return PNG bytes directly — let the browser handle it
        return Response(
            content=response.content,
            media_type="image/png"
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Image generation timed out (>10 min)")
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="Could not connect to Image API")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation error: {str(e)}")
