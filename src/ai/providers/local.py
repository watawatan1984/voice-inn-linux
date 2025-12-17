import os
import logging
from src.core.config import config_manager
from src.ai.providers.base import AIProvider

class LocalProvider(AIProvider):
    def __init__(self):
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError("faster-whisper is not installed. Please install it with 'pip install faster-whisper'")
        
        local_settings = config_manager.settings.get("local", {})
        model_size = local_settings.get("model_size", "large-v3")
        device = local_settings.get("device", "cuda")
        compute_type = local_settings.get("compute_type", "float16")
        
        logging.info(f"Loading Local Whisper Model: {model_size} on {device} ({compute_type})")
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as e:
            logging.error(f"Failed to load WhisperModel: {e}")
            raise e

    def transcribe(self, audio_path: str, prompts: dict) -> str:
        # prompt argument in transcribe is for initial prompt (context)
        # We can use the whisper prompt from settings if applicable, but typical whisper prompt is different.
        # But 'initial_prompt' is supported by faster-whisper.
        whisper_prompt = prompts.get("groq_whisper_prompt", "") # Re-use the same prompt or add a new one?
        # The prompt in settings is "You are a pro transcriber..." which might be too long/chatty for Whisper initial prompt?
        # Whisper initial prompt is usually previous text or style guide.
        # faster-whisper 'initial_prompt'
        
        segments, info = self.model.transcribe(
            audio_path, 
            beam_size=5, 
            initial_prompt=whisper_prompt,
            language="ja"
        )
        
        text_segments = []
        for segment in segments:
            text_segments.append(segment.text)
            
        return "".join(text_segments).strip()
