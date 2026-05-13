#!/usr/bin/env python3
"""
Peekaboo - Cross-platform AI screen capture & automation tool
Supports Windows and Ubuntu Desktop (ported from macOS openclaw/Peekaboo)
"""

import click
import sys
from core.screenshot import ScreenshotManager
from core.automation import AutomationManager
from core.window import WindowManager
from ai.analyzer import AIAnalyzer
import json

@click.group()
@click.version_option("1.0.0", prog_name="peekaboo")
def cli():
    """Peekaboo - AI-powered screen capture and GUI automation (Windows/Ubuntu)"""
    pass


# ─── image command ───────────────────────────────────────────────────────────

@cli.command()
@click.option("--mode", type=click.Choice(["screen", "window", "area"]), default="screen",
              help="Capture mode: full screen, specific window, or area")
@click.option("--app", default=None, help="App/window name to capture (for --mode window)")
@click.option("--screen", "screen_index", default=0, type=int, help="Screen index (0=primary)")
@click.option("--retina", is_flag=True, help="Capture at 2x resolution (HiDPI)")
@click.option("--path", default=None, help="Save path (e.g. ~/Desktop/shot.png)")
@click.option("--analyze", is_flag=True, help="Run AI analysis after capture")
@click.option("--prompt", default="Describe what you see on this screen.", help="AI analysis prompt")
@click.option("--provider", default=None, help="AI provider: anthropic, openai, gemini, ollama")
@click.option("--json", "output_json", is_flag=True, help="Output result as JSON")
def image(mode, app, screen_index, retina, path, analyze, prompt, provider, output_json):
    """Capture a screenshot of the screen, window, or area."""
    sm = ScreenshotManager()
    
    try:
        if mode == "screen":
            img_path, meta = sm.capture_screen(screen_index=screen_index, retina=retina, save_path=path)
        elif mode == "window":
            if not app:
                raise click.ClickException("--app is required for --mode window")
            img_path, meta = sm.capture_window(app_name=app, retina=retina, save_path=path)
        elif mode == "area":
            img_path, meta = sm.capture_area(save_path=path)

        result = {"screenshot": img_path, "meta": meta}

        if analyze:
            analyzer = AIAnalyzer(provider=provider)
            analysis = analyzer.analyze_image(img_path, prompt)
            result["analysis"] = analysis
            if not output_json:
                click.echo(f"\n📸 Screenshot: {img_path}")
                click.echo(f"\n🤖 AI Analysis:\n{analysis}")
        else:
            if not output_json:
                click.echo(f"📸 Screenshot saved: {img_path}")

        if output_json:
            click.echo(json.dumps(result, indent=2))

    except Exception as e:
        if output_json:
            click.echo(json.dumps({"error": str(e)}))
        else:
            raise click.ClickException(str(e))


# ─── see command ─────────────────────────────────────────────────────────────

@cli.command()
@click.option("--app", default=None, help="App/window to capture")
@click.option("--analyze", is_flag=True, default=True, help="Run AI analysis (default: on)")
@click.option("--prompt", default="Describe the UI elements visible on screen in detail.", help="AI prompt")
@click.option("--provider", default=None, help="AI provider")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def see(app, analyze, prompt, provider, output_json):
    """Capture and analyze screen with AI (combined shortcut)."""
    sm = ScreenshotManager()
    analyzer = AIAnalyzer(provider=provider)

    try:
        if app:
            img_path, meta = sm.capture_window(app_name=app)
        else:
            img_path, meta = sm.capture_screen()

        analysis = analyzer.analyze_image(img_path, prompt)
        result = {"screenshot": img_path, "analysis": analysis, "meta": meta}

        if output_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"📸 Captured: {img_path}")
            click.echo(f"\n🤖 {analysis}")

    except Exception as e:
        if output_json:
            click.echo(json.dumps({"error": str(e)}))
        else:
            raise click.ClickException(str(e))


# ─── click command ────────────────────────────────────────────────────────────

@cli.command(name="click")
@click.option("--on", "target", required=True, help="Element label or description to click")
@click.option("--app", default=None, help="Target app window")
@click.option("--provider", default=None, help="AI provider for element detection")
@click.option("--double", is_flag=True, help="Double-click")
@click.option("--right", is_flag=True, help="Right-click")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def click_cmd(target, app, provider, double, right, output_json):
    """Click a UI element by describing it in natural language."""
    sm = ScreenshotManager()
    analyzer = AIAnalyzer(provider=provider)
    auto = AutomationManager()

    try:
        if app:
            img_path, meta = sm.capture_window(app_name=app)
        else:
            img_path, meta = sm.capture_screen()

        # Ask AI to find the element coordinates
        prompt = (
            f"Find the UI element described as: '{target}'. "
            f"Return ONLY a JSON object with keys 'x' and 'y' as pixel coordinates "
            f"(integers) where this element is located. No explanation, just JSON."
        )
        coords_str = analyzer.analyze_image(img_path, prompt)
        coords = json.loads(coords_str.strip().strip("```json").strip("```").strip())
        x, y = int(coords["x"]), int(coords["y"])

        click_type = "right" if right else ("double" if double else "left")
        auto.click(x, y, click_type=click_type)

        result = {"clicked": target, "x": x, "y": y, "type": click_type}
        if output_json:
            click.echo(json.dumps(result))
        else:
            click.echo(f"✅ Clicked '{target}' at ({x}, {y})")

    except Exception as e:
        if output_json:
            click.echo(json.dumps({"error": str(e)}))
        else:
            raise click.ClickException(str(e))


