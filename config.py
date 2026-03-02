import os

# coreProps.json paths
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
