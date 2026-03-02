import requests
from collections import defaultdict


class SonarPresetsClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._session = requests.Session()

    def get_all_configs(self) -> list[dict] | None:
        try:
            resp = self._session.get(f"{self.base_url}/configs", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_configs_by_device(self, favorites_only: bool = True) -> dict[str, list[dict]] | None:
        configs = self.get_all_configs()
        if configs is None:
            return None
        grouped = defaultdict(list)
        for cfg in configs:
            if favorites_only and not cfg.get("isFavorite"):
                continue
            grouped[cfg.get("virtualAudioDevice", "unknown")].append({
                "id": cfg["id"],
                "name": cfg["name"],
                "isFavorite": cfg.get("isFavorite", False),
            })
        return dict(grouped)

    def get_selected_configs(self) -> dict[str, dict] | None:
        try:
            resp = self._session.get(f"{self.base_url}/configs/selected", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            result = {}
            for cfg in data:
                device = cfg.get("virtualAudioDevice", "unknown")
                result[device] = {"id": cfg["id"], "name": cfg["name"]}
            return result
        except Exception:
            return None

    def select_config(self, config_id: str) -> bool:
        try:
            resp = self._session.put(
                f"{self.base_url}/configs/{config_id}/select",
                headers={"Content-Length": "0"}, timeout=5)
            return resp.ok
        except Exception:
            return False
