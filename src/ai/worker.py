from PyQt6.QtCore import QObject, pyqtSignal
import logging
import traceback
import io

from src.core.config import config_manager
from src.ai.providers.groq import GroqProvider
from src.ai.providers.gemini import GeminiProvider
from src.ai.providers.local import LocalProvider

class AIWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, provider_name, audio_path, prompts):
        super().__init__()
        self.provider_name = provider_name
        self.audio_path = audio_path
        self.prompts = prompts
        self.provider = None

    def run(self):
        try:
            if self.provider_name == "groq":
                self.provider = GroqProvider()
            elif self.provider_name == "gemini":
                self.provider = GeminiProvider()
            elif self.provider_name == "local":
                self.provider = LocalProvider()
            else:
                raise ValueError(f"Unknown provider: {self.provider_name}")

            logging.info(f"Starting transcription with {self.provider_name}")
            text = self.provider.transcribe(self.audio_path, self.prompts)
            logging.info(f"Transcription finished: {len(text)} chars")
            self.finished.emit(text)

        except Exception as e:
            logging.error(f"AIWorker Error: {traceback.format_exc()}")
            self.error.emit(str(e))
