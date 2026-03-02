"""Sonar audio device routing - list output devices and switch per channel."""

import requests
from urllib.parse import quote


class SonarDevicesClient:
    """Manage audio device routing through Sonar's classicRedirections API."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self._session = requests.Session()

    def get_audio_devices(self) -> list[dict]:
        """Get all available audio devices.

        Returns list of:
            {"id": "...", "name": "Speakers (Realtek)", "dataFlow": "render", "isVad": False}
        """
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
        """Get non-VAD render devices (real physical outputs)."""
        all_devs = self.get_audio_devices()
        return [
            d for d in all_devs
            if d["dataFlow"] == "render" and not d["isVad"]
        ]

    def get_input_devices(self) -> list[dict]:
        """Get non-VAD capture devices (real physical inputs)."""
        all_devs = self.get_audio_devices()
        return [
            d for d in all_devs
            if d["dataFlow"] == "capture" and not d["isVad"]
        ]

    def get_classic_redirections(self) -> dict[str, str]:
        """Get current output device mapping per channel.

        Returns: {"game": "device_id", "chat": "device_id", ...}
        """
        try:
            resp = self._session.get(
                f"{self.base_url}/classicRedirections", timeout=5,
            )
            resp.raise_for_status()
            return {r["id"]: r["deviceId"] for r in resp.json()}
        except Exception:
            return {}

    def set_redirection(self, channel: str, device_id: str) -> bool:
        """Change the output device for a channel.

        Uses: PUT /classicRedirections/{channel}/deviceId/{url_encoded_device_id}
        channel: 'game', 'chat', 'media', 'aux', 'mic'
        """
        try:
            encoded_id = quote(device_id, safe='')
            resp = self._session.put(
                f"{self.base_url}/classicRedirections/{channel}/deviceId/{encoded_id}",
                timeout=5,
            )
            return resp.ok
        except Exception:
            return False
