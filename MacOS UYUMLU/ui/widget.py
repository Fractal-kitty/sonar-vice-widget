import platform
import customtkinter as ctk

from config import WIDGET_WIDTH, WIDGET_HEIGHT
from ui import styles
from ui.styles import THEMES, apply_theme, get_current_theme_name, FONT_TITLE

MIN_W, MIN_H = 320, 300
CORNER_RADIUS = 14

IS_MACOS = platform.system() == "Darwin"


class GGWidget:
    """Main widget - modern, borderless, draggable, always-on-top (macOS compatible)."""

    def __init__(self, root: ctk.CTk, on_quit_callback=None):
        self.root = root
        self._drag_x = 0
        self._drag_y = 0
        self._minimized = False
        self._on_theme_change_cb = None
        self._on_rebuild_cb = None
        self._on_quit = on_quit_callback or root.destroy
        self._hwnd = None

        # Window configuration — start hidden to prevent flash
        root.withdraw()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.95)
        root.configure(fg_color=styles.BG_DARK)

        # Position
        root.update_idletasks()
        sx = root.winfo_screenwidth()
        sy = root.winfo_screenheight()
        root.geometry(f"{WIDGET_WIDTH}x{WIDGET_HEIGHT}+{sx - WIDGET_WIDTH - 30}+{(sy - WIDGET_HEIGHT) // 2}")

        # Platform-specific setup — runs after Tk maps the window
        root.after(50, self._setup_platform)

        # Build UI components
        self._build_title_bar()
        self._build_menu()
        self._build_content()

    # =================================================================
    # UI Construction
    # =================================================================

    def _build_title_bar(self):
        """Build the title bar with hamburger menu, title, and window controls."""
        font_family = styles.FONT_TITLE[0]

        self.title_bar = ctk.CTkFrame(self.root, height=40, fg_color=styles.BG_MID, corner_radius=0)
        self.title_bar.pack(fill="x")
        self.title_bar.pack_propagate(False)

        # Hamburger menu button
        self.menu_btn = ctk.CTkButton(
            self.title_bar, text="\u2630", width=32, height=28,
            font=(font_family, 18), fg_color="transparent",
            hover_color=styles.BG_HOVER, text_color=styles.ACCENT,
            corner_radius=6, command=self._toggle_menu,
        )
        self.menu_btn.pack(side="left", padx=(8, 2))

        # Title
        self._title_label = ctk.CTkLabel(
            self.title_bar, text="Sonar Vice Widget", font=FONT_TITLE,
            text_color=styles.TEXT,
        )
        self._title_label.pack(side="left", padx=4)

        # Close button
        ctk.CTkButton(
            self.title_bar, text="\u2715", width=32, height=28,
            font=(font_family, 15), fg_color="transparent",
            hover_color="#F85149", text_color=styles.TEXT_DIM,
            corner_radius=6, command=self._on_quit,
        ).pack(side="right", padx=(0, 8))

        # Minimize button
        ctk.CTkButton(
            self.title_bar, text="\u2500", width=32, height=28,
            font=(font_family, 15), fg_color="transparent",
            hover_color=styles.ACCENT, text_color=styles.TEXT_DIM,
            corner_radius=6, command=self._toggle_minimize,
        ).pack(side="right", padx=2)

        # Credit label
        ctk.CTkLabel(
            self.title_bar, text="Made by Kingpindev",
            font=(font_family, 10), text_color=styles.TEXT_MUTED,
        ).pack(side="right", padx=(0, 6))

        # Drag bindings
        for w in (self.title_bar, self._title_label):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._do_drag)

    def _build_menu(self):
        """Build the hamburger dropdown menu with theme options."""
        font_family = styles.FONT_TITLE[0]

        self._menu_visible = False
        self._menu_frame = ctk.CTkFrame(
            self.root, fg_color=styles.BG_MID, corner_radius=10,
            border_width=1, border_color=styles.BG_HOVER,
        )
        ctk.CTkLabel(
            self._menu_frame, text="Tema", font=(font_family, 12, "bold"),
            text_color=styles.TEXT_DIM,
        ).pack(anchor="w", padx=12, pady=(10, 4))

        for theme_name in THEMES:
            is_current = theme_name == get_current_theme_name()
            btn = ctk.CTkButton(
                self._menu_frame,
                text=f"{'  \u2713 ' if is_current else '     '}{theme_name}",
                font=(font_family, 12),
                fg_color=styles.ACCENT if is_current else "transparent",
                hover_color=styles.BG_HOVER,
                text_color=styles.TEXT, anchor="w",
                height=30, corner_radius=6,
                command=lambda n=theme_name: self._change_theme(n),
            )
            btn.pack(fill="x", padx=8, pady=1)

    def _build_content(self):
        """Build the main content area with tabview."""
        self.content = ctk.CTkFrame(self.root, fg_color=styles.BG_DARK, corner_radius=0)
        self.content.pack(fill="both", expand=True)

        self.tabview = ctk.CTkTabview(
            self.content,
            fg_color=styles.BG_DARK,
            segmented_button_fg_color=styles.BG_MID,
            segmented_button_selected_color=styles.ACCENT,
            segmented_button_selected_hover_color=styles.ACCENT,
            segmented_button_unselected_color=styles.BG_MID,
            segmented_button_unselected_hover_color=styles.BG_HOVER,
            corner_radius=8,
        )
        self.tabview.pack(fill="both", expand=True, padx=8, pady=(4, 8))

    # =================================================================
    # Live Theme Rebuild
    # =================================================================

    def set_rebuild_callback(self, callback):
        self._on_rebuild_cb = callback

    def rebuild_ui(self):
        self.title_bar.destroy()
        self._menu_frame.destroy()
        self.content.destroy()
        self.root.configure(fg_color=styles.BG_DARK)
        self._build_title_bar()
        self._build_menu()
        self._build_content()
        if self._on_rebuild_cb:
            self._on_rebuild_cb()

    # --- Tabs ---
    def add_tab(self, name: str) -> ctk.CTkFrame:
        self.tabview.add(name)
        return self.tabview.tab(name)

    # --- Hamburger Menu ---
    def _toggle_menu(self):
        if self._menu_visible:
            self._menu_frame.place_forget()
            self._menu_visible = False
        else:
            self._menu_frame.place(x=8, y=42)
            self._menu_frame.lift()
            self._menu_visible = True

    def _change_theme(self, name: str):
        current = get_current_theme_name()
        if name == current:
            self._menu_frame.place_forget()
            self._menu_visible = False
            return
        apply_theme(name)
        self.rebuild_ui()

    def on_theme_change(self, callback):
        self._on_theme_change_cb = callback

    # --- Drag ---
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_x)
        y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    # =================================================================
    # Platform-specific setup
    # =================================================================

    def _setup_platform(self):
        if IS_MACOS:
            self._setup_macos()
        else:
            self._setup_win32()

    def _setup_macos(self):
        """macOS: show window and set floating level."""
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        # macOS Tk floating window style
        try:
            self.root.tk.call("::tk::unsupported::MacWindowStyle",
                              "style", self.root._w, "plain", "none")
        except Exception:
            pass

    def _setup_win32(self):
        """Windows: hide from taskbar + rounded corners."""
        try:
            import ctypes
            GWL_EXSTYLE = -20
            GA_ROOT = 2
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_APPWINDOW = 0x00040000

            _user32 = ctypes.windll.user32

            frame = self.root.winfo_id()
            hwnd = _user32.GetParent(frame)
            if not hwnd:
                hwnd = _user32.GetAncestor(frame, GA_ROOT)
            self._hwnd = hwnd or frame

            ex = _user32.GetWindowLongW(self._hwnd, GWL_EXSTYLE)
            ex |= WS_EX_TOOLWINDOW
            ex &= ~WS_EX_APPWINDOW
            _user32.SetWindowLongW(self._hwnd, GWL_EXSTYLE, ex)
        except Exception:
            self._hwnd = None

        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.after(30, self._apply_rounded_corners)

    def _apply_rounded_corners(self):
        """Clip window to rounded rectangle (Windows only)."""
        if IS_MACOS:
            return
        try:
            import ctypes
            hwnd = self._hwnd
            if not hwnd:
                return
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            r = CORNER_RADIUS
            rgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, r, r)
            ctypes.windll.user32.SetWindowRgn(hwnd, rgn, True)
        except Exception:
            pass

    # --- Show / Hide ---
    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)

    def hide(self):
        self.root.withdraw()

    # --- Minimize ---
    def _toggle_minimize(self):
        if self._minimized:
            self.content.pack(fill="both", expand=True)
            self.root.geometry(f"{self.root.winfo_width()}x{WIDGET_HEIGHT}")
            self._minimized = False
        else:
            self.content.pack_forget()
            self.root.geometry(f"{self.root.winfo_width()}x40")
            self._minimized = True
        if not IS_MACOS:
            self.root.after(30, self._apply_rounded_corners)
