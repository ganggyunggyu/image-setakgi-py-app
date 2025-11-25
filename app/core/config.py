import json
from pathlib import Path
from typing import Any

CONFIG_FILE = Path.home() / ".image_setakgi" / "config.json"

DEFAULT_CONFIG = {
    "resize": {"width": 0, "height": 0, "keep_ratio": True},
    "rotation": 0.0,
    "brightness": 0,
    "contrast": 0,
    "saturation": 0,
    "noise": 0,
    "exif": {
        "remove_all": False,
        "override": {},
    },
    "last_output_dir": "",
    "last_input_dir": "",
}


def ensure_config_dir():
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    ensure_config_dir()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(saved)
            return merged
    return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]):
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def update_config(key: str, value: Any):
    config = load_config()
    config[key] = value
    save_config(config)
