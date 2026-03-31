# -*- coding: utf-8 -*-
"""本地生成任务历史与请求快照（支持多人并发：按 generation_id 隔离）。"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone

from .paths import PROJECT_ROOT

HISTORY_PATH = os.path.join(PROJECT_ROOT, "data", "generation_history.json")
STATE_DIR = os.path.join(PROJECT_ROOT, "data", "generation_state")
_LOCK = threading.Lock()
MAX_ENTRIES = 500

TERMINAL_STATUSES = frozenset({"completed", "error"})


def _title_from_requirement(text: str) -> str:
    if not text or not str(text).strip():
        return ""
    return str(text).strip().split("\n")[0][:120]


def persist_request_snapshot(generation_id: str, payload: dict) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    path = os.path.join(STATE_DIR, f"{generation_id}.request.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
    except OSError as ex:
        print(f"⚠️ 保存生成请求快照失败: {ex}")


def load_request_snapshot(generation_id: str) -> dict | None:
    path = os.path.join(STATE_DIR, f"{generation_id}.request.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _read_history() -> list:
    if not os.path.isfile(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write_history(entries: list) -> None:
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    tmp = HISTORY_PATH + ".tmp"
    trimmed = entries[:MAX_ENTRIES]
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=0)
    os.replace(tmp, HISTORY_PATH)


def append_job(
    generation_id: str,
    client_id: str,
    requirement_text: str,
    status: str = "running",
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "generation_id": generation_id,
        "client_id": client_id or "",
        "title": _title_from_requirement(requirement_text),
        "status": status,
        "created_at": now,
        "updated_at": now,
        "case_count": None,
        "error_summary": None,
        "excel_file": None,
    }
    with _LOCK:
        arr = _read_history()
        arr.insert(0, entry)
        _write_history(arr)


def update_job(generation_id: str, **kwargs) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        arr = _read_history()
        found = False
        for i, e in enumerate(arr):
            if e.get("generation_id") == generation_id:
                e = dict(e)
                for k, v in kwargs.items():
                    if v is not None:
                        e[k] = v
                e["updated_at"] = now
                arr[i] = e
                found = True
                break
        if found:
            _write_history(arr)


def list_jobs(client_id: str | None = None, limit: int = 200) -> list:
    with _LOCK:
        arr = _read_history()
    if client_id:
        arr = [x for x in arr if x.get("client_id") == client_id]
    return arr[:limit]


def get_job(generation_id: str) -> dict | None:
    with _LOCK:
        for e in _read_history():
            if e.get("generation_id") == generation_id:
                return dict(e)
    return None


def scan_active_jobs(state_dir: str) -> list[dict]:
    """扫描进度文件，返回未处于终态的任务（多用户共享同一目录时即「全局进行中」）。"""
    if not os.path.isdir(state_dir):
        return []
    active = []
    for name in os.listdir(state_dir):
        if not name.endswith(".progress.json"):
            continue
        gid = name[: -len(".progress.json")]
        path = os.path.join(state_dir, name)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            st = data.get("status", "")
            if st in TERMINAL_STATUSES:
                continue
            mt = os.path.getmtime(path)
            active.append(
                {
                    "generation_id": gid,
                    "status": st,
                    "message": (data.get("message") or "")[:200],
                    "progress": data.get("progress", 0),
                    "start_time": data.get("start_time"),
                    "mtime": mt,
                }
            )
        except (OSError, json.JSONDecodeError):
            continue
    active.sort(key=lambda x: -x["mtime"])
    return active
