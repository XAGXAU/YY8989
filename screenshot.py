"""
Screenshot capture module - Windows & Ubuntu Desktop support
Uses mss (cross-platform) with platform-specific window capture helpers.
"""

import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

import mss
from PIL import Image

PLATFORM = platform.system()  # "Windows" | "Linux"


def _default_save_path(suffix: str = "") -> str:
    desktop = Path.home() / "Desktop"
    desktop.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    return str(desktop / f"peekaboo_{ts}{suffix}.png")


def _sct_to_pil(sct_img) -> Image.Image:
    """
    Safely convert mss ScreenShot (BGRA) to PIL RGB Image.
    Avoids frombytes raw decoder mode fragility across Pillow versions.
    """
    img_rgba = Image.frombytes("RGBA", sct_img.size, bytes(sct_img.bgra))
    r, g, b, _a = img_rgba.split()
    return Image.merge("RGB", (b, g, r))


def _grab_and_save(bbox: dict, save_path: str, retina: bool = False) -> Image.Image:
    with mss.mss() as sct:
        sct_img = sct.grab(bbox)
        img = _sct_to_pil(sct_img)
    if retina:
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    img.save(save_path)
    return img


class ScreenshotManager:

    def capture_screen(
        self,
        screen_index: int = 0,
        retina: bool = False,
        save_path: Optional[str] = None,
    ) -> Tuple[str, dict]:
        """Capture an entire monitor by index (0 = primary)."""
        save_path = save_path or _default_save_path("_screen")
        save_path = os.path.expanduser(save_path)

        with mss.mss() as sct:
            monitors = sct.monitors  # [0]=all combined, [1+]=individual
            idx = screen_index + 1
            if idx >= len(monitors):
                raise ValueError(
                    f"Screen index {screen_index} not found. "
                    f"Available: 0–{len(monitors) - 2}"
                )
            bbox = monitors[idx]

        img = _grab_and_save(bbox, save_path, retina)
        return save_path, {
            "width": img.width, "height": img.height,
            "screen_index": screen_index, "platform": PLATFORM,
        }

    def capture_window(
        self,
        app_name: str,
        retina: bool = False,
        save_path: Optional[str] = None,
    ) -> Tuple[str, dict]:
        """Capture a specific application window by its title."""
        save_path = save_path or _default_save_path(f"_{app_name.replace(' ', '_')}")
        save_path = os.path.expanduser(save_path)

        if PLATFORM == "Windows":
            return self._capture_window_windows(app_name, retina, save_path)
        elif PLATFORM == "Linux":
            return self._capture_window_linux(app_name, retina, save_path)
        else:
            raise RuntimeError(f"Platform '{PLATFORM}' not supported. Use Windows or Linux.")

    def _capture_window_windows(self, app_name: str, retina: bool, save_path: str):
        try:
            import pygetwindow as gw
        except ImportError:
            raise RuntimeError("Install pygetwindow: pip install pygetwindow")

        windows = gw.getWindowsWithTitle(app_name)
        if not windows:
            all_titles = [w.title for w in gw.getAllWindows() if w.title.strip()]
            raise ValueError(
                f"No window matching '{app_name}'. Open windows: {all_titles[:10]}"
            )

        win = windows[0]
        win.activate()
        time.sleep(0.4)

        if win.width <= 0 or win.height <= 0:
            raise ValueError(f"Window '{app_name}' is minimised or has no size.")

        bbox = {
            "left": max(0, win.left), "top": max(0, win.top),
            "width": win.width, "height": win.height,
        }
        img = _grab_and_save(bbox, save_path, retina)
        return save_path, {
            "window": win.title, "width": img.width,
            "height": img.height, "platform": PLATFORM,
        }

    def _capture_window_linux(self, app_name: str, retina: bool, save_path: str):
        result = subprocess.run(
            ["xdotool", "search", "--name", app_name],
            capture_output=True, text=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise ValueError(
                f"No window matching '{app_name}'. "
                "Install xdotool: sudo apt install xdotool"
            )

        wid = result.stdout.strip().splitlines()[0]
        subprocess.run(["xdotool", "windowactivate", "--sync", wid], check=False)
        time.sleep(0.4)

        geo = subprocess.run(
            ["xdotool", "getwindowgeometry", "--shell", wid],
            capture_output=True, text=True,
        )
        props: dict = {}
        for line in geo.stdout.strip().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                props[k.strip()] = v.strip()

        x, y = int(props.get("X", 0)), int(props.get("Y", 0))
        w, h = int(props.get("WIDTH", 0)), int(props.get("HEIGHT", 0))

        if w <= 0 or h <= 0:
            raise ValueError(f"Window '{app_name}' has invalid size ({w}x{h}).")

        img = _grab_and_save({"left": x, "top": y, "width": w, "height": h}, save_path, retina)
        return save_path, {
            "window_id": wid, "window_name": app_name,
            "width": img.width, "height": img.height, "platform": PLATFORM,
        }

    def capture_area(self, save_path: Optional[str] = None) -> Tuple[str, dict]:
        """Interactive area selection. Linux tries slop first, falls back to tkinter."""
        save_path = save_path or _default_save_path("_area")
        save_path = os.path.expanduser(save_path)

        if PLATFORM == "Linux":
            try:
                return self._capture_area_slop(save_path)
            except Exception:
                pass

        return self._capture_area_tkinter(save_path)

    def _capture_area_slop(self, save_path: str):
        result = subprocess.run(["slop", "-f", "%x %y %w %h"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("slop not available")
        x, y, w, h = map(int, result.stdout.strip().split())
        img = _grab_and_save({"left": x, "top": y, "width": w, "height": h}, save_path)
        return save_path, {"x": x, "y": y, "width": w, "height": h}

    def _capture_area_tkinter(self, save_path: str):
        import tkinter as tk

        root = tk.Tk()
        root.attributes("-fullscreen", True)
        root.attributes("-alpha", 0.25)
        root.configure(bg="grey10")
        root.attributes("-topmost", True)

        coords: dict = {"x1": 0, "y1": 0, "x2": 0, "y2": 0}
        canvas = tk.Canvas(root, cursor="cross", bg="grey10", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        rect_id = None

        def on_press(e):
            coords["x1"], coords["y1"] = e.x_root, e.y_root

        def on_drag(e):
            nonlocal rect_id
            if rect_id:
                canvas.delete(rect_id)
            rx = coords["x1"] - root.winfo_rootx()
            ry = coords["y1"] - root.winfo_rooty()
            rect_id = canvas.create_rectangle(
                rx, ry,
                e.x_root - root.winfo_rootx(),
                e.y_root - root.winfo_rooty(),
                outline="red", width=2,
            )

        def on_release(e):
            coords["x2"], coords["y2"] = e.x_root, e.y_root
            root.destroy()

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        root.bind("<Escape>", lambda _e: root.destroy())
        root.mainloop()

        x1 = min(coords["x1"], coords["x2"])
        y1 = min(coords["y1"], coords["y2"])
        x2 = max(coords["x1"], coords["x2"])
        y2 = max(coords["y1"], coords["y2"])
        w, h = x2 - x1, y2 - y1

        if w < 10 or h < 10:
            raise ValueError("Selection too small (minimum 10×10 px).")

        img = _grab_and_save({"left": x1, "top": y1, "width": w, "height": h}, save_path)
        return save_path, {"x": x1, "y": y1, "width": w, "height": h}
