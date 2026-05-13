# 🙈 Peekaboo (Windows & Ubuntu Port)

Cross-platform AI screen capture and GUI automation tool.
**Ported from [openclaw/Peekaboo](https://github.com/openclaw/Peekaboo) (macOS/Swift) → Python (Windows + Ubuntu Desktop)**

---

## ✨ Features

| Feature | macOS original | This port |
|---|---|---|
| Full screen capture | ✅ | ✅ Windows + Ubuntu |
| Window capture | ✅ | ✅ Windows + Ubuntu |
| Area selection | ✅ | ✅ Windows + Ubuntu |
| AI image analysis | ✅ | ✅ Claude / GPT / Gemini / Ollama |
| Mouse click automation | ✅ | ✅ |
| Keyboard typing | ✅ | ✅ |
| Hotkeys | ✅ | ✅ |
| Scroll | ✅ | ✅ |
| Window management | ✅ | ✅ |
| Natural language agent | ✅ | ✅ |
| MCP server | ✅ | ✅ |

---

## 🖥️ System Requirements

### Windows
- Windows 10 or later
- Python 3.9+

### Ubuntu Desktop
- Ubuntu 20.04+ (with a desktop environment: GNOME, KDE, etc.)
- Python 3.9+
- Required system packages:
  ```bash
  sudo apt install xdotool wmctrl scrot python3-tk
  # Optional (for area selection):
  sudo apt install slop
  ```

---

## 📦 Installation

```bash
# Clone this repo
git clone https://github.com/yourname/peekaboo-cross-platform
cd peekaboo-cross-platform

# Install Python dependencies
pip install -r requirements.txt

# Run setup wizard (configure AI provider + API key)
python setup_config.py
```

---

## ⚙️ Configuration

Config is stored at `~/.peekaboo/config.json`:

```json
{
  "default_provider": "anthropic",
  "anthropic_api_key": "sk-ant-...",
  "openai_api_key": "sk-...",
  "gemini_api_key": "AIza...",
  "ollama_base_url": "http://localhost:11434",
  "ollama_model": "llava"
}
```

Or use environment variables:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=AIza...
```

---

## 🚀 Usage

### Screenshot

```bash
# Capture full screen
python peekaboo.py image --mode screen

# Capture specific window
python peekaboo.py image --mode window --app "Firefox"

# Capture and save to specific path
python peekaboo.py image --mode screen --path ~/Desktop/shot.png

# Capture with AI analysis
python peekaboo.py image --mode screen --analyze --prompt "What do you see?"
```

### AI Screen Analysis

```bash
# See & analyze current screen
python peekaboo.py see

# Analyze specific app window
python peekaboo.py see --app "VS Code"

# Custom prompt
python peekaboo.py see --prompt "List all the buttons visible on screen"

# JSON output
python peekaboo.py see --json
```

### GUI Automation

```bash
# Click a UI element by description
python peekaboo.py click --on "Submit button"
python peekaboo.py click --on "Search box"
python peekaboo.py click --on "File menu" --right   # right-click
python peekaboo.py click --on "icon" --double        # double-click

# Type text
python peekaboo.py type --text "Hello, World!"

# Keyboard shortcuts
python peekaboo.py hotkey ctrl c        # copy
python peekaboo.py hotkey ctrl v        # paste
python peekaboo.py hotkey alt F4        # close window (Windows)

# Scroll
python peekaboo.py scroll --direction down --amount 5
python peekaboo.py scroll --direction up
```

### Window Management

```bash
# List all open windows
python peekaboo.py window list

# Focus a window
python peekaboo.py window focus "Firefox"

# Resize
python peekaboo.py window resize "Firefox" --width 1280 --height 720
```

### Natural Language Agent

```bash
# Run a multi-step task in plain English
python peekaboo.py agent "Open Firefox and navigate to google.com"
python peekaboo.py agent "Take a screenshot and save it to the Desktop"
python peekaboo.py agent "Close all open Notepad windows"

# Limit steps
python peekaboo.py agent "Fill in the form" --max-steps 20
```

### MCP Server (for Claude Code / Cursor)

```bash
# Start MCP server
python peekaboo.py serve

# Add to Claude Code config (~/.claude/claude_desktop_config.json):
# {
#   "mcpServers": {
#     "peekaboo": {
#       "command": "python",
#       "args": ["/path/to/peekaboo.py", "serve"]
#     }
#   }
# }
```

---

## 🔌 Supported AI Providers

| Provider | Model | Setup |
|---|---|---|
| **Anthropic** | claude-opus-4-5 | `export ANTHROPIC_API_KEY=...` |
| **OpenAI** | gpt-4o | `export OPENAI_API_KEY=...` |
| **Gemini** | gemini-1.5-flash | `export GEMINI_API_KEY=...` |
| **Ollama** | llava (local) | Install Ollama + pull llava |

Override per command:
```bash
python peekaboo.py see --provider openai
python peekaboo.py agent "do something" --provider gemini
```

---

## 🆚 Differences from macOS original

| | macOS (openclaw/Peekaboo) | This Port |
|---|---|---|
| Language | Swift | Python |
| Platform | macOS 15+ only | Windows 10+ & Ubuntu 20.04+ |
| Window capture | ScreenCaptureKit | mss + pygetwindow / xdotool |
| UI automation | Accessibility API | pyautogui |
| Installation | Homebrew / npm | pip |
| MCP transport | stdio | stdio (same) |

---

## 🐛 Troubleshooting

**Ubuntu: `xdotool` not found**
```bash
sudo apt install xdotool
```

**Ubuntu: Screenshot is black**
```bash
# Some compositors need this:
sudo apt install scrot
```

**Windows: Window capture fails**
```bash
pip install pygetwindow
```

**pyautogui fails on Linux without display**
```bash
export DISPLAY=:0
```

---

## 📁 Project Structure

```
peekaboo/
├── peekaboo.py          # CLI entry point
├── setup_config.py      # First-time setup wizard
├── requirements.txt
├── core/
│   ├── screenshot.py    # Cross-platform screen capture
│   ├── automation.py    # Mouse & keyboard automation
│   ├── window.py        # Window management
│   └── agent.py         # Natural language task agent
├── ai/
│   └── analyzer.py      # Multi-provider AI vision
└── mcp_server/
    └── server.py        # MCP stdio server
```
