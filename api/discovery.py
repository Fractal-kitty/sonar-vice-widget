import json
import urllib3
import requests

from config import GG_CORE_PROPS, ENGINE3_CORE_PROPS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class APIDiscovery:
    def __init__(self):
        self.gg_encrypted_address = None
        self.engine_address = None
        self.sonar_base_url = None

    def load_core_props(self) -> dict:
        """Read coreProps.json, try GG path first then Engine 3 fallback."""
        for path in (GG_CORE_PROPS, ENGINE3_CORE_PROPS):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    props = json.load(f)
                self.gg_encrypted_address = props.get("ggEncryptedAddress")
                self.engine_address = props.get("address")
                return props
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        raise FileNotFoundError("coreProps.json not found. Is SteelSeries GG installed?")

    def discover_sonar(self) -> str | None:
        """Query GG API to find Sonar's dynamic port. Returns base URL or None."""
        if not self.gg_encrypted_address:
            return None
        try:
            url = f"https://{self.gg_encrypted_address}/subApps"
            resp = requests.get(url, verify=False, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            sonar = data.get("subApps", {}).get("sonar", {})
            metadata = sonar.get("metadata", {})
            if not sonar.get("isRunning", False):
                return None
            web_addr = metadata.get("webServerAddress")
            if web_addr:
                self.sonar_base_url = web_addr.rstrip("/")
                return self.sonar_base_url
        except Exception:
            pass
        return None

    def get_engine_url(self) -> str | None:
        """Return the GameSense Engine HTTP base URL."""
        if self.engine_address:
            return f"http://{self.engine_address}"
        return None
