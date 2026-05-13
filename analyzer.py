"""
AI Analyzer - supports Anthropic Claude, OpenAI, Google Gemini, Ollama
"""

import os
import base64
import json
from pathlib import Path
from typing import Optional


def _load_config() -> dict:
    """Load config from ~/.peekaboo/config.json or environment variables."""
    config_path = Path.home() / ".peekaboo" / "config.json"
    config = {}
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    return config


def _image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _detect_provider() -> str:
    """Auto-detect available AI provider from environment."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    return "ollama"  # fallback to local


class AIAnalyzer:

    def __init__(self, provider: Optional[str] = None):
        config = _load_config()
        self.provider = provider or config.get("default_provider") or _detect_provider()
        self.config = config

    def analyze_image(self, image_path: str, prompt: str) -> str:
        """Send image + prompt to AI and return text response."""
        if self.provider == "anthropic":
            return self._analyze_anthropic(image_path, prompt)
        elif self.provider == "openai":
            return self._analyze_openai(image_path, prompt)
        elif self.provider == "gemini":
            return self._analyze_gemini(image_path, prompt)
        elif self.provider == "ollama":
            return self._analyze_ollama(image_path, prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    # ── Anthropic Claude ──────────────────────────────────────────────────────

    def _analyze_anthropic(self, image_path: str, prompt: str) -> str:
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("Install anthropic: pip install anthropic")

        api_key = os.getenv("ANTHROPIC_API_KEY") or self.config.get("anthropic_api_key")
        if not api_key:
            raise RuntimeError("Set ANTHROPIC_API_KEY environment variable")

        client = anthropic.Anthropic(api_key=api_key)
        img_b64 = _image_to_base64(image_path)

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return response.content[0].text

    # ── OpenAI GPT-4 Vision ───────────────────────────────────────────────────

    def _analyze_openai(self, image_path: str, prompt: str) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("Install openai: pip install openai")

        api_key = os.getenv("OPENAI_API_KEY") or self.config.get("openai_api_key")
        if not api_key:
            raise RuntimeError("Set OPENAI_API_KEY environment variable")

        client = OpenAI(api_key=api_key)
        img_b64 = _image_to_base64(image_path)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
            max_tokens=2048,
        )
        return response.choices[0].message.content

    # ── Google Gemini ─────────────────────────────────────────────────────────

    def _analyze_gemini(self, image_path: str, prompt: str) -> str:
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError("Install google-generativeai: pip install google-generativeai")

        api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or self.config.get("gemini_api_key")
        )
        if not api_key:
            raise RuntimeError("Set GEMINI_API_KEY environment variable")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        from PIL import Image
        img = Image.open(image_path)
        response = model.generate_content([prompt, img])
        return response.text

    # ── Ollama (local) ────────────────────────────────────────────────────────

    def _analyze_ollama(self, image_path: str, prompt: str) -> str:
        try:
            import requests
        except ImportError:
            raise RuntimeError("Install requests: pip install requests")

        base_url = self.config.get("ollama_base_url", "http://localhost:11434")
        model = self.config.get("ollama_model", "llava")
        img_b64 = _image_to_base64(image_path)

        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "")
