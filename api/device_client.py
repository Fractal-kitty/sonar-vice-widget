"""SteelSeries device info - battery level, connection status.

Battery info is obtained via TWO methods:
1. HTTP POST /device/{id}/function/read_battery_status (legacy - may fail)
2. GG WebSocket at wss://{ggEncryptedAddress}/sock listening for
   device_event messages containing batteryEvent data (modern/push-based)
"""

import json
import ssl
import threading
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import websocket
    _HAS_WEBSOCKET = True
except ImportError:
    _HAS_WEBSOCKET = False


class DeviceClient:
    """Query the Engine API for headset battery and device info."""

    def __init__(self, encrypted_address: str, gg_encrypted_address: str = ""):
        # encrypted_address = "127.0.0.1:63021" (from coreProps encryptedAddress)
        self.base_url = f"https://{encrypted_address}"
        self._gg_ws_url = f"wss://{gg_encrypted_address}/sock" if gg_encrypted_address else ""
        self._session = requests.Session()
        self._session.verify = False
        self._device_id = None
        self._device_name = None

        # WebSocket battery state
        self._ws = None
        self._ws_thread = None
        self._ws_battery = None          # latest battery dict from WS
        self._ws_battery_lock = threading.Lock()
        self._ws_connected = False

    def discover_headset(self) -> bool:
        """Find first connected headset device with battery support."""
        try:
            resp = self._session.get(f"{self.base_url}/devices", timeout=5)
            resp.raise_for_status()
            devices = resp.json().get("devices", [])

            # First: connected device with battery
            for d in devices:
                if d.get("connected") == 1 and "batteryLevels" in d.get(
                    "genericDevicePropertiesStatus", []
                ):
                    self._device_id = d["id"]
                    self._device_name = d.get("display_name", d.get("full_name", "Headset"))
                    return True

            # Second: any device with battery (dongle connected, headset maybe off)
            for d in devices:
                if "batteryLevels" in d.get("genericDevicePropertiesStatus", []):
                    self._device_id = d["id"]
                    self._device_name = d.get("display_name", d.get("full_name", "Headset"))
                    return True

            return False
        except Exception:
            return False

    @property
    def device_name(self) -> str:
        return self._device_name or "Unknown"

    # --- WebSocket Battery (modern / push-based) ---

    def start_ws_battery_listener(self):
        """Start a background WebSocket listener for battery events."""
        if not _HAS_WEBSOCKET or not self._gg_ws_url:
            return
        if self._ws_thread and self._ws_thread.is_alive():
            return  # already running

        def _on_message(ws, message):
            try:
                data = json.loads(message)
                event_data = data.get("data", {})
                # Check for batteryEvent in device_event messages
                if "batteryEvent" in event_data:
                    be = event_data["batteryEvent"]
                    level = be.get("batteryPercent", be.get("leftBatteryPercent", -1))
                    with self._ws_battery_lock:
                        self._ws_battery = {
                            "level": level,
                            "charging": be.get("isCharging", False),
                            "dac_level": -1,
                        }
                elif "chargerBatteryEvent" in event_data:
                    ce = event_data["chargerBatteryEvent"]
                    with self._ws_battery_lock:
                        if self._ws_battery:
                            self._ws_battery["dac_level"] = ce.get("chargerBatteryPercent", -1)
            except Exception:
                pass

        def _on_open(ws):
            self._ws_connected = True

        def _on_close(ws, code, msg):
            self._ws_connected = False

        def _on_error(ws, error):
            self._ws_connected = False

        def _run():
            ssl_opts = {"cert_reqs": ssl.CERT_NONE}
            self._ws = websocket.WebSocketApp(
                self._gg_ws_url,
                on_open=_on_open,
                on_message=_on_message,
                on_error=_on_error,
                on_close=_on_close,
            )
            while True:
                try:
                    self._ws.run_forever(
                        sslopt=ssl_opts,
                        ping_interval=30,
                        ping_timeout=10,
                        reconnect=5,
                    )
                except Exception:
                    pass
                import time
                time.sleep(5)  # reconnect delay

        self._ws_thread = threading.Thread(target=_run, daemon=True)
        self._ws_thread.start()

    def get_ws_battery(self) -> dict | None:
        """Get latest battery data from WebSocket (if available)."""
        with self._ws_battery_lock:
            return self._ws_battery.copy() if self._ws_battery else None

    # --- HTTP Battery (legacy) ---

    def get_battery(self) -> dict | None:
        """Read battery status. Tries WebSocket data first, falls back to HTTP.

        Returns:
            {"level": 85, "charging": True, "dac_level": 100} or None
        """
        # Try WS data first (more reliable)
        ws_data = self.get_ws_battery()
        if ws_data and ws_data["level"] >= 0:
            return ws_data

        # Fallback to HTTP
        if not self._device_id:
            return None
        try:
            resp = self._session.post(
                f"{self.base_url}/device/{self._device_id}/function/read_battery_status",
                json={},
                timeout=5,
            )
            if not resp.ok:
                return None
            data = resp.json()
            if "error" in data:
                return None
            fd_str = data.get("function_data")
            if not fd_str:
                return None
            fd = json.loads(fd_str)
            headset = fd.get("headset_battery_level", {})
            charger = fd.get("charger_battery_level", {})
            charging = fd.get("charging_status", {})
            return {
                "level": headset.get("level", -1),
                "charging": charging.get("chargingStatus", "DISCHARGING") != "DISCHARGING",
                "dac_level": charger.get("level", -1),
            }
        except Exception:
            return None

    def get_devices_list(self) -> list[dict]:
        """Get all connected devices with basic info."""
        try:
            resp = self._session.get(f"{self.base_url}/devices", timeout=5)
            resp.raise_for_status()
            return [
                {
                    "id": d["id"],
                    "name": d.get("display_name", d.get("full_name", "")),
                    "type": d.get("deviceTypeName", ""),
                    "connected": d.get("connected") == 1,
                    "has_battery": "batteryLevels" in d.get("genericDevicePropertiesStatus", []),
                }
                for d in resp.json().get("devices", [])
            ]
        except Exception:
            return []
