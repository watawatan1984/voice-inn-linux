import sys
import os
import platform
from datetime import datetime

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # Using src/core/utils.py depth to resolve root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _xdg_home(env_key: str, fallback_path: str) -> str:
    return os.path.expanduser(os.getenv(env_key) or fallback_path)

def get_config_dir() -> str:
    """
    設定ファイルの保存ディレクトリを取得する。
    ポータブルモード、環境変数指定、OS別標準ディレクトリ、既存ディレクトリとの下位互換に対応。
    """
    if str(os.getenv("VOICEIN_PORTABLE") or "").strip() == "1":
        return get_app_dir()

    custom = os.getenv("VOICEIN_CONFIG_DIR")
    if custom:
        return os.path.abspath(custom)

    legacy_xdg = os.path.join(_xdg_home("XDG_CONFIG_HOME", "~/.config"), "voice-in")
    system = platform.system()

    # 既に legacy XDG パスが存在する場合は既存設定の互換性を最優先
    if os.path.exists(legacy_xdg):
        return legacy_xdg

    if system == "Windows":
        appdata = os.getenv("APPDATA")
        if appdata:
            return os.path.join(appdata, "VoiceIn")
    elif system == "Darwin":
        return os.path.expanduser("~/Library/Application Support/VoiceIn")

    return legacy_xdg

def get_state_dir() -> str:
    """
    ログや履歴ファイルの一時状態保存ディレクトリを取得する。
    """
    if str(os.getenv("VOICEIN_PORTABLE") or "").strip() == "1":
        return get_app_dir()

    custom = os.getenv("VOICEIN_STATE_DIR")
    if custom:
        return os.path.abspath(custom)

    legacy_xdg = os.path.join(_xdg_home("XDG_STATE_HOME", "~/.local/state"), "voice-in")
    system = platform.system()

    if os.path.exists(legacy_xdg):
        return legacy_xdg

    if system == "Windows":
        localappdata = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        if localappdata:
            return os.path.join(localappdata, "VoiceIn")
    elif system == "Darwin":
        return os.path.expanduser("~/Library/Application Support/VoiceIn")

    return legacy_xdg


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
