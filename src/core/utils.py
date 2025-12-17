import sys
import os
from datetime import datetime

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__)).split('src')[0] # Adjust for src depth if needed, or better:
    # If this file is in src/core/utils.py, app dir is ../../
    # But original code used `__file__` of main.py.
    # Let's keep it robust. If frozen, it's executable dir.
    # If not frozen, it's the root of the repo.

def _xdg_home(env_key: str, fallback_path: str) -> str:
    return os.path.expanduser(os.getenv(env_key) or fallback_path)

def get_config_dir() -> str:
    if str(os.getenv("VOICEIN_PORTABLE") or "").strip() == "1":
        return get_app_dir()
    return os.path.join(_xdg_home("XDG_CONFIG_HOME", "~/.config"), "voice-in")

def get_state_dir() -> str:
    if str(os.getenv("VOICEIN_PORTABLE") or "").strip() == "1":
        return get_app_dir()
    return os.path.join(_xdg_home("XDG_STATE_HOME", "~/.local/state"), "voice-in")

def deep_merge_dict(base, override):
    if not isinstance(base, dict) or not isinstance(override, dict):
        return override
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge_dict(result[k], v)
        else:
            result[k] = v
    return result

def now_iso():
    try:
        return datetime.now().astimezone().isoformat(timespec="seconds")
    except Exception:
        return datetime.now().isoformat()
