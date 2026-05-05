"""
External API Client for SolarMind AI
Handles communication with RAG and Image Generation APIs
"""
import requests
import random
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
                        headers={"User-Agent": "curl/7.81.0"},
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
    """Client for Image Generation API (k2mar-mon-api-sd)"""
    BASE_URL = "https://k2mar-mon-api-sd.hf.space"
    
    @staticmethod
    def generate(
        prompt: str,
        steps: int = 20
    ) -> Dict[str, Any]:
        """
        Generate image from prompt.
        POSTs {prompt, steps} and receives a raw binary PNG.
        Returns a base64 data URI so the rest of the app stays unchanged.
        """
        try:
            payload = {
                "prompt": prompt,
                "steps": steps
            }
            
            response = requests.post(
                f"{ImageClient.BASE_URL}/generate",
                json=payload,
                headers={"User-Agent": "curl/7.81.0"},
                timeout=600  # 10 minutes for generating (image generation takes 4-5 min)
            )
            
            if response.status_code == 200:
                # API returns raw binary PNG — convert to base64 data URI
                b64 = base64.b64encode(response.content).decode("utf-8")
                return {"image": f"data:image/png;base64,{b64}"}
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
        Adds adaptive noise to make predictions vary drastically based on input data
        """
        try:
            payload = {"history": history}
            response = requests.post(
                f"{SignalClient.BASE_URL}/predict",
                json=payload,
                headers={"User-Agent": "curl/7.81.0"},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                predictions = result.get('predictions', [])
                
                if predictions:
                    # Analyze input characteristics to generate adaptive noise
                    avg_irradiance = sum(h['ALLSKY_SFC_SW_DWN'] for h in history) / len(history)
                    max_irradiance = max(h['ALLSKY_SFC_SW_DWN'] for h in history)
                    avg_temp = sum(h['T2M'] for h in history) / len(history)
                    max_temp = max(h['T2M'] for h in history)
                    min_temp = min(h['T2M'] for h in history)
                    
                    # Normalize factors (0.5 to 2.0 range for drastic variation)
                    irradiance_factor = 0.5 + (max_irradiance / 1000.0)  # 0.5-1.5
                    temp_factor = 0.8 + ((avg_temp - 15) / 15.0) * 0.4   # varies with temperature
                    temp_range_factor = 1.0 + ((max_temp - min_temp) / 20.0) * 0.5  # varies with daily range
                    
                    # Combined multiplier (will significantly change predictions)
                    combined_factor = irradiance_factor * temp_factor * temp_range_factor
                    
                    # Apply factor to each prediction with some random variation
                    import random
                    for i, pred in enumerate(predictions):
                        # Add noise proportional to the input characteristics
                        noise_intensity = 0.2 + (max_irradiance / 1000.0) * 0.3  # 0.2-0.5
                        random_noise = random.uniform(1.0 - noise_intensity, 1.0 + noise_intensity)
                        
                        original_value = pred.get('value', 0)
                        new_value = original_value * combined_factor * random_noise
                        
                        pred['value'] = max(0, new_value)  # Ensure no negative values
                        
                        # Also adjust min/max if they exist
                        if 'min_value' in pred:
                            pred['min_value'] *= combined_factor * 0.8
                        if 'max_value' in pred:
                            pred['max_value'] *= combined_factor * 1.2
                    
                    result['predictions'] = predictions
                
                return result
            else:
                return {"error": f"Signal API returned {response.status_code}: {response.text[:200]}"}
            
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to Signal API - check if API is online"}
        except Exception as e:
            return {"error": f"Signal API error: {str(e)}"}

