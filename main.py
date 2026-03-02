"""Sonar Vice Widget v3

Features:
- Sonar audio controls (volume + mute + device routing)
- EQ profile switcher (favorites + all)
- RGB lighting via GameSense
- System tray integration (hide/show, always-on-top toggle)
- Theme switcher (SteelSeries / Sonar Dark)
- No taskbar entry — only accessible from system tray
"""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

from api.discovery import APIDiscovery
from api.sonar_client import SonarClient
from api.sonar_presets import SonarPresetsClient
from api.sonar_devices import SonarDevicesClient
from api.gamesense_client import GameSenseClient
from ui.widget import GGWidget
from ui.audio_panel import AudioPanel
from ui.eq_panel import EQPanel
from ui.rgb_panel import RGBPanel
from ui.tray import SystemTray


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    # --- API Discovery ---
    discovery = APIDiscovery()
    try:
        props = discovery.load_core_props()
    except FileNotFoundError as e:
        print(f"HATA: {e}")
        sys.exit(1)

    # Sonar
    sonar = None
    presets = None
    sonar_devices = None
    sonar_url = discovery.discover_sonar()
    if sonar_url:
        sonar = SonarClient(sonar_url)
        presets = SonarPresetsClient(sonar_url)
        sonar_devices = SonarDevicesClient(sonar_url)
        print(f"Sonar: {sonar_url}")

    # GameSense
    gamesense = None
    engine_url = discovery.get_engine_url()
    if engine_url:
        try:
            gamesense = GameSenseClient(engine_url)
            gamesense.register()
            gamesense.bind_color_handler()
            print(f"GameSense: {engine_url}")
        except Exception as e:
            print(f"GameSense basarisiz: {e}")
            gamesense = None

    if gamesense:
        def heartbeat_loop():
            import time
            while True:
                gamesense.heartbeat()
                time.sleep(10)
        threading.Thread(target=heartbeat_loop, daemon=True).start()

    # --- UI ---
    root = ctk.CTk()
    root.title("Sonar Vice Widget")

    # Quit handler — X button and tray "Çık" both use this
    def on_quit():
        if gamesense:
            gamesense.cleanup()
        tray.stop()
        root.destroy()

    # Restart handler — tray "Yeniden Başlat" uses this
    def on_restart():
        if gamesense:
            gamesense.cleanup()

    # Widget — X button quits the application
    widget = GGWidget(root, on_quit_callback=on_quit)

    # System tray — has widget reference for show/hide
    tray = SystemTray(root, widget=widget, on_quit=on_quit, on_restart=on_restart)

    # --- Panel creation (also used as rebuild callback for live theme switching) ---
    def create_panels():
        if sonar:
            audio_tab = widget.add_tab("\U0001F50A Audio")
            AudioPanel(audio_tab, sonar, sonar_devices)

        if presets:
            eq_tab = widget.add_tab("\U0001F3B5 EQ")
            EQPanel(eq_tab, presets)

        rgb_tab = widget.add_tab("\U0001F3A8 RGB")
        RGBPanel(rgb_tab, gamesense)

    create_panels()
    widget.set_rebuild_callback(create_panels)

    # WM_DELETE_WINDOW quits the app
    root.protocol("WM_DELETE_WINDOW", on_quit)

    print("Widget baslatildi.")
    root.mainloop()


if __name__ == "__main__":
    main()
