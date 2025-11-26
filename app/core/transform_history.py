import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

HISTORY_FILE = Path.home() / ".image_setakgi" / "transform_history.json"


def ensure_history_dir():
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_history() -> dict[str, Any]:
    ensure_history_dir()
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(history: dict[str, Any]):
    ensure_history_dir()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def record_transform(
    filename: str,
    crop: Optional[dict] = None,
    rotation: float = 0,
    brightness: int = 0,
    contrast: int = 0,
    saturation: int = 0,
    noise: int = 0,
    metadata_actions: Optional[list] = None,
):
    history = load_history()

    record = {
        "crop": crop or {},
        "rotation": rotation,
        "brightness": brightness,
        "contrast": contrast,
        "saturation": saturation,
        "noise": noise,
        "metadataActions": metadata_actions or [],
        "timestamp": datetime.now().isoformat(),
    }

    history[filename] = record
    save_history(history)


def get_file_history(filename: str) -> Optional[dict]:
    history = load_history()
    return history.get(filename)


def clear_history():
    save_history({})


def delete_file_history(filename: str):
    history = load_history()
    if filename in history:
        del history[filename]
        save_history(history)
