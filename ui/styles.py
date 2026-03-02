"""Theme system - switchable color palettes."""

import json
import os

# Fonts (shared across all themes)
FONT_TITLE = ("Segoe UI", 15, "bold")
FONT_SECTION = ("Segoe UI", 13, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 11)
FONT_TINY = ("Segoe UI", 10)
FONT_ICON = ("Segoe UI Emoji", 14)

THEMES = {
    "SteelSeries": {
        "ACCENT": "#FF6600",
        "ACCENT_HOVER": "#FF8533",
        "ACCENT_DARK": "#CC5200",
        "BG_DARK": "#0D1117",
        "BG_MID": "#161B22",
        "BG_CARD": "#1C2333",
        "BG_HOVER": "#252D3A",
        "TEXT": "#E6EDF3",
        "TEXT_DIM": "#8B949E",
        "TEXT_MUTED": "#484F58",
        "GREEN": "#3FB950",
        "RED": "#F85149",
        "YELLOW": "#D29922",
        "BLUE": "#58A6FF",
    },
    "Sonar Dark": {
        "ACCENT": "#02DDBC",
        "ACCENT_HOVER": "#33E8CF",
        "ACCENT_DARK": "#019E86",
        "BG_DARK": "#171F24",
        "BG_MID": "#1E262D",
        "BG_CARD": "#222931",
        "BG_HOVER": "#2C3540",
        "TEXT": "#FFFFFF",
        "TEXT_DIM": "#8A939E",
        "TEXT_MUTED": "#3E4350",
        "GREEN": "#02DDBC",
        "RED": "#FF5359",
        "YELLOW": "#FFE061",
        "BLUE": "#2476FE",
    },
}

_SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "widget_settings.json",
)


def _load_settings() -> dict:
    try:
        with open(_SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_settings(settings: dict):
    try:
        with open(_SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


def get_current_theme_name() -> str:
    return _load_settings().get("theme", "SteelSeries")


def set_theme(name: str):
    s = _load_settings()
    s["theme"] = name
    _save_settings(s)


def get_theme() -> dict:
    name = get_current_theme_name()
    return THEMES.get(name, THEMES["SteelSeries"])


# --- Module-level color variables (updated by apply_theme) ---
_t = get_theme()
ACCENT = _t["ACCENT"]
ACCENT_HOVER = _t["ACCENT_HOVER"]
ACCENT_DARK = _t["ACCENT_DARK"]
BG_DARK = _t["BG_DARK"]
BG_MID = _t["BG_MID"]
BG_CARD = _t["BG_CARD"]
BG_HOVER = _t["BG_HOVER"]
TEXT = _t["TEXT"]
TEXT_DIM = _t["TEXT_DIM"]
TEXT_MUTED = _t["TEXT_MUTED"]
GREEN = _t["GREEN"]
RED = _t["RED"]
YELLOW = _t["YELLOW"]
BLUE = _t["BLUE"]


def apply_theme(name: str | None = None):
    """Update module-level color variables to match the given theme."""
    global ACCENT, ACCENT_HOVER, ACCENT_DARK
    global BG_DARK, BG_MID, BG_CARD, BG_HOVER
    global TEXT, TEXT_DIM, TEXT_MUTED
    global GREEN, RED, YELLOW, BLUE

    if name:
        set_theme(name)
    t = get_theme()
    ACCENT = t["ACCENT"]
    ACCENT_HOVER = t["ACCENT_HOVER"]
    ACCENT_DARK = t["ACCENT_DARK"]
    BG_DARK = t["BG_DARK"]
    BG_MID = t["BG_MID"]
    BG_CARD = t["BG_CARD"]
    BG_HOVER = t["BG_HOVER"]
    TEXT = t["TEXT"]
    TEXT_DIM = t["TEXT_DIM"]
    TEXT_MUTED = t["TEXT_MUTED"]
    GREEN = t["GREEN"]
    RED = t["RED"]
    YELLOW = t["YELLOW"]
    BLUE = t["BLUE"]
