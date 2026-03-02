import requests
from urllib.parse import quote


class SonarDevicesClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._session = requests.Session()

    def get_audio_devices(self) -> list[dict]:
        try:
            resp = self._session.get(f"{self.base_url}/audioDevices", timeout=5)
            resp.raise_for_status()
            return [
                {
                    "id": d["id"],
                    "name": d["friendlyName"],
                    "dataFlow": d.get("dataFlow", ""),
                    "isVad": d.get("isVad", False),
                    "role": d.get("role", "none"),
                }
                for d in resp.json()
            ]
        except Exception:
            return []

    def get_output_devices(self) -> list[dict]:
        return [d for d in self.get_audio_devices()
                if d["dataFlow"] == "render" and not d["isVad"]]

    def get_input_devices(self) -> list[dict]:
        return [d for d in self.get_audio_devices()
                if d["dataFlow"] == "capture" and not d["isVad"]]

    def get_classic_redirections(self) -> dict[str, str]:
        try:
            resp = self._session.get(f"{self.base_url}/classicRedirections", timeout=5)
            resp.raise_for_status()
            return {r["id"]: r["deviceId"] for r in resp.json()}
        except Exception:
            return {}

    def set_redirection(self, channel: str, device_id: str) -> bool:
        try:
            encoded_id = quote(device_id, safe='')
            resp = self._session.put(
                f"{self.base_url}/classicRedirections/{channel}/deviceId/{encoded_id}",
                timeout=5)
            return resp.ok
        except Exception:
            return False
