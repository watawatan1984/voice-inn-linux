from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, prompts: dict) -> str:
        pass
