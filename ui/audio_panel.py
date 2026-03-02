import customtkinter as ctk
import threading

from config import SONAR_CHANNELS, SONAR_CHANNEL_LABELS, SONAR_CHANNEL_ICONS
from ui import styles

# Sonar channel -> classicRedirections key mapping
CHANNEL_TO_REDIRECT = {
    "game": "game",
    "chatRender": "chat",
    "media": "media",
    "aux": "aux",
    "chatCapture": "mic",
}


class AudioPanel:
    """Audio controls with volume sliders, mute toggles, device selectors, and ChatMix."""

    def __init__(self, parent: ctk.CTkFrame, sonar_client, sonar_devices=None):
        self.parent = parent
        self.sonar = sonar_client
        self.devices_client = sonar_devices
        self.sliders = {}
        self.mute_buttons = {}
        self.value_labels = {}
        self._value_frames = {}       # channel -> wrapper frame for label/entry swap
        self._value_entries = {}      # channel -> CTkEntry (active inline edit)
        self._editing_channel = None  # which channel is being edited
        self._device_menus = {}
        self._expand_states = {}
        self._device_frames = {}
        self._output_devices = []
        self._input_devices = []
        self._redirections = {}
        self._name_to_id = {}
        self._updating = False

        parent.configure(fg_color=styles.BG_DARK)

        self.scroll = ctk.CTkScrollableFrame(
            parent, fg_color=styles.BG_DARK, corner_radius=0,
            scrollbar_button_color=styles.BG_CARD,
            scrollbar_button_hover_color=styles.ACCENT,
        )
        self.scroll.pack(fill="both", expand=True, padx=2, pady=2)

        # --- ChatMix card (top) ---
        self._create_chatmix_card()

        # --- Volume cards ---
        for channel in SONAR_CHANNELS:
            self._create_channel_card(channel)

        self.status_label = ctk.CTkLabel(
            parent, text="", font=styles.FONT_SMALL, text_color=styles.TEXT_DIM,
        )
        self.status_label.pack(pady=(2, 4))

        # Load devices in background
        if self.devices_client:
            threading.Thread(target=self._load_devices, daemon=True).start()

        self._poll_volumes()

    # ========================
    # ChatMix
    # ========================

    def _create_chatmix_card(self):
        """ChatMix balance control - Game vs Chat volume balance."""
        self._chatmix_dragging = False
        self._chatmix_base_game = 1.0
        self._chatmix_base_chat = 1.0

        wrapper = ctk.CTkFrame(self.scroll, fg_color="transparent")
        wrapper.pack(fill="x", padx=4, pady=(4, 6))

        card = ctk.CTkFrame(wrapper, fg_color=styles.BG_CARD, corner_radius=10)
        card.pack(fill="x")

        # Title row
        title_row = ctk.CTkFrame(card, fg_color="transparent")
        title_row.pack(fill="x", padx=12, pady=(8, 0))

        ctk.CTkLabel(
            title_row, text="\U0001F3A7  ChatMix",
            font=styles.FONT_BODY, text_color=styles.TEXT,
        ).pack(side="left")

        self._chatmix_status = ctk.CTkLabel(
            title_row, text="",
            font=("Segoe UI", 11), text_color=styles.TEXT_DIM,
        )
        self._chatmix_status.pack(side="right")

        # Slider row: Game label -- slider -- Chat label
        slider_row = ctk.CTkFrame(card, fg_color="transparent")
        slider_row.pack(fill="x", padx=12, pady=(4, 4))

        self._chatmix_game_label = ctk.CTkLabel(
            slider_row, text="\U0001F3AE",
            font=("Segoe UI Emoji", 16), text_color=styles.ACCENT,
            width=30,
        )
        self._chatmix_game_label.pack(side="left")

        self._chatmix_slider = ctk.CTkSlider(
            slider_row, from_=-100, to=100,
            fg_color=styles.BG_HOVER,
            progress_color=styles.BG_HOVER,
            button_color=styles.ACCENT,
            button_hover_color=styles.ACCENT_HOVER,
            height=14, corner_radius=7,
            command=self._on_chatmix_change,
        )
        self._chatmix_slider.pack(side="left", fill="x", expand=True, padx=6)
        self._chatmix_slider.set(0)

        self._chatmix_chat_label = ctk.CTkLabel(
            slider_row, text="\U0001F3A7",
            font=("Segoe UI Emoji", 16), text_color=styles.ACCENT,
            width=30,
        )
        self._chatmix_chat_label.pack(side="left")

        # Balance value row
        val_row = ctk.CTkFrame(card, fg_color="transparent")
        val_row.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            val_row, text="Game",
            font=("Segoe UI", 11), text_color=styles.TEXT_DIM,
        ).pack(side="left")

        self._chatmix_val_label = ctk.CTkLabel(
            val_row, text="Dengeli",
            font=("Segoe UI", 12, "bold"), text_color=styles.TEXT_DIM,
        )
        self._chatmix_val_label.pack(side="left", expand=True)

        ctk.CTkLabel(
            val_row, text="Chat",
            font=("Segoe UI", 11), text_color=styles.TEXT_DIM,
        ).pack(side="right")

    def _on_chatmix_change(self, value: float):
        """User dragged the ChatMix slider - adjust Game/Chat volumes."""
        self._chatmix_dragging = True
        balance = value / 100.0  # -1.0 to 1.0

        # Snapshot base volumes on first drag (so we scale from user's set levels)
        if not hasattr(self, '_chatmix_snapshot_taken') or not self._chatmix_snapshot_taken:
            vol_data = self.sonar.get_volumes()
            if vol_data:
                self._chatmix_base_game = vol_data.get("game", {}).get("volume", 1.0)
                self._chatmix_base_chat = vol_data.get("chatRender", {}).get("volume", 1.0)
            self._chatmix_snapshot_taken = True

        # Calculate target volumes:
        #   balance < 0 (toward Game): lower Chat
        #   balance > 0 (toward Chat): lower Game
        if balance <= 0:
            game_vol = self._chatmix_base_game
            chat_vol = self._chatmix_base_chat * (1.0 + balance)
        else:
            game_vol = self._chatmix_base_game * (1.0 - balance)
            chat_vol = self._chatmix_base_chat

        game_vol = max(0.0, min(1.0, game_vol))
        chat_vol = max(0.0, min(1.0, chat_vol))

        # Update UI labels immediately
        self._update_chatmix_display(balance)

        # Apply volumes in background
        def do_set():
            self.sonar.set_volume("game", game_vol)
            self.sonar.set_volume("chatRender", chat_vol)
            self._chatmix_dragging = False

        threading.Thread(target=do_set, daemon=True).start()

    def _update_chatmix_display(self, balance: float):
        """Update ChatMix visual indicator based on balance value."""
        if balance < -0.05:
            self._chatmix_game_label.configure(text_color=styles.ACCENT)
            self._chatmix_chat_label.configure(text_color=styles.TEXT_MUTED)
            pct = int(abs(balance) * 100)
            self._chatmix_val_label.configure(
                text=f"\u25C0 Game {pct}%",
                text_color=styles.ACCENT,
            )
        elif balance > 0.05:
            self._chatmix_game_label.configure(text_color=styles.TEXT_MUTED)
            self._chatmix_chat_label.configure(text_color=styles.ACCENT)
            pct = int(abs(balance) * 100)
            self._chatmix_val_label.configure(
                text=f"Chat {pct}% \u25B6",
                text_color=styles.ACCENT,
            )
        else:
            self._chatmix_game_label.configure(text_color=styles.TEXT_DIM)
            self._chatmix_chat_label.configure(text_color=styles.TEXT_DIM)
            self._chatmix_val_label.configure(
                text="Dengeli",
                text_color=styles.TEXT_DIM,
            )

    def _update_chatmix(self, data: dict):
        """Update ChatMix UI from API polling data (hardware dial state)."""
        balance = data.get("balance", 0.0)
        state = data.get("state", "disabled")

        if state != "enabled":
            self._chatmix_status.configure(text="Devre disi", text_color=styles.TEXT_MUTED)
            self._chatmix_slider.set(0)
            self._chatmix_val_label.configure(text="-", text_color=styles.TEXT_MUTED)
            return

        self._chatmix_status.configure(text="", text_color=styles.TEXT_DIM)

        # Don't override slider while user is actively dragging
        if not self._chatmix_dragging:
            # Only sync from hardware if hardware dial actually moved (non-zero)
            if abs(balance) > 0.01:
                self._chatmix_slider.set(balance * 100)
                self._update_chatmix_display(balance)
                # Reset snapshot so next user drag uses fresh volumes
                self._chatmix_snapshot_taken = False

    # ========================
    # Device routing
    # ========================

    def _load_devices(self):
        """Fetch output/input devices and current redirections."""
        self._output_devices = self.devices_client.get_output_devices()
        self._input_devices = self.devices_client.get_input_devices()
        self._redirections = self.devices_client.get_classic_redirections()

    def _create_channel_card(self, channel: str):
        """Card with volume slider + expandable device selector."""
        wrapper = ctk.CTkFrame(self.scroll, fg_color="transparent")
        wrapper.pack(fill="x", padx=4, pady=3)

        # Main card
        card = ctk.CTkFrame(wrapper, fg_color=styles.BG_CARD, corner_radius=10, height=56)
        card.pack(fill="x")
        card.pack_propagate(False)

        # Expand arrow (for device selection) - only for non-master channels
        redirect_key = CHANNEL_TO_REDIRECT.get(channel)
        if redirect_key and self.devices_client:
            expand_btn = ctk.CTkButton(
                card, text="\u25B6", width=20, height=36,
                font=("Segoe UI", 11), fg_color="transparent",
                hover_color=styles.BG_HOVER, text_color=styles.TEXT_MUTED,
                corner_radius=4,
                command=lambda ch=channel: self._toggle_device_dropdown(ch),
            )
            expand_btn.pack(side="left", padx=(4, 0))
            self._expand_states[channel] = False

        # Icon + label
        left = ctk.CTkFrame(card, fg_color="transparent", width=75)
        left.pack(side="left", padx=(8 if not redirect_key else 2, 4))
        left.pack_propagate(False)

        icon = SONAR_CHANNEL_ICONS.get(channel, "\U0001F50A")
        ctk.CTkLabel(
            left, text=f"{icon} {SONAR_CHANNEL_LABELS.get(channel, channel)}",
            font=styles.FONT_BODY, text_color=styles.TEXT, anchor="w",
        ).pack(side="left")

        # Mute button
        mute_btn = ctk.CTkButton(
            card, text="\U0001F50A", width=36, height=36,
            font=("Segoe UI Emoji", 16),
            fg_color="transparent", hover_color=styles.BG_HOVER,
            text_color=styles.TEXT, corner_radius=8,
            command=lambda ch=channel: self._toggle_mute(ch),
        )
        mute_btn.pack(side="right", padx=(4, 10))
        self.mute_buttons[channel] = mute_btn

        # Value label in a fixed wrapper (clickable — opens inline entry for manual input)
        val_frame = ctk.CTkFrame(card, fg_color="transparent", width=44, height=28)
        val_frame.pack(side="right", padx=2)
        val_frame.pack_propagate(False)

        val_label = ctk.CTkLabel(
            val_frame, text="0%", font=styles.FONT_SMALL, text_color=styles.TEXT_DIM,
            cursor="hand2",
        )
        val_label.pack(expand=True)
        val_label.bind("<Button-1>", lambda e, ch=channel: self._start_edit_value(ch))
        self.value_labels[channel] = val_label
        self._value_frames[channel] = val_frame

        # Slider
        slider = ctk.CTkSlider(
            card, from_=0, to=100,
            fg_color=styles.BG_HOVER, progress_color=styles.ACCENT,
            button_color=styles.ACCENT, button_hover_color=styles.ACCENT_HOVER,
            height=16, corner_radius=8,
            command=lambda val, ch=channel: self._on_volume_change(ch, val),
        )
        slider.pack(side="left", fill="x", expand=True, padx=(4, 8))
        slider.set(0)
        self.sliders[channel] = slider

        # Device dropdown frame (hidden initially)
        if redirect_key and self.devices_client:
            dev_frame = ctk.CTkFrame(wrapper, fg_color=styles.BG_MID, corner_radius=8)
            self._device_frames[channel] = dev_frame

    def _toggle_device_dropdown(self, channel: str):
        """Toggle device selector dropdown visibility."""
        expanded = self._expand_states.get(channel, False)
        dev_frame = self._device_frames.get(channel)
        if not dev_frame:
            return

        if expanded:
            dev_frame.pack_forget()
            self._expand_states[channel] = False
        else:
            for w in dev_frame.winfo_children():
                w.destroy()

            redirect_key = CHANNEL_TO_REDIRECT.get(channel, "")
            is_input = channel == "chatCapture"
            devices = self._input_devices if is_input else self._output_devices
            current_dev_id = self._redirections.get(redirect_key, "")

            if not devices:
                ctk.CTkLabel(
                    dev_frame, text="Cihaz bulunamadi",
                    font=styles.FONT_TINY, text_color=styles.TEXT_MUTED,
                ).pack(padx=8, pady=4)
            else:
                for dev in devices:
                    is_active = dev["id"] == current_dev_id
                    name = dev["name"]
                    if len(name) > 40:
                        name = name[:37] + "..."
                    btn = ctk.CTkButton(
                        dev_frame,
                        text=f"{'  \u2713 ' if is_active else '     '}{name}",
                        font=styles.FONT_TINY,
                        fg_color=styles.ACCENT if is_active else "transparent",
                        hover_color=styles.BG_HOVER,
                        text_color=styles.TEXT, anchor="w",
                        height=26, corner_radius=6,
                        command=lambda d=dev["id"], ch=channel, rk=redirect_key: self._change_device(ch, rk, d),
                    )
                    btn.pack(fill="x", padx=4, pady=1)

            dev_frame.pack(fill="x", padx=8, pady=(2, 0))
            self._expand_states[channel] = True

    def _change_device(self, channel: str, redirect_key: str, device_id: str):
        """Change audio device for a channel."""
        self._redirections[redirect_key] = device_id
        self._toggle_device_dropdown(channel)

        def do_change():
            self.devices_client.set_redirection(redirect_key, device_id)

        threading.Thread(target=do_change, daemon=True).start()

    # ========================
    # Inline value editing
    # ========================

    def _start_edit_value(self, channel: str):
        """Replace the percentage label with an editable entry field."""
        # If already editing this channel, ignore
        if self._editing_channel == channel:
            return
        # Close any other active edit first
        if self._editing_channel:
            self._finish_edit_value(self._editing_channel, apply=False)

        self._editing_channel = channel
        label = self.value_labels[channel]
        val_frame = self._value_frames[channel]

        # Get current percentage text (strip %)
        current_text = label.cget("text").replace("%", "").strip()

        # Hide the label inside the wrapper
        label.pack_forget()

        # Create entry inside the same wrapper frame
        entry = ctk.CTkEntry(
            val_frame, width=42, height=26,
            font=styles.FONT_SMALL,
            fg_color=styles.BG_HOVER, border_color=styles.ACCENT,
            text_color=styles.TEXT, border_width=1,
            corner_radius=4, justify="center",
        )
        entry.pack(expand=True, fill="both", padx=1, pady=1)
        entry.insert(0, current_text)
        entry.select_range(0, "end")
        entry.focus_set()

        # Bind keys
        entry.bind("<Return>", lambda e, ch=channel: self._finish_edit_value(ch, apply=True))
        entry.bind("<KP_Enter>", lambda e, ch=channel: self._finish_edit_value(ch, apply=True))
        entry.bind("<Escape>", lambda e, ch=channel: self._finish_edit_value(ch, apply=False))
        entry.bind("<FocusOut>", lambda e, ch=channel: self._finish_edit_value(ch, apply=True))

        self._value_entries[channel] = entry

    def _finish_edit_value(self, channel: str, apply: bool = True):
        """Close the inline entry and optionally apply the typed value."""
        if self._editing_channel != channel:
            return
        entry = self._value_entries.pop(channel, None)
        if not entry or not entry.winfo_exists():
            self._editing_channel = None
            return

        label = self.value_labels[channel]

        if apply:
            raw = entry.get().strip().replace("%", "")
            try:
                val = int(float(raw))
                val = max(0, min(100, val))
            except (ValueError, TypeError):
                val = None

            if val is not None:
                label.configure(text=f"{val}%")
                self.sliders[channel].set(val)
                # Apply via API in background
                threading.Thread(
                    target=self.sonar.set_volume,
                    args=(channel, val / 100.0),
                    daemon=True,
                ).start()

        # Destroy entry, re-show label inside wrapper
        entry.destroy()
        self._editing_channel = None
        label.pack(expand=True)

    # ========================
    # Volume controls
    # ========================

    def _on_volume_change(self, channel: str, value: float):
        if self._updating:
            return
        int_val = int(value)
        self.value_labels[channel].configure(text=f"{int_val}%")
        threading.Thread(
            target=self.sonar.set_volume,
            args=(channel, value / 100.0),
            daemon=True,
        ).start()

    def _toggle_mute(self, channel: str):
        def do_toggle():
            new_state = self.sonar.toggle_mute(channel)
            try:
                if new_state is not None:
                    self.parent.after(0, lambda: self._update_mute_ui(channel, new_state))
            except (RuntimeError, Exception):
                pass  # Panel destroyed

        threading.Thread(target=do_toggle, daemon=True).start()

    def _update_mute_ui(self, channel: str, muted: bool):
        btn = self.mute_buttons[channel]
        if muted:
            btn.configure(text="\U0001F507", text_color=styles.RED)
        else:
            btn.configure(text="\U0001F50A", text_color=styles.TEXT)

    def _poll_volumes(self):
        def do_poll():
            data = self.sonar.get_volumes()
            chatmix = self.sonar.get_chatmix()
            try:
                if data:
                    self.parent.after(0, lambda: self._apply_volume_data(data))
                    self.parent.after(0, lambda: self.status_label.configure(text=""))
                else:
                    self.parent.after(0, lambda: self.status_label.configure(
                        text="Sonar baglantisi kurulamadi", text_color=styles.RED,
                    ))
                if chatmix:
                    self.parent.after(0, lambda: self._update_chatmix(chatmix))
            except (RuntimeError, Exception):
                return  # Panel destroyed — stop silently

        threading.Thread(target=do_poll, daemon=True).start()
        try:
            self.parent.after(3000, self._poll_volumes)
        except (RuntimeError, Exception):
            pass  # Parent destroyed — stop scheduling

    def _apply_volume_data(self, data: dict):
        self._updating = True
        for channel, info in data.items():
            if channel in self.sliders:
                vol_pct = int(info["volume"] * 100)
                self.sliders[channel].set(vol_pct)
                # Don't overwrite the label if user is actively editing this channel
                if self._editing_channel != channel:
                    self.value_labels[channel].configure(text=f"{vol_pct}%")
                self._update_mute_ui(channel, info["muted"])
        self._updating = False
