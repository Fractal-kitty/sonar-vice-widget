import customtkinter as ctk
import threading

from ui import styles
from ui.styles import FONT_BODY, FONT_SECTION, FONT_SMALL


class RGBPanel:
    def __init__(self, parent: ctk.CTkFrame, gamesense_client):
        self.parent = parent
        self.gs = gamesense_client
        self._font_family = styles.FONT_TITLE[0]

        parent.configure(fg_color=styles.BG_DARK)
        scroll = ctk.CTkScrollableFrame(
            parent, fg_color=styles.BG_DARK, corner_radius=0,
            scrollbar_button_color=styles.BG_CARD, scrollbar_button_hover_color=styles.ACCENT)
        scroll.pack(fill="both", expand=True, padx=2, pady=2)

        rgb_card = ctk.CTkFrame(scroll, fg_color=styles.BG_CARD, corner_radius=12)
        rgb_card.pack(fill="x", padx=4, pady=4)
        ctk.CTkLabel(rgb_card, text="\U0001F3A8  RGB Lighting", font=FONT_SECTION,
                     text_color=styles.TEXT).pack(anchor="w", padx=16, pady=(12, 8))

        if not self.gs:
            ctk.CTkLabel(rgb_card, text="GameSense baglantisi yok",
                         font=FONT_SMALL, text_color=styles.RED).pack(pady=(0, 16))
            return

        rgb_inner = ctk.CTkFrame(rgb_card, fg_color="transparent")
        rgb_inner.pack(fill="x", padx=16, pady=(0, 12))

        self.r_var = ctk.IntVar(value=255)
        self.g_var = ctk.IntVar(value=102)
        self.b_var = ctk.IntVar(value=0)

        self._create_color_slider(rgb_inner, "R", "#FF4444", self.r_var)
        self._create_color_slider(rgb_inner, "G", "#44FF44", self.g_var)
        self._create_color_slider(rgb_inner, "B", "#4488FF", self.b_var)

        bottom = ctk.CTkFrame(rgb_inner, fg_color="transparent")
        bottom.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(bottom, text="Preview", font=FONT_SMALL, text_color=styles.TEXT_DIM).pack(side="left")
        self.preview_frame = ctk.CTkFrame(
            bottom, width=40, height=24, corner_radius=6,
            fg_color="#FF6600", border_width=1, border_color="#444")
        self.preview_frame.pack(side="left", padx=8)
        self.preview_frame.pack_propagate(False)
        ctk.CTkButton(bottom, text="Apply", width=80, height=28, font=FONT_BODY,
                      fg_color=styles.ACCENT, hover_color=styles.ACCENT_HOVER,
                      text_color=styles.TEXT, corner_radius=8,
                      command=self._send_color).pack(side="right")

        preset_frame = ctk.CTkFrame(rgb_inner, fg_color="transparent")
        preset_frame.pack(fill="x", pady=(8, 0))
        presets = [("Orange", 255, 102, 0), ("Red", 255, 0, 0), ("Blue", 0, 100, 255),
                   ("Green", 0, 255, 0), ("White", 255, 255, 255), ("Off", 0, 0, 0)]
        for name, r, g, b in presets:
            ctk.CTkButton(preset_frame, text=name, width=50, height=26, font=FONT_SMALL,
                          fg_color=styles.BG_HOVER, hover_color=styles.ACCENT,
                          text_color=styles.TEXT, corner_radius=6,
                          command=lambda r=r, g=g, b=b: self._apply_preset(r, g, b)).pack(side="left", padx=2)

        for var in (self.r_var, self.g_var, self.b_var):
            var.trace_add("write", lambda *_: self._update_preview())

    def _create_color_slider(self, parent, label: str, color: str, var: ctk.IntVar):
        row = ctk.CTkFrame(parent, fg_color="transparent", height=30)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)
        ctk.CTkLabel(row, text=label, font=(self._font_family, 12, "bold"),
                     text_color=color, width=22).pack(side="left")
        slider = ctk.CTkSlider(
            row, from_=0, to=255, variable=var, fg_color=styles.BG_HOVER,
            progress_color=color, button_color=color, button_hover_color="#FFFFFF",
            height=14, corner_radius=7)
        slider.pack(side="left", fill="x", expand=True, padx=8)
        ctk.CTkLabel(row, textvariable=var, font=FONT_SMALL,
                     text_color=styles.TEXT_DIM, width=30).pack(side="right")

    def _update_preview(self):
        try:
            r, g, b = self.r_var.get(), self.g_var.get(), self.b_var.get()
            self.preview_frame.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}")
        except Exception:
            pass

    def _apply_preset(self, r: int, g: int, b: int):
        self.r_var.set(r)
        self.g_var.set(g)
        self.b_var.set(b)
        self._send_color()

    def _send_color(self):
        if not self.gs:
            return
        r, g, b = self.r_var.get(), self.g_var.get(), self.b_var.get()
        threading.Thread(target=self.gs.send_color, args=(r, g, b), daemon=True).start()
