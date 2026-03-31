# -*- coding: utf-8 -*-
"""
推荐模型预设：选择一项即可得到 provider + model + base_url（用户只需填 API Key）。
名称随厂商文档会迭代，此处为 OpenAI 兼容/各厂商常用入口（2026 初参考）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# provider 值须与 functional_ai.real_ai_generator.AIProvider 的 .value 一致

AI_MODEL_PRESETS: List[Dict[str, Any]] = [
    # OpenAI（官方）
    {
        "id": "openai_gpt4o",
        "label_zh": "OpenAI · GPT-4o",
        "label_en": "OpenAI · GPT-4o",
        "provider": "openai",
        "model": "gpt-4o",
        "base_url": "https://api.openai.com/v1",
    },
    {
        "id": "openai_gpt4o_mini",
        "label_zh": "OpenAI · GPT-4o mini（性价比高）",
        "label_en": "OpenAI · GPT-4o mini",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
    },
    {
        "id": "openai_gpt4_turbo",
        "label_zh": "OpenAI · GPT-4 Turbo",
        "label_en": "OpenAI · GPT-4 Turbo",
        "provider": "openai",
        "model": "gpt-4-turbo",
        "base_url": "https://api.openai.com/v1",
    },
    {
        "id": "openai_o3_mini",
        "label_zh": "OpenAI · o3-mini（推理）",
        "label_en": "OpenAI · o3-mini",
        "provider": "openai",
        "model": "o3-mini",
        "base_url": "https://api.openai.com/v1",
    },
    # Anthropic（模型 ID 以控制台/文档为准，若 404 请换同系列日期后缀）
    {
        "id": "anthropic_sonnet35",
        "label_zh": "Anthropic · Claude 3.5 Sonnet",
        "label_en": "Anthropic · Claude 3.5 Sonnet",
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
        "base_url": None,
    },
    {
        "id": "anthropic_sonnet37",
        "label_zh": "Anthropic · Claude 3.7 Sonnet",
        "label_en": "Anthropic · Claude 3.7 Sonnet",
        "provider": "anthropic",
        "model": "claude-3-7-sonnet-20250219",
        "base_url": None,
    },
    {
        "id": "anthropic_haiku35",
        "label_zh": "Anthropic · Claude 3.5 Haiku（快）",
        "label_en": "Anthropic · Claude 3.5 Haiku",
        "provider": "anthropic",
        "model": "claude-3-5-haiku-20241022",
        "base_url": None,
    },
    # DeepSeek
    {
        "id": "deepseek_chat",
        "label_zh": "DeepSeek · deepseek-chat（V3）",
        "label_en": "DeepSeek · deepseek-chat",
        "provider": "deepseek",
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
    },
    {
        "id": "deepseek_reasoner",
        "label_zh": "DeepSeek · deepseek-reasoner（R1）",
        "label_en": "DeepSeek · deepseek-reasoner",
        "provider": "deepseek",
        "model": "deepseek-reasoner",
        "base_url": "https://api.deepseek.com/v1",
    },
    # 阿里通义（DashScope OpenAI 兼容：用 openai 客户端 + 兼容 base_url）
    {
        "id": "qwen3_max",
        "label_zh": "阿里云 · Qwen3-Max（DashScope OpenAI 兼容）",
        "label_en": "Alibaba · Qwen3-Max (DashScope compat)",
        "provider": "openai",
        "model": "qwen3-max",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    },
    {
        "id": "qwen_plus",
        "label_zh": "阿里云 · Qwen-Plus（DashScope OpenAI 兼容）",
        "label_en": "Alibaba · Qwen-Plus (DashScope compat)",
        "provider": "openai",
        "model": "qwen-plus",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    },
    {
        "id": "qwen_turbo",
        "label_zh": "阿里云 · Qwen-Turbo（DashScope OpenAI 兼容）",
        "label_en": "Alibaba · Qwen-Turbo (DashScope compat)",
        "provider": "openai",
        "model": "qwen-turbo",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    },
    {
        "id": "qwen_native_turbo",
        "label_zh": "阿里云 · Qwen-Turbo（原生 DashScope API）",
        "label_en": "Alibaba · Qwen-Turbo (native API)",
        "provider": "qwen",
        "model": "qwen-turbo",
        "base_url": None,
    },
    # Google Gemini（REST 用模型名；base_url 占位，实际在代码里拼 URL）
    {
        "id": "gemini_25_flash",
        "label_zh": "Google · Gemini 2.5 Flash Preview",
        "label_en": "Google · Gemini 2.5 Flash Preview",
        "provider": "google_gemini",
        "model": "gemini-2.5-flash-preview-05-20",
        "base_url": None,
    },
    {
        "id": "gemini_20_flash",
        "label_zh": "Google · Gemini 2.0 Flash",
        "label_en": "Google · Gemini 2.0 Flash",
        "provider": "google_gemini",
        "model": "gemini-2.0-flash",
        "base_url": None,
    },
    # 智谱
    {
        "id": "glm4_air",
        "label_zh": "智谱 · GLM-4-Air",
        "label_en": "Zhipu · GLM-4-Air",
        "provider": "chatglm",
        "model": "glm-4-air",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
    },
    {
        "id": "glm4_plus",
        "label_zh": "智谱 · GLM-4-Plus",
        "label_en": "Zhipu · GLM-4-Plus",
        "provider": "chatglm",
        "model": "glm-4-plus",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
    },
    # Moonshot / Kimi（OpenAI 兼容客户端）
    {
        "id": "moonshot_v1_128k",
        "label_zh": "Moonshot · moonshot-v1-128k",
        "label_en": "Moonshot · moonshot-v1-128k",
        "provider": "moonshot",
        "model": "moonshot-v1-128k",
        "base_url": "https://api.moonshot.cn/v1",
    },
    {
        "id": "moonshot_v1_8k",
        "label_zh": "Moonshot · moonshot-v1-8k",
        "label_en": "Moonshot · moonshot-v1-8k",
        "provider": "moonshot",
        "model": "moonshot-v1-8k",
        "base_url": "https://api.moonshot.cn/v1",
    },
]

_PRESET_BY_ID = {p["id"]: p for p in AI_MODEL_PRESETS}


def get_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    if not preset_id:
        return None
    return _PRESET_BY_ID.get(preset_id.strip())


def list_presets_for_template(lang: str) -> List[Dict[str, Any]]:
    """供 Jinja 使用：每项含 id、label。"""
    use_en = (lang or "zh").startswith("en")
    out = []
    for p in AI_MODEL_PRESETS:
        label = p["label_en"] if use_en else p["label_zh"]
        out.append({"id": p["id"], "label": label})
    return out
