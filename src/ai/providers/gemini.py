import os
import google.generativeai as genai
import logging
from src.core.config import config_manager
from src.ai.providers.base import AIProvider

class GeminiProvider(AIProvider):
    def __init__(self):
        self.api_key = config_manager.settings.get("gemini_key") or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
            except Exception as e:
                print(f"Error configuring Gemini: {e}")

    def transcribe(self, audio_path: str, prompts: dict) -> str:
        if not self.api_key:
             raise RuntimeError("Gemini API Key missing")

        model_name = config_manager.settings.get("gemini_model") or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        prompt = prompts.get("gemini_transcribe_prompt", "")

        myfile = genai.upload_file(audio_path)
        try:
            model = genai.GenerativeModel(model_name)
            config = genai.GenerationConfig(temperature=0.0)
            result = model.generate_content([myfile, prompt], generation_config=config)
            
            final_text = result.text.strip()
            return final_text
        finally:
            myfile.delete()
