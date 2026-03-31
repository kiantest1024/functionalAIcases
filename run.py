#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从仓库根目录启动 Web 服务：python run.py"""

from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

from functional_ai.ai_web_app import app

if __name__ == "__main__":
    # use_reloader=False：避免 watchdog 在生成长任务时重启进程，导致后台线程中断、进度会话丢失。
    # 需要热重载时可改为 True，但长文档 AI 生成期间请勿保存会触发重载的文件。
    app.run(debug=True, host="0.0.0.0", port=5001, use_reloader=False)
