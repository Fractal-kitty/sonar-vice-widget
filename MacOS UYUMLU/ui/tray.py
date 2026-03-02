"""System tray integration using pystray + Pillow (macOS compatible)."""

import sys
import os
import platform
import threading

IS_MACOS = platform.system() == "Darwin"

try:
    import pystray
    from PIL import Image, ImageDraw
    _HAS_TRAY = True
except ImportError:
    _HAS_TRAY = False


def _create_icon_image():
    """Create a SteelSeries-style orange icon programmatically."""
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([1, 1, size - 1, size - 1], fill='#1C2333')
    draw.ellipse([4, 4, size - 4, size - 4], outline='#FF6600', width=5)
    draw.ellipse([20, 20, size - 20, size - 20], fill='#FF6600')
    return img


class SystemTray:
    """System tray icon — left-click toggles widget, right-click shows menu."""

    def __init__(self, root, widget, on_quit, on_restart=None):
        self.root = root
        self._widget = widget
        self._on_quit = on_quit
        self._on_restart = on_restart
        self._visible = True
        self._topmost = True

        if not _HAS_TRAY:
            print("pystray/Pillow not found — system tray disabled.")
            return

        menu = pystray.Menu(
            pystray.MenuItem(
                "Show/Hide",
                self._toggle_visibility,
                default=True,
                visible=False,
            ),
            pystray.MenuItem(
                "Always on Top",
                self._toggle_topmost,
                checked=lambda item: self._topmost,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("\U0001F504  Restart", self._restart),
            pystray.MenuItem("\u274C  Quit", self._quit),
        )

        self._icon = pystray.Icon(
            "sonar_vice_widget",
            _create_icon_image(),
            "Sonar Vice Widget",
            menu,
        )

        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def _toggle_visibility(self):
        if self._visible:
            self.root.after(0, self._hide_window)
        else:
            self.root.after(0, self._show_window)

    def _hide_window(self):
        self._widget.hide()
        self._visible = False

    def _show_window(self):
        self._widget.show()
        self._visible = True

    def _toggle_topmost(self):
        self._topmost = not self._topmost
        self.root.after(0, lambda: self.root.attributes("-topmost", self._topmost))

    def _restart(self):
        try:
            self._icon.stop()
        except Exception:
            pass
        self.root.after(0, self._do_restart)

    def _do_restart(self):
        if self._on_restart:
            self._on_restart()
        self.root.destroy()

        python = sys.executable
        if getattr(sys, 'frozen', False):
            os.execv(python, sys.argv)
        else:
            os.execv(python, [python] + sys.argv)

    def _quit(self):
        try:
            self._icon.stop()
        except Exception:
            pass
        self.root.after(0, self._on_quit)

    def stop(self):
        if _HAS_TRAY:
            try:
                self._icon.stop()
            except Exception:
                pass
