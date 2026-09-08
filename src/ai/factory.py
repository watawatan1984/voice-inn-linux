"""
AI Provider Factory Module
Provides unified creation and management of AI transcription providers.
"""

from typing import Dict, Type
import logging

from src.ai.providers.base import AIProvider
from src.ai.providers.gemini import GeminiProvider
from src.ai.providers.groq import GroqProvider
from src.ai.providers.local import LocalProvider

_PROVIDERS: Dict[str, Type[AIProvider]] = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "local": LocalProvider,
}

def get_provider(provider_name: str) -> AIProvider:
    """
    指定されたプロバイダ名に対応する AIProvider インスタンスを生成して返す。
    
    Args:
        provider_name: "gemini", "groq", "local" 等のプロバイダ識別名
        
    Returns:
        AIProvider インスタンス
        
    Raises:
        ValueError: 未知のプロバイダ名が指定された場合
    """
    key = (provider_name or "").strip().lower()
    provider_cls = _PROVIDERS.get(key)
    if not provider_cls:
        available = ", ".join(_PROVIDERS.keys())
        raise ValueError(f"Unknown provider: '{provider_name}'. Available providers: {available}")
    
    logging.debug(f"Instantiating AI provider: {key}")
    return provider_cls()

def get_available_providers() -> list[str]:
    """登録されているプロバイダ名のリストを返す。"""
    return list(_PROVIDERS.keys())
