import customtkinter as ctk
import threading

from config import SONAR_DEVICE_LABELS
from ui import styles
from ui.styles import FONT_BODY, FONT_SECTION, FONT_SMALL, FONT_TINY


DEVICE_ICONS = {
    "game": "\U0001F3AE",
    "chatRender": "\U0001F3A7",
    "chatCapture": "\U0001F399",
    "media": "\U0001F3B5",
    "aux": "\U0001F50A",
}

DEVICE_ORDER = ["game", "chatRender", "chatCapture", "media", "aux"]


class _ToggleDropdown:
    """Custom dropdown that properly toggles open/close on click."""

    def __init__(self, card, button_parent, values, current, on_change):
        self._card = card
        self._values = values
        self._current = current
        self._on_change = on_change
        self._open = False

        # Main button (looks like a dropdown selector)
        display = current if current else "Sec..."
        self._btn = ctk.CTkButton(
            button_parent,
            text=f"  {display}  \u25BE",
            font=FONT_SMALL,
            fg_color=styles.BG_MID,
            hover_color=styles.BG_HOVER,
            text_color=styles.TEXT,
            anchor="w",
            height=32,
            corner_radius=8,
            command=self._toggle,
        )
        self._btn.pack(side="left", fill="x", expand=True)

        # Dropdown options frame (hidden, placed inside card below button)
        # Height calculated dynamically on open based on number of items
        self._options_frame = None  # lazy-created

    def _toggle(self):
        if self._open:
            self.close()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        """Build option buttons and show the dropdown."""
        # Destroy previous frame if exists
        if self._options_frame is not None:
            self._options_frame.destroy()

        # Calculate height: 30px per item, max 180px
        item_h = 30
        calc_h = min(len(self._values) * item_h + 8, 180)
        use_scroll = len(self._values) > 5

        if use_scroll:
            self._options_frame = ctk.CTkScrollableFrame(
                self._card, fg_color=styles.BG_MID, corner_radius=8,
                height=calc_h,
                scrollbar_button_color=styles.BG_CARD,
                scrollbar_button_hover_color=styles.ACCENT,
            )
        else:
            self._options_frame = ctk.CTkFrame(
                self._card, fg_color=styles.BG_MID, corner_radius=8,
            )

        for val in self._values:
            is_active = val == self._current
            btn = ctk.CTkButton(
                self._options_frame,
                text=f"{'  \u2713 ' if is_active else '     '}{val}",
                font=FONT_SMALL,
                fg_color=styles.ACCENT if is_active else "transparent",
                hover_color=styles.BG_HOVER,
                text_color=styles.TEXT,
                anchor="w",
                height=28,
                corner_radius=6,
                command=lambda v=val: self._select(v),
            )
            btn.pack(fill="x", padx=4, pady=1)

        self._options_frame.pack(fill="x", padx=10, pady=(0, 8))
        self._btn.configure(text=f"  {self._current or 'Sec...'}  \u25B4")
        self._open = True

    def close(self):
        """Hide the dropdown."""
        if self._open:
            if self._options_frame is not None:
                self._options_frame.destroy()
                self._options_frame = None
            self._btn.configure(text=f"  {self._current or 'Sec...'}  \u25BE")
            self._open = False

    def _select(self, val):
        """Handle option selection."""
        self._current = val
        self._btn.configure(text=f"  {val}  \u25BE")
        self.close()
        if self._on_change:
            self._on_change(val)

    def set(self, val):
        """Set current value without triggering callback."""
        self._current = val
        self._btn.configure(text=f"  {val}  \u25BE")

    def update_values(self, values, current=None):
        """Update the list of available values."""
        self._values = values
        if current is not None:
            self._current = current
            self._btn.configure(text=f"  {current}  \u25BE")


