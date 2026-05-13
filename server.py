"""
Peekaboo MCP Server
Exposes Peekaboo tools via Model Context Protocol (MCP)
Compatible with Claude Code, Cursor, and other MCP clients
"""

import json
import sys
import base64
from pathlib import Path
from typing import Any, Optional

# Minimal MCP server using stdio transport (no external mcp package required)
# Compatible with the MCP spec: https://modelcontextprotocol.io

TOOLS = [
    {
        "name": "peekaboo_screenshot",
        "description": "Capture a screenshot of the screen or a specific application window",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["screen", "window"],
                    "description": "Capture mode",
                    "default": "screen"
                },
                "app": {
                    "type": "string",
                    "description": "Application window name (required for mode=window)"
                },
                "screen_index": {
                    "type": "integer",
                    "description": "Monitor index (0=primary)",
                    "default": 0
                },
            },
            "required": []
        }
    },
    {
        "name": "peekaboo_analyze",
        "description": "Capture and analyze the screen using AI vision",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "What to analyze or look for on screen"
                },
                "app": {
                    "type": "string",
                    "description": "Specific app window to capture (optional)"
                },
                "provider": {
                    "type": "string",
                    "description": "AI provider: anthropic, openai, gemini, ollama"
                }
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "peekaboo_click",
        "description": "Click a UI element described in natural language",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Description of the UI element to click"
                },
                "button": {
                    "type": "string",
                    "enum": ["left", "right", "double"],
                    "default": "left"
                }
            },
            "required": ["target"]
        }
    },
    {
        "name": "peekaboo_type",
        "description": "Type text using keyboard simulation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to type"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "peekaboo_hotkey",
        "description": "Press a keyboard shortcut",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keys to press simultaneously, e.g. ['ctrl', 'c']"
                }
            },
            "required": ["keys"]
        }
    },
    {
        "name": "peekaboo_scroll",
        "description": "Scroll the mouse wheel",
        "inputSchema": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["up", "down", "left", "right"],
                    "default": "down"
                },
                "amount": {
                    "type": "integer",
                    "description": "Scroll clicks",
                    "default": 3
                }
            },
            "required": []
        }
    },
    {
        "name": "peekaboo_windows",
        "description": "List all open windows on the desktop",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "peekaboo_agent",
        "description": "Run a natural language automation task (multi-step)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Natural language description of what to do"
                },
                "max_steps": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum automation steps"
                }
            },
            "required": ["task"]
        }
    }
]


def handle_tool(name: str, args: dict) -> Any:
    """Execute a tool and return the result."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    if name == "peekaboo_screenshot":
        from core.screenshot import ScreenshotManager
        sm = ScreenshotManager()
        mode = args.get("mode", "screen")
        if mode == "window":
            app = args.get("app")
            if not app:
                return {"error": "app parameter required for window mode"}
            path, meta = sm.capture_window(app)
        else:
            path, meta = sm.capture_screen(screen_index=args.get("screen_index", 0))

        # Return image as base64
        with open(path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        return {
            "path": path,
            "meta": meta,
            "image_base64": img_b64,
        }

    elif name == "peekaboo_analyze":
        from core.screenshot import ScreenshotManager
        from ai.analyzer import AIAnalyzer
        sm = ScreenshotManager()
        app = args.get("app")
        if app:
            path, meta = sm.capture_window(app)
        else:
            path, meta = sm.capture_screen()
        analyzer = AIAnalyzer(provider=args.get("provider"))
        analysis = analyzer.analyze_image(path, args["prompt"])
        return {"analysis": analysis, "screenshot": path}

    elif name == "peekaboo_click":
        from core.screenshot import ScreenshotManager
        from core.automation import AutomationManager
        from ai.analyzer import AIAnalyzer
        import json as _json
        sm = ScreenshotManager()
        auto = AutomationManager()
        analyzer = AIAnalyzer()
        path, _ = sm.capture_screen()
        prompt = (
            f"Find the UI element: '{args['target']}'. "
            f"Return ONLY JSON {{\"x\": int, \"y\": int}}. No explanation."
        )
        coords_str = analyzer.analyze_image(path, prompt)
        coords = _json.loads(coords_str.strip().strip("```json").strip("```").strip())
        x, y = int(coords["x"]), int(coords["y"])
        auto.click(x, y, click_type=args.get("button", "left"))
        return {"clicked": args["target"], "x": x, "y": y}

    elif name == "peekaboo_type":
        from core.automation import AutomationManager
        auto = AutomationManager()
        auto.type_text(args["text"])
        return {"typed": args["text"]}

    elif name == "peekaboo_hotkey":
        from core.automation import AutomationManager
        auto = AutomationManager()
        auto.hotkey(*args["keys"])
        return {"hotkey": args["keys"]}

    elif name == "peekaboo_scroll":
        from core.automation import AutomationManager
        auto = AutomationManager()
        auto.scroll(direction=args.get("direction", "down"), amount=args.get("amount", 3))
        return {"scrolled": args.get("direction", "down")}

    elif name == "peekaboo_windows":
        from core.window import WindowManager
        wm = WindowManager()
        return {"windows": wm.list_windows()}

    elif name == "peekaboo_agent":
        from core.agent import Agent
        import io
        from contextlib import redirect_stdout
        ag = Agent()
        f = io.StringIO()
        with redirect_stdout(f):
            ag.run(args["task"], max_steps=args.get("max_steps", 10))
        return {"log": f.getvalue()}

    return {"error": f"Unknown tool: {name}"}


def run_server():
    """Run MCP server using stdio transport (standard MCP protocol)."""
    import json

    # MCP uses stdin/stdout JSON-RPC
    def send(obj):
        line = json.dumps(obj)
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    send({
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    })

    for line in sys.stdin:
        try:
            req = json.loads(line.strip())
        except json.JSONDecodeError:
            continue

        method = req.get("method", "")
        req_id = req.get("id")
        params = req.get("params", {})

        if method == "initialize":
            send({
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "peekaboo", "version": "1.0.0"}
                }
            })

        elif method == "tools/list":
            send({
                "jsonrpc": "2.0", "id": req_id,
                "result": {"tools": TOOLS}
            })

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                result = handle_tool(tool_name, tool_args)
                send({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result)}]
                    }
                })
            except Exception as e:
                send({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {e}"}],
                        "isError": True
                    }
                })

        elif method == "ping":
            send({"jsonrpc": "2.0", "id": req_id, "result": {}})
