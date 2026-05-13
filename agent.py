"""
Agent - executes natural language tasks via a loop of see → decide → act
"""

import json
import time
import click
from typing import Optional
from core.screenshot import ScreenshotManager
from core.automation import AutomationManager
from ai.analyzer import AIAnalyzer

SYSTEM_PROMPT = """You are Peekaboo, a desktop automation agent running on {platform}.
You control the computer using actions. Given a screenshot and a task, decide the NEXT single action.

Available actions (respond ONLY with JSON):
- click: {{"action": "click", "x": int, "y": int, "button": "left|right|double"}}
- type: {{"action": "type", "text": "string"}}
- hotkey: {{"action": "hotkey", "keys": ["ctrl", "c"]}}
- scroll: {{"action": "scroll", "direction": "up|down|left|right", "amount": int}}
- wait: {{"action": "wait", "seconds": float}}
- done: {{"action": "done", "result": "summary of what was accomplished"}}
- fail: {{"action": "fail", "reason": "why the task cannot be completed"}}

Rules:
1. Respond ONLY with a single JSON object, no explanation.
2. Be precise with coordinates — analyze the screenshot carefully.
3. Use "done" when the task is fully complete.
4. Use "fail" only if truly stuck after trying alternatives.
"""

import platform
PLATFORM = platform.system()


class Agent:

    def __init__(self, provider: Optional[str] = None):
        self.sm = ScreenshotManager()
        self.auto = AutomationManager()
        self.analyzer = AIAnalyzer(provider=provider)

    def run(self, task: str, max_steps: int = 10):
        """Execute a natural language task."""
        history = []
        system = SYSTEM_PROMPT.format(platform=PLATFORM)

        for step in range(1, max_steps + 1):
            click.echo(f"\n🔄 Step {step}/{max_steps}")

            # Capture current screen state
            img_path, _ = self.sm.capture_screen()
            click.echo(f"   📸 Screenshot: {img_path}")

            # Build prompt with task + history
            history_text = ""
            if history:
                history_text = "\n\nPrevious actions:\n" + "\n".join(
                    f"- Step {i+1}: {h}" for i, h in enumerate(history)
                )

            prompt = (
                f"{system}\n\n"
                f"Task: {task}"
                f"{history_text}\n\n"
                f"What is the next action? Respond with JSON only."
            )

            # Get AI decision
            response = self.analyzer.analyze_image(img_path, prompt)
            click.echo(f"   🤖 Decision: {response}")

            # Parse action
            try:
                clean = response.strip().strip("```json").strip("```").strip()
                action = json.loads(clean)
            except json.JSONDecodeError:
                click.echo(f"   ⚠️  Could not parse response, retrying...")
                continue

            action_type = action.get("action")

            # Execute action
            if action_type == "click":
                x, y = action["x"], action["y"]
                btn = action.get("button", "left")
                click.echo(f"   🖱️  Clicking ({x}, {y}) [{btn}]")
                self.auto.click(x, y, click_type=btn)
                history.append(f"click at ({x},{y}) button={btn}")

            elif action_type == "type":
                text = action["text"]
                click.echo(f"   ⌨️  Typing: {text}")
                self.auto.type_text(text)
                history.append(f"typed: {text[:50]}")

            elif action_type == "hotkey":
                keys = action["keys"]
                click.echo(f"   ⌨️  Hotkey: {' + '.join(keys)}")
                self.auto.hotkey(*keys)
                history.append(f"hotkey: {'+'.join(keys)}")

            elif action_type == "scroll":
                direction = action.get("direction", "down")
                amount = action.get("amount", 3)
                click.echo(f"   🖱️  Scrolling {direction} x{amount}")
                self.auto.scroll(direction=direction, amount=amount)
                history.append(f"scroll {direction} x{amount}")

            elif action_type == "wait":
                seconds = action.get("seconds", 1.0)
                click.echo(f"   ⏳ Waiting {seconds}s")
                time.sleep(seconds)
                history.append(f"waited {seconds}s")

            elif action_type == "done":
                result = action.get("result", "Task completed.")
                click.echo(f"\n✅ Done: {result}")
                return

            elif action_type == "fail":
                reason = action.get("reason", "Unknown reason")
                click.echo(f"\n❌ Failed: {reason}")
                return

            else:
                click.echo(f"   ⚠️  Unknown action: {action_type}")
                continue

            time.sleep(0.5)  # Brief pause between actions

        click.echo(f"\n⚠️  Reached max steps ({max_steps}) without completing task.")
