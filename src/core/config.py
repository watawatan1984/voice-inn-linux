import os
import json
import copy
import logging
from dotenv import load_dotenv, set_key

from src.core.utils import get_config_dir, get_state_dir, deep_merge_dict
from src.core.const import (
    SUPPORTED_LANGUAGES,
    DEFAULT_APP_CATEGORIES,
    DEFAULT_CATEGORY_PROMPTS,
    DEFAULT_GROQ_WHISPER_PROMPT,
    DEFAULT_GROQ_REFINE_PROMPT,
    DEFAULT_GEMINI_TRANSCRIBE_PROMPT,
    DEFAULT_LOCAL_MODEL
)

CONFIG_DIR = get_config_dir()
STATE_DIR = get_state_dir()
ENV_PATH = os.path.join(CONFIG_DIR, '.env')
SETTINGS_PATH = os.path.join(CONFIG_DIR, 'settings.json')

DEFAULT_SETTINGS = {
    "audio": {
        "input_device": None,
        "input_gain_db": 0.0,
        "max_record_seconds": 60,
        "auto_paste": True,
        "paste_delay_ms": 60,
        "hold_key": "alt_l",
    },
    "ui": {
        "overlay_pos": None,
        "language": "ja",
    },
    "prompts": {
        "groq_whisper_prompt": DEFAULT_GROQ_WHISPER_PROMPT,
        "groq_refine_system_prompt": DEFAULT_GROQ_REFINE_PROMPT,
        "gemini_transcribe_prompt": DEFAULT_GEMINI_TRANSCRIBE_PROMPT,
    },
    "dictionary": {},
    "local": {
        "model_size": DEFAULT_LOCAL_MODEL,
        "device": "cuda",
        "compute_type": "float16"
    },
    "app_categories": copy.deepcopy(DEFAULT_APP_CATEGORIES),
    "category_prompts": copy.deepcopy(DEFAULT_CATEGORY_PROMPTS),
    "detected_apps": {},
    "context_aware_enabled": True
}


class ConfigManager:
    def __init__(self):
        self.settings = copy.deepcopy(DEFAULT_SETTINGS)
        self.ensure_dirs()
        self.load_env()
        self.load_settings()

    def ensure_dirs(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            os.makedirs(STATE_DIR, exist_ok=True)
        except Exception:
            pass

    def load_env(self):
        if not os.path.exists(ENV_PATH):
            try:
                os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
                with open(ENV_PATH, 'a', encoding='utf-8'):
                    pass
            except Exception as e:
                logging.error(f"Failed to create .env: {e}")
        if os.path.exists(ENV_PATH):
            load_dotenv(ENV_PATH, override=True)

    def load_settings(self):
        if not os.path.exists(SETTINGS_PATH):
            self.settings = copy.deepcopy(DEFAULT_SETTINGS)
            return
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.settings = deep_merge_dict(DEFAULT_SETTINGS, data)
        except Exception as e:
            logging.error(f"Failed to load settings.json: {e}")
            self.settings = copy.deepcopy(DEFAULT_SETTINGS)

    def save_settings(self):
        try:
            with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Failed to save settings.json: {e}")

    def update_settings(self, new_settings):
        self.settings = deep_merge_dict(self.settings, new_settings)
        self.save_settings()

    def update_env(self, key, value):
        try:
            # Also update os.environ for current process
            if value:
                os.environ[key] = value
                set_key(ENV_PATH, key, value)
            else:
                # If value is empty, maybe remove it? Or just set to empty string.
                # set_key might fail if file doesn't exist but we ensured it.
                os.environ[key] = ""
                set_key(ENV_PATH, key, "")
        except Exception as e:
            logging.error(f"Failed to update .env: {e}")

    def get_language(self):
        ui = self.settings.get("ui", {})
        if isinstance(ui, dict):
            lang = str(ui.get("language") or "").strip() or "ja"
            if lang in SUPPORTED_LANGUAGES:
                return lang
        return "ja"

# Global instance
config_manager = ConfigManager()
app_settings = config_manager.settings # Direct access shortcut if needed, but better to use manager
