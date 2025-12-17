import os
from groq import Groq
from src.core.config import config_manager
from src.ai.providers.base import AIProvider

class GroqProvider(AIProvider):
    def __init__(self):
        self.api_key = config_manager.settings.get("groq_key") or os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Error initializing Groq client: {e}")

    def transcribe(self, audio_path: str, prompts: dict) -> str:
        if not self.client:
            raise RuntimeError("Groq Client not initialized (Missing API Key?)")

        whisper_prompt = prompts.get("groq_whisper_prompt", "")
        refine_system = prompts.get("groq_refine_system_prompt", "")

        # 1. Transcribe
        with open(audio_path, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
                file=(audio_path, file.read()),
                model="whisper-large-v3",
                language="ja",
                temperature=0.0,
                prompt=whisper_prompt,
                response_format="text"
            )
        raw_text = str(transcription)
        
        if not raw_text or not raw_text.strip() or raw_text == whisper_prompt:
             return ""

        # 2. Refine
        completion = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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
        final_text = completion.choices[0].message.content
        return final_text
