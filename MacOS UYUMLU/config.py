import os
import platform

IS_MACOS = platform.system() == "Darwin"

# coreProps.json paths — platform-specific
if IS_MACOS:
    # macOS: SteelSeries GG stores coreProps.json under /Library or ~/Library
    _lib = os.path.expanduser("~/Library/Application Support")
    GG_CORE_PROPS = os.path.join(_lib, "SteelSeries", "GG", "coreProps.json")
    ENGINE3_CORE_PROPS = os.path.join(_lib, "SteelSeries Engine 3", "coreProps.json")

    # Also check system-wide path
    _sys_lib = "/Library/Application Support"
    if not os.path.exists(GG_CORE_PROPS) and os.path.exists(
        os.path.join(_sys_lib, "SteelSeries", "GG", "coreProps.json")
    ):
        GG_CORE_PROPS = os.path.join(_sys_lib, "SteelSeries", "GG", "coreProps.json")
    if not os.path.exists(ENGINE3_CORE_PROPS) and os.path.exists(
        os.path.join(_sys_lib, "SteelSeries Engine 3", "coreProps.json")
    ):
        ENGINE3_CORE_PROPS = os.path.join(_sys_lib, "SteelSeries Engine 3", "coreProps.json")
else:
    # Windows
    GG_CORE_PROPS = os.path.join(
        os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
        "SteelSeries", "GG", "coreProps.json",
    )
    ENGINE3_CORE_PROPS = os.path.join(
        os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
        "SteelSeries", "SteelSeries Engine 3", "coreProps.json",
    )

# Sonar audio channels
SONAR_CHANNELS = ["master", "game", "chatRender", "media", "aux", "chatCapture"]
SONAR_CHANNEL_LABELS = {
    "master": "Master",
    "game": "Game",
    "chatRender": "Chat",
    "media": "Media",
    "aux": "Aux",
    "chatCapture": "Mic",
}
SONAR_CHANNEL_ICONS = {
    "master": "\U0001F39B",
    "game": "\U0001F3AE",
    "chatRender": "\U0001F3A7",
    "media": "\U0001F3B5",
    "aux": "\U0001F50A",
    "chatCapture": "\U0001F399",
}

# Sonar device display names for EQ profiles tab
SONAR_DEVICE_LABELS = {
    "game": "Game",
    "chatRender": "Chat",
    "chatCapture": "Mic",
    "media": "Media",
    "aux": "Aux",
}

# GameSense
GAMESENSE_GAME = "SONAR_VICE_WIDGET"
GAMESENSE_DISPLAY = "Sonar Vice Widget"
GAMESENSE_EVENT = "RGB_COLOR"

# Widget
WIDGET_WIDTH = 380
WIDGET_HEIGHT = 540
