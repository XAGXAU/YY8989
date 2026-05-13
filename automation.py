"""
GUI Automation module - Windows & Ubuntu Desktop
Uses pyautogui for cross-platform mouse/keyboard control
"""

import platform
import time
from typing import Optional

PLATFORM = platform.system()


class AutomationManager:

    def __init__(self):
        try:
            import pyautogui
            pyautogui.FAILSAFE = True   # Move mouse to top-left corner to abort
            pyautogui.PAUSE = 0.1       # Small delay between actions
            self.pag = pyautogui
        except ImportError:
            raise RuntimeError("Install pyautogui: pip install pyautogui")

    def click(self, x: int, y: int, click_type: str = "left"):
        """Click at screen coordinates."""
        self.pag.moveTo(x, y, duration=0.2)
        if click_type == "left":
            self.pag.click(x, y)
        elif click_type == "right":
            self.pag.rightClick(x, y)
        elif click_type == "double":
            self.pag.doubleClick(x, y)
        elif click_type == "middle":
            self.pag.middleClick(x, y)

    def type_text(self, text: str, interval: float = 0.05):
        """Type text with keyboard simulation."""
        self.pag.typewrite(text, interval=interval)

    def hotkey(self, *keys: str):
        """Press a keyboard shortcut. e.g. hotkey('ctrl', 'c')"""
        self.pag.hotkey(*keys)

    def press(self, key: str, presses: int = 1, interval: float = 0.1):
        """Press a single key."""
        self.pag.press(key, presses=presses, interval=interval)

    def scroll(
        self,
        direction: str = "down",
        amount: int = 3,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ):
        """Scroll mouse wheel."""
        if x is not None and y is not None:
            self.pag.moveTo(x, y, duration=0.2)

        if direction == "down":
            self.pag.scroll(-amount)
        elif direction == "up":
            self.pag.scroll(amount)
        elif direction == "left":
            self.pag.hscroll(-amount)
        elif direction == "right":
            self.pag.hscroll(amount)

    def move(self, x: int, y: int, duration: float = 0.2):
        """Move mouse cursor to coordinates."""
        self.pag.moveTo(x, y, duration=duration)

    def drag(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        duration: float = 0.5,
        button: str = "left",
    ):
        """Drag from one position to another."""
        self.pag.moveTo(x1, y1, duration=0.2)
        self.pag.dragTo(x2, y2, duration=duration, button=button)

    def get_mouse_pos(self):
        """Get current mouse cursor position."""
        return self.pag.position()

    def screenshot_region(self, x: int, y: int, w: int, h: int):
        """Take a screenshot of a region (returns PIL Image)."""
        return self.pag.screenshot(region=(x, y, w, h))

    def write_clipboard(self, text: str):
        """Write text to clipboard."""
        if PLATFORM == "Windows":
            import subprocess
            subprocess.run(["clip"], input=text.encode(), check=True)
        elif PLATFORM == "Linux":
            try:
                import subprocess
                subprocess.run(["xclip", "-selection", "clipboard"],
                               input=text.encode(), check=True)
            except FileNotFoundError:
                subprocess.run(["xsel", "--clipboard", "--input"],
                               input=text.encode(), check=True)

    def read_clipboard(self) -> str:
        """Read text from clipboard."""
        if PLATFORM == "Windows":
            import subprocess
            result = subprocess.run(["powershell", "-command", "Get-Clipboard"],
                                    capture_output=True, text=True)
            return result.stdout.strip()
        elif PLATFORM == "Linux":
            import subprocess
            try:
                result = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                                        capture_output=True, text=True)
            except FileNotFoundError:
                result = subprocess.run(["xsel", "--clipboard", "--output"],
                                        capture_output=True, text=True)
            return result.stdout.strip()
        return ""
