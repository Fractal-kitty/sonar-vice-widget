import requests
from config import SONAR_CHANNELS


class SonarClient:
    def __init__(self, base_url: str, mode: str = "classic"):
        self.base_url = base_url
        self.mode = mode
        self._session = requests.Session()

    def get_volumes(self) -> dict | None:
        try:
            resp = self._session.get(
                f"{self.base_url}/volumeSettings/{self.mode}", timeout=3)
            resp.raise_for_status()
            data = resp.json()
            result = {}
            masters = data.get("masters", {})
            master_data = masters.get(self.mode, {})
            result["master"] = {
                "volume": master_data.get("volume", 0.0),
                "muted": master_data.get("muted", False),
            }
            devices = data.get("devices", {})
            for channel in SONAR_CHANNELS:
                if channel == "master":
                    continue
                ch_data = devices.get(channel, {}).get(self.mode, {})
                result[channel] = {
                    "volume": ch_data.get("volume", 0.0),
                    "muted": ch_data.get("muted", False),
                }
            return result
        except Exception:
            return None

    def set_volume(self, channel: str, volume: float) -> bool:
        try:
            volume = max(0.0, min(1.0, volume))
            resp = self._session.put(
                f"{self.base_url}/volumeSettings/{self.mode}/{channel}/Volume/{volume:.2f}",
                headers={"Content-Length": "0"}, timeout=3)
            return resp.ok
        except Exception:
            return False

    def set_mute(self, channel: str, muted: bool) -> bool:
        try:
            mute_str = "true" if muted else "false"
            resp = self._session.put(
                f"{self.base_url}/volumeSettings/{self.mode}/{channel}/Mute/{mute_str}",
                headers={"Content-Length": "0"}, timeout=3)
            return resp.ok
        except Exception:
            return False

    def toggle_mute(self, channel: str) -> bool | None:
        data = self.get_volumes()
        if data and channel in data:
            new_state = not data[channel]["muted"]
            if self.set_mute(channel, new_state):
                return new_state
        return None

    def get_chatmix(self) -> dict | None:
        try:
            resp = self._session.get(f"{self.base_url}/chatMix", timeout=3)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None
