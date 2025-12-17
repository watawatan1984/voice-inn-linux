import os
import logging
import mimetypes

try:
    from google import genai
    from google.genai import types
except ImportError:
    # Fail fast with helpful message if package is missing
    raise ImportError("The 'google-genai' package is required. Please install it via pip or uv.")

from src.core.config import config_manager
from src.ai.providers.base import AIProvider

class GeminiProvider(AIProvider):
    def __init__(self):
        self.api_key = config_manager.settings.get("gemini_key") or os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                logging.exception("Error configuring Gemini Client")

    def transcribe(self, audio_path: str, prompts: dict) -> str:
        if not self.client:
             raise RuntimeError("Gemini Client not initialized (Check API Key)")

        model_name = config_manager.settings.get("gemini_model") or os.getenv("GEMINI_MODEL") or "gemini-2.0-flash" 
        
        prompt_text = prompts.get("gemini_transcribe_prompt", "")

        try:
            mime_type, _ = mimetypes.guess_type(audio_path)
            if not mime_type or not mime_type.startswith("audio/"):
                mime_type = "audio/wav"

            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
                
            # New SDK usage (v1/v0.x of google-genai)
            # client.models.generate_content
            response = self.client.models.generate_content(
                model=model_name,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                            types.Part.from_text(text=prompt_text)
                        ]
                    )
                ],
                config=types.GenerateContentConfig(temperature=0.0)
            )
            
            if response.text:
                return response.text.strip()
            return ""
            
        except Exception:
            logging.exception("Gemini Transcription Error")
            raise
