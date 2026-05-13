"""
Window management module - Windows & Ubuntu Desktop
"""

import platform
import subprocess
from typing import List, Dict, Optional

PLATFORM = platform.system()


class WindowManager:

    def list_windows(self) -> List[Dict]:
        """List all visible windows."""
        if PLATFORM == "Windows":
            return self._list_windows_windows()
        elif PLATFORM == "Linux":
            return self._list_windows_linux()
        raise RuntimeError(f"Platform '{PLATFORM}' not supported.")

    def _list_windows_windows(self) -> List[Dict]:
        try:
            import pygetwindow as gw
        except ImportError:
            raise RuntimeError("Install pygetwindow: pip install pygetwindow")

        windows = []
        for w in gw.getAllWindows():
            if w.title.strip():
                windows.append({
                    "id": str(w._hWnd),
                    "title": w.title,
                    "app": w.title.split("-")[-1].strip(),
                    "x": w.left, "y": w.top,
                    "width": w.width, "height": w.height,
                    "visible": w.visible,
                })
        return windows

    def _list_windows_linux(self) -> List[Dict]:
        try:
            result = subprocess.run(
                ["xdotool", "search", "--onlyvisible", "--name", ""],
                capture_output=True, text=True
            )
            wids = result.stdout.strip().splitlines()
        except FileNotFoundError:
            raise RuntimeError("Install xdotool: sudo apt install xdotool")

        windows = []
        for wid in wids:
            try:
                name_r = subprocess.run(
                    ["xdotool", "getwindowname", wid],
                    capture_output=True, text=True
                )
                geo_r = subprocess.run(
                    ["xdotool", "getwindowgeometry", "--shell", wid],
                    capture_output=True, text=True
                )
                name = name_r.stdout.strip()
                props = {}
                for line in geo_r.stdout.strip().splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        props[k.strip()] = v.strip()

                if name:
                    windows.append({
                        "id": wid,
                        "title": name,
                        "app": name,
                        "x": int(props.get("X", 0)),
                        "y": int(props.get("Y", 0)),
                        "width": int(props.get("WIDTH", 0)),
                        "height": int(props.get("HEIGHT", 0)),
                    })
            except Exception:
                continue

        return windows

    def focus_window(self, app_name: str):
        """Bring a window to focus by name."""
        if PLATFORM == "Windows":
            try:
                import pygetwindow as gw
            except ImportError:
                raise RuntimeError("Install pygetwindow: pip install pygetwindow")
            windows = gw.getWindowsWithTitle(app_name)
            if not windows:
                raise ValueError(f"No window found: '{app_name}'")
            windows[0].activate()

        elif PLATFORM == "Linux":
            result = subprocess.run(
                ["xdotool", "search", "--name", app_name],
                capture_output=True, text=True
            )
            if not result.stdout.strip():
                raise ValueError(f"No window found: '{app_name}'")
            wid = result.stdout.strip().split("\n")[0]
            subprocess.run(["xdotool", "windowactivate", "--sync", wid])

    def resize_window(self, app_name: str, width: int, height: int):
        """Resize a window by name."""
        if PLATFORM == "Windows":
            try:
                import pygetwindow as gw
            except ImportError:
                raise RuntimeError("Install pygetwindow: pip install pygetwindow")
            windows = gw.getWindowsWithTitle(app_name)
            if not windows:
                raise ValueError(f"No window found: '{app_name}'")
            windows[0].resizeTo(width, height)

        elif PLATFORM == "Linux":
            result = subprocess.run(
                ["xdotool", "search", "--name", app_name],
                capture_output=True, text=True
            )
            if not result.stdout.strip():
                raise ValueError(f"No window found: '{app_name}'")
            wid = result.stdout.strip().split("\n")[0]
            subprocess.run(["xdotool", "windowsize", wid, str(width), str(height)])

    def move_window(self, app_name: str, x: int, y: int):
        """Move a window to (x, y)."""
        if PLATFORM == "Windows":
            try:
                import pygetwindow as gw
            except ImportError:
                raise RuntimeError("Install pygetwindow: pip install pygetwindow")
            windows = gw.getWindowsWithTitle(app_name)
            if not windows:
                raise ValueError(f"No window found: '{app_name}'")
            windows[0].moveTo(x, y)

        elif PLATFORM == "Linux":
            result = subprocess.run(
                ["xdotool", "search", "--name", app_name],
                capture_output=True, text=True
            )
            if not result.stdout.strip():
                raise ValueError(f"No window found: '{app_name}'")
            wid = result.stdout.strip().split("\n")[0]
            subprocess.run(["xdotool", "windowmove", wid, str(x), str(y)])

    def minimize_window(self, app_name: str):
        """Minimize a window."""
        if PLATFORM == "Windows":
            try:
                import pygetwindow as gw
                windows = gw.getWindowsWithTitle(app_name)
                if windows:
                    windows[0].minimize()
            except ImportError:
                raise RuntimeError("Install pygetwindow: pip install pygetwindow")
        elif PLATFORM == "Linux":
            result = subprocess.run(
                ["xdotool", "search", "--name", app_name],
                capture_output=True, text=True
            )
            if result.stdout.strip():
                wid = result.stdout.strip().split("\n")[0]
                subprocess.run(["xdotool", "windowminimize", wid])

    def maximize_window(self, app_name: str):
        """Maximize a window."""
        if PLATFORM == "Windows":
            try:
                import pygetwindow as gw
                windows = gw.getWindowsWithTitle(app_name)
                if windows:
                    windows[0].maximize()
            except ImportError:
                raise RuntimeError("Install pygetwindow: pip install pygetwindow")
        elif PLATFORM == "Linux":
            result = subprocess.run(
                ["xdotool", "search", "--name", app_name],
                capture_output=True, text=True
            )
            if result.stdout.strip():
                wid = result.stdout.strip().split("\n")[0]
                subprocess.run([
                    "wmctrl", "-ir", wid, "-b", "add,maximized_vert,maximized_horz"
                ])
