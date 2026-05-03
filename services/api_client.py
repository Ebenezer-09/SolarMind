"""
External API Client for SolarMind AI
Handles communication with RAG and Image Generation APIs
"""
import requests
from typing import Dict, Any, List
import base64


class RAGClient:
    """Client for Smart Energy RAG API"""
    BASE_URL = "https://freddyouedraogo-smart-energy-api.hf.space"
    
    @staticmethod
    def chat(message: str) -> Dict[str, Any]:
        """
        Send message to RAG API
        Supports multiple format attempts for HuggingFace endpoints
        """
        try:
            # Try multiple formats to support different HF API versions
            formats = [
                {"question": message}, # Format exact demandé par l'API externe actuelle
                {"message": message},  # Original format
                {"inputs": message},   # Standard HF format
                {"prompt": message},   # Alternative format
                {"text": message},     # Alternative format
            ]
            
            for payload in formats:
                try:
                    response = requests.post(
                        f"{RAGClient.BASE_URL}/chat",
                        json=payload,
                        timeout=120  # 2 minutes — HF spaces can cold-start
                    )
                    if response.status_code == 200:
                        return response.json()
                except Exception:
                    continue
            
            # If all formats fail, try the last response
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            return {"error": "RAG API timeout - taking too long to respond"}
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to RAG API - check if API is online"}
        except Exception as e:
            return {"error": f"RAG API error: {str(e)}"}


class ImageClient:
    """Client for Image Generation API"""
    BASE_URL = "https://Soso26-generator-api.hf.space"
    
    @staticmethod
    def generate(
        prompt: str,
        guidance_scale: float = 8.5,
        num_inference_steps: int = 25
    ) -> Dict[str, Any]:
        """
        Generate image from prompt
        Returns base64 encoded image or data URI
        """
        try:
            # Include all parameters in the request
            params = {
                "prompt": prompt,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_inference_steps
            }
            
            response = requests.get(
                f"{ImageClient.BASE_URL}/generate",
                params=params,
                timeout=None  # No timeout — image generation can take several minutes
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # If image is not a data URI, convert base64 if needed
                if "image" in data:
                    img_data = data["image"]
                    if not img_data.startswith("data:"):
                        # Assume it's base64, convert to data URI
                        data["image"] = f"data:image/png;base64,{img_data}"
                
                return data
            else:
                return {"error": f"Image API returned {response.status_code}: {response.text[:200]}"}
            
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to Image API - check if API is online"}
        except Exception as e:
            return {"error": f"Image generation error: {str(e)}"}


class SignalClient:
    """Client for AI Signal Prediction API"""
    BASE_URL = "https://freddyouedraogo-modele-signal-ia.hf.space"
    
    @staticmethod
    def predict(history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get predictions based on history of 24 points
        """
        try:
            payload = {"history": history}
            response = requests.post(
                f"{SignalClient.BASE_URL}/predict",
                json=payload,
                timeout=None  # No timeout — model inference can be slow
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Signal API returned {response.status_code}: {response.text[:200]}"}
            
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to Signal API - check if API is online"}
        except Exception as e:
            return {"error": f"Signal API error: {str(e)}"}

