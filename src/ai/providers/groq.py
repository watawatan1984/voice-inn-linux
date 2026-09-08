import os
import logging
from typing import Dict, Any

from src.core.config import config_manager
from src.core.const import DEFAULT_GROQ_WHISPER_MODEL, DEFAULT_GROQ_REFINE_MODEL
from src.ai.providers.base import AIProvider

class GroqProvider(AIProvider):
    def __init__(self):
        try:
            from groq import Groq
            self._groq_cls = Groq
        except ImportError:
            raise ImportError("The 'groq' package is required. Please install it via pip or uv.")

        self.api_key = config_manager.settings.get("groq_key") or os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = self._groq_cls(api_key=self.api_key)
            except Exception as e:
                logging.error(f"Error initializing Groq client: {e}")


    def transcribe(self, audio_path: str, prompts: Dict[str, Any]) -> str:
        if not self.client:
            raise RuntimeError("Groq Client not initialized (Missing API Key?)")

        whisper_model = (
            config_manager.settings.get("groq_whisper_model")
            or os.getenv("GROQ_WHISPER_MODEL")
            or DEFAULT_GROQ_WHISPER_MODEL
        )
        refine_model = (
            config_manager.settings.get("groq_refine_model")
            or os.getenv("GROQ_REFINE_MODEL")
            or DEFAULT_GROQ_REFINE_MODEL
        )

        whisper_prompt = prompts.get("groq_whisper_prompt", "")
        refine_system = prompts.get("groq_refine_system_prompt", "")

        # 1. 音声文字起こし (Whisper)
        with open(audio_path, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
                file=(audio_path, file.read()),
                model=whisper_model,
                language="ja",
                temperature=0.0,
                prompt=whisper_prompt,
                response_format="text"
            )
        raw_text = str(transcription)
        
        if not raw_text or not raw_text.strip() or raw_text == whisper_prompt:
            return ""

        # 2. テキスト整形 (LLM)
        if refine_system:
            completion = self.client.chat.completions.create(
                model=refine_model,
                messages=[
                    {
                        "role": "system", 
                        "content": refine_system
                    },
                    {
                        "role": "user", 
                        "content": raw_text
                    }
                ],
                temperature=0.0,
            )
            final_text = completion.choices[0].message.content or ""
            return final_text.strip()

        return raw_text.strip()
