import logging
import traceback
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from src.ai.factory import get_provider
from src.ai.providers.base import AIProvider

class AIWorker(QObject):
    """
    バックグラウンドスレッドで音声文字起こし処理を実行する QObject ワーカー。
    """
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, provider_name: str, audio_path: str, prompts: Dict[str, Any]):
        super().__init__()
        self.provider_name = provider_name
        self.audio_path = audio_path
        self.prompts = prompts
        self.provider: Optional[AIProvider] = None

    def run(self):
        try:
            self.provider = get_provider(self.provider_name)
            logging.info(f"Starting transcription with {self.provider_name}")
            text = self.provider.transcribe(self.audio_path, self.prompts)
            logging.info(f"Transcription finished: {len(text)} chars")
            self.finished.emit(text)

        except Exception as e:
            logging.error(f"AIWorker Error: {traceback.format_exc()}")
            self.error.emit(str(e))
