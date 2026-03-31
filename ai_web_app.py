#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向后兼容入口：与 `python run.py` 相同。推荐统一使用 `python run.py`。"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from functional_ai.ai_web_app import app

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
