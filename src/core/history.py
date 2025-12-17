import os
import json
import time
import tempfile
from src.core.config import STATE_DIR
from src.core.utils import now_iso

HISTORY_PATH = os.path.join(STATE_DIR, 'history.json')
HISTORY_MAX_ITEMS = 50

def load_history_file():
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            items = data.get("items", [])
            return items if isinstance(items, list) else []
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []

def save_history_file(items):
    if not isinstance(items, list):
        items = []
    items = items[:HISTORY_MAX_ITEMS]
    payload = {"version": 1, "items": items}

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            suffix='.tmp',
            delete=False,
            dir=STATE_DIR,
        ) as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            tmp_path = f.name
        os.replace(tmp_path, HISTORY_PATH)
        tmp_path = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

def append_history_item(text=None, error=None, provider=None):
    txt = (text or "").strip()
    err = (str(error).strip() if error is not None else "")
    if not txt and not err:
        return

    item = {
        "id": str(int(time.time() * 1000)),
        "created_at": now_iso(),
        "provider": str(provider or ""),
        "text": txt,
        "error": (err or None),
    }

    items = load_history_file()
    if not isinstance(items, list):
        items = []
    items.insert(0, item)
    save_history_file(items)
