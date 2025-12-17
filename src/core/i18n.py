from src.core.const import TRANSLATIONS
from src.core.config import config_manager

def t(key: str, **kwargs) -> str:
    lang = config_manager.get_language()
    src = TRANSLATIONS.get(lang) or {}
    base = TRANSLATIONS.get("en") or {}
    msg = src.get(key) or base.get(key) or key
    try:
        return msg.format(**kwargs)
    except Exception:
        return msg
