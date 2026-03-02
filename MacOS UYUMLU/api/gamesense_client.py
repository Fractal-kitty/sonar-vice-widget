import requests
from config import GAMESENSE_GAME, GAMESENSE_DISPLAY, GAMESENSE_EVENT


class GameSenseClient:
    def __init__(self, engine_url: str):
        self.base_url = engine_url
        self._session = requests.Session()
        self.registered = False

    def register(self):
        payload = {
            "game": GAMESENSE_GAME,
            "game_display_name": GAMESENSE_DISPLAY,
            "developer": "Custom Widget",
        }
        resp = self._session.post(f"{self.base_url}/game_metadata", json=payload, timeout=5)
        resp.raise_for_status()
        self.registered = True

    def bind_color_handler(self, device_type: str = "rgb-per-key-zones", zone: str = "all"):
        payload = {
            "game": GAMESENSE_GAME,
            "event": GAMESENSE_EVENT,
            "handlers": [{
                "device-type": device_type,
                "zone": zone,
                "mode": "color",
                "color": {
                    "red": {"has-context": True, "context-key": "red"},
                    "green": {"has-context": True, "context-key": "green"},
                    "blue": {"has-context": True, "context-key": "blue"},
                },
            }],
        }
        resp = self._session.post(f"{self.base_url}/bind_game_event", json=payload, timeout=5)
        resp.raise_for_status()

    def send_color(self, red: int, green: int, blue: int) -> bool:
        payload = {
            "game": GAMESENSE_GAME,
            "event": GAMESENSE_EVENT,
            "data": {
                "value": 100,
                "frame": {
                    "red": max(0, min(255, red)),
                    "green": max(0, min(255, green)),
                    "blue": max(0, min(255, blue)),
                },
            },
        }
        try:
            resp = self._session.post(f"{self.base_url}/game_event", json=payload, timeout=3)
            return resp.ok
        except Exception:
            return False

    def heartbeat(self):
        try:
            self._session.post(
                f"{self.base_url}/game_heartbeat",
                json={"game": GAMESENSE_GAME}, timeout=3)
        except Exception:
            pass

    def cleanup(self):
        try:
            self._session.post(
                f"{self.base_url}/remove_game",
                json={"game": GAMESENSE_GAME}, timeout=3)
        except Exception:
            pass