class EQPanel:
    """EQ profile switcher with toggle dropdown selectors per device."""

    def __init__(self, parent: ctk.CTkFrame, presets_client):
        self.parent = parent
        self.presets = presets_client
        self._all_configs = {}
        self._fav_configs = {}
        self._selected = {}
        self._dropdowns = {}        # device -> _ToggleDropdown
        self._active_labels = {}
        self._name_to_id = {}
        self._show_all = False

        parent.configure(fg_color=styles.BG_DARK)

        # === Header row ===
        header = ctk.CTkFrame(parent, fg_color=styles.BG_DARK, height=36)
        header.pack(fill="x", padx=8, pady=(6, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="EQ Profiles", font=FONT_SECTION, text_color=styles.TEXT,
        ).pack(side="left", padx=4)

        self.refresh_btn = ctk.CTkButton(
            header, text="\u21BB", width=32, height=28,
            font=("Segoe UI", 14), fg_color="transparent",
            hover_color=styles.BG_HOVER, text_color=styles.TEXT_DIM,
            corner_radius=6, command=self._refresh_data,
        )
        self.refresh_btn.pack(side="right")

        # === Show all checkbox ===
        checkbox_row = ctk.CTkFrame(parent, fg_color=styles.BG_DARK, height=28)
        checkbox_row.pack(fill="x", padx=12, pady=(4, 2))
        checkbox_row.pack_propagate(False)

        self._show_all_var = ctk.BooleanVar(value=False)
        self.show_all_cb = ctk.CTkCheckBox(
            checkbox_row, text="Tum profilleri goster",
            font=FONT_SMALL, text_color=styles.TEXT_DIM,
            fg_color=styles.ACCENT, hover_color=styles.ACCENT_HOVER,
            border_color=styles.BG_HOVER, checkmark_color=styles.TEXT,
            corner_radius=4, height=22,
            variable=self._show_all_var,
            command=self._on_show_all_toggle,
        )
        self.show_all_cb.pack(side="left")

        # === Scrollable content ===
        self.scroll = ctk.CTkScrollableFrame(
            parent, fg_color=styles.BG_DARK, corner_radius=0,
            scrollbar_button_color=styles.BG_CARD,
            scrollbar_button_hover_color=styles.ACCENT,
        )
        self.scroll.pack(fill="both", expand=True, padx=2, pady=2)

        # === Status ===
        self.status_label = ctk.CTkLabel(
            parent, text="", font=FONT_TINY, text_color=styles.TEXT_DIM,
        )
        self.status_label.pack(pady=(0, 4))

        # Load data
        self._refresh_data()

    def _on_show_all_toggle(self):
        """Toggle between favorites-only and all profiles."""
        self._show_all = self._show_all_var.get()
        self._rebuild_dropdowns()

    def _refresh_data(self):
        """Fetch all configs and selected in background."""
        self.status_label.configure(text="Yukleniyor...", text_color=styles.YELLOW)

        def do_fetch():
            all_cfgs = self.presets.get_configs_by_device(favorites_only=False)
            fav_cfgs = self.presets.get_configs_by_device(favorites_only=True)
            selected = self.presets.get_selected_configs()
            try:
                self.parent.after(0, lambda: self._on_data_loaded(all_cfgs, fav_cfgs, selected))
            except (RuntimeError, Exception):
                pass  # Panel destroyed

        threading.Thread(target=do_fetch, daemon=True).start()

    def _on_data_loaded(self, all_cfgs, fav_cfgs, selected):
        """Store data and build UI."""
        if all_cfgs is None:
            self.status_label.configure(text="Sonar baglantisi yok", text_color=styles.RED)
            return

        self._all_configs = all_cfgs
        self._fav_configs = fav_cfgs or {}
        self._selected = selected or {}
        self._rebuild_dropdowns()

    def _rebuild_dropdowns(self):
        """Clear and rebuild all device sections based on current mode."""
        # Close any open dropdowns before destroying
        for dd in self._dropdowns.values():
            dd.close()

        for w in self.scroll.winfo_children():
            w.destroy()
        self._dropdowns.clear()
        self._active_labels.clear()
        self._name_to_id.clear()

        configs = self._all_configs if self._show_all else self._fav_configs

        if not configs:
            msg = "Profil bulunamadi." if self._show_all else \
                  "Favori profil yok.\nSonar'da profilleri favorilere ekleyin."
            ctk.CTkLabel(
                self.scroll, text=msg, font=FONT_BODY,
                text_color=styles.TEXT_DIM, justify="center",
            ).pack(pady=30)
            self.status_label.configure(text="", text_color=styles.TEXT_DIM)
            return

        for device in DEVICE_ORDER:
            device_cfgs = configs.get(device, [])
            if not device_cfgs:
                continue
            self._create_device_card(device, device_cfgs)

        total = sum(len(v) for v in configs.values())
        mode = "profil" if self._show_all else "favori"
        self.status_label.configure(
            text=f"{total} {mode} yuklendi", text_color=styles.TEXT_DIM,
        )

    def _create_device_card(self, device: str, configs: list[dict]):
        """Create a card with device label + toggle dropdown selector."""
        card = ctk.CTkFrame(self.scroll, fg_color=styles.BG_CARD, corner_radius=12)
        card.pack(fill="x", padx=4, pady=4)

        icon = DEVICE_ICONS.get(device, "\U0001F50A")
        label = SONAR_DEVICE_LABELS.get(device, device)
        selected_name = self._selected.get(device, {}).get("name", "")

        # Header row: icon + device name + active indicator
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            header, text=f"{icon}  {label}", font=FONT_SECTION, text_color=styles.TEXT,
        ).pack(side="left")

        active_label = ctk.CTkLabel(
            header, text=f"\u2713 {selected_name}" if selected_name else "",
            font=FONT_TINY, text_color=styles.GREEN,
        )
        active_label.pack(side="right")
        self._active_labels[device] = active_label

        # Dropdown row
        dropdown_row = ctk.CTkFrame(card, fg_color="transparent")
        dropdown_row.pack(fill="x", padx=14, pady=(2, 4))

        # Build name list and mapping
        name_map = {}
        names = []
        for cfg in configs:
            display = cfg["name"]
            if self._show_all and cfg.get("isFavorite"):
                display = f"\u2605 {display}"
            name_map[display] = cfg["id"]
            names.append(display)

        self._name_to_id[device] = name_map

        # Find current selection in the list
        current_display = None
        selected_id = self._selected.get(device, {}).get("id", "")
        for display, cid in name_map.items():
            if cid == selected_id:
                current_display = display
                break

        # Create toggle dropdown
        dd = _ToggleDropdown(
            card=card,
            button_parent=dropdown_row,
            values=names,
            current=current_display or (names[0] if names else ""),
            on_change=lambda val, dev=device: self._on_dropdown_change(dev, val),
        )
        self._dropdowns[device] = dd

    def _on_dropdown_change(self, device: str, display_name: str):
        """Handle dropdown selection change."""
        name_map = self._name_to_id.get(device, {})
        config_id = name_map.get(display_name)
        if not config_id:
            return

        # Update active label immediately
        clean_name = display_name.lstrip("\u2605 ")
        if device in self._active_labels:
            self._active_labels[device].configure(text=f"\u2713 {clean_name}")

        def do_select():
            success = self.presets.select_config(config_id)
            try:
                if success:
                    selected = self.presets.get_selected_configs()
                    if selected:
                        self.parent.after(0, lambda: self._update_selected(selected))
                    self.parent.after(
                        0,
                        lambda: self.status_label.configure(
                            text=f"{clean_name} aktif", text_color=styles.GREEN,
                        ),
                    )
                else:
                    self.parent.after(
                        0,
                        lambda: self.status_label.configure(
                            text="Degistirilemedi", text_color=styles.RED,
                        ),
                    )
            except (RuntimeError, Exception):
                pass  # Panel destroyed

        threading.Thread(target=do_select, daemon=True).start()

    def _update_selected(self, selected: dict):
        """Update internal state after a selection."""
        self._selected = selected
        for device, info in selected.items():
            if device in self._active_labels:
                self._active_labels[device].configure(
                    text=f"\u2713 {info.get('name', '')}"
                )