# ─── type command ─────────────────────────────────────────────────────────────

@cli.command(name="type")
@click.option("--text", required=True, help="Text to type")
@click.option("--interval", default=0.05, type=float, help="Delay between keystrokes (seconds)")
def type_cmd(text, interval):
    """Type text using keyboard simulation."""
    auto = AutomationManager()
    auto.type_text(text, interval=interval)
    click.echo(f"⌨️  Typed: {text}")


# ─── hotkey command ───────────────────────────────────────────────────────────

@cli.command()
@click.argument("keys", nargs=-1, required=True)
def hotkey(keys):
    """Press a keyboard shortcut. Example: peekaboo hotkey ctrl c"""
    auto = AutomationManager()
    auto.hotkey(*keys)
    click.echo(f"⌨️  Hotkey: {' + '.join(keys)}")


# ─── scroll command ───────────────────────────────────────────────────────────

@cli.command()
@click.option("--direction", type=click.Choice(["up", "down", "left", "right"]), default="down")
@click.option("--amount", default=3, type=int, help="Scroll amount (clicks)")
@click.option("--x", default=None, type=int, help="X coordinate")
@click.option("--y", default=None, type=int, help="Y coordinate")
def scroll(direction, amount, x, y):
    """Scroll the mouse wheel."""
    auto = AutomationManager()
    auto.scroll(direction=direction, amount=amount, x=x, y=y)
    click.echo(f"🖱️  Scrolled {direction} x{amount}")


# ─── move command ─────────────────────────────────────────────────────────────

@cli.command()
@click.option("--x", required=True, type=int, help="X coordinate")
@click.option("--y", required=True, type=int, help="Y coordinate")
@click.option("--duration", default=0.2, type=float, help="Move duration in seconds")
def move(x, y, duration):
    """Move the mouse cursor to coordinates."""
    auto = AutomationManager()
    auto.move(x, y, duration=duration)
    click.echo(f"🖱️  Moved to ({x}, {y})")


# ─── window command ───────────────────────────────────────────────────────────

@cli.group()
def window():
    """Window management commands."""
    pass

@window.command(name="list")
@click.option("--json", "output_json", is_flag=True)
def window_list(output_json):
    """List all visible windows."""
    wm = WindowManager()
    windows = wm.list_windows()
    if output_json:
        click.echo(json.dumps(windows, indent=2))
    else:
        click.echo("🪟 Open Windows:")
        for w in windows:
            click.echo(f"  [{w['id']}] {w['title']} ({w['app']})")

@window.command(name="focus")
@click.argument("app_name")
def window_focus(app_name):
    """Bring a window to focus."""
    wm = WindowManager()
    wm.focus_window(app_name)
    click.echo(f"🪟 Focused: {app_name}")

@window.command(name="resize")
@click.argument("app_name")
@click.option("--width", required=True, type=int)
@click.option("--height", required=True, type=int)
def window_resize(app_name, width, height):
    """Resize a window."""
    wm = WindowManager()
    wm.resize_window(app_name, width, height)
    click.echo(f"🪟 Resized {app_name} to {width}x{height}")


# ─── agent command ────────────────────────────────────────────────────────────

@cli.command()
@click.argument("task")
@click.option("--provider", default=None, help="AI provider")
@click.option("--max-steps", default=10, type=int, help="Maximum automation steps")
def agent(task, provider, max_steps):
    """Run a natural language automation task. Example: peekaboo agent 'Open Firefox and go to google.com'"""
    import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from core.agent import Agent
    ag = Agent(provider=provider)
    click.echo(f"🤖 Running task: {task}")
    ag.run(task, max_steps=max_steps)


# ─── mcp command ─────────────────────────────────────────────────────────────

@cli.command()
@click.option("--host", default="127.0.0.1", help="MCP server host")
@click.option("--port", default=3000, type=int, help="MCP server port")
def serve():
    """Start Peekaboo as an MCP server for use with Claude Code, Cursor, etc."""
    from mcp_server.server import run_server
    click.echo(f"🚀 Starting Peekaboo MCP server on {host}:{port}")
    run_server()


if __name__ == "__main__":
    cli()
