from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True, slots=True)
class AiRewriteResult:
    title: str
    description: str
    tags: list[str]
    provider: str


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _fallback_rewrite(platform: str, title: str, description: str, tags: list[str]) -> AiRewriteResult:
    # 最小无模型兜底：不做“幻想生成”，只做轻量格式化，保证平台有可用返回值。
    normalized_tags = [tag.strip().lstrip("#") for tag in tags if tag and tag.strip()]
    normalized_tags = list(dict.fromkeys(normalized_tags))[:10]
    normalized_desc = description.strip()
    if normalized_desc and not normalized_desc.endswith("。") and len(normalized_desc) < 80:
        normalized_desc += "。"
    return AiRewriteResult(
        title=title.strip(),
        description=f"[{platform}] {normalized_desc}".strip(),
        tags=normalized_tags,
        provider="fallback",
    )


def rewrite_for_platform(
    platform: str,
    title: str,
    description: str,
    tags: list[str],
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> AiRewriteResult:
    """
    可选的 OpenAI 兼容接口：
    - SAU_AI_BASE_URL: 例如 https://api.openai.com
    - SAU_AI_API_KEY: Bearer token
    - SAU_AI_MODEL: 例如 gpt-4.1-mini
    """
    base_url = (base_url or "").strip() or _env("SAU_AI_BASE_URL")
    api_key = (api_key or "").strip() or _env("SAU_AI_API_KEY")
    model = (model or "").strip() or (_env("SAU_AI_MODEL") or "gpt-4.1-mini")
    if not base_url or not api_key:
        return _fallback_rewrite(platform, title, description, tags)

    url = base_url.rstrip("/") + "/v1/chat/completions"
    prompt = (
        "你是自媒体运营助手。请把输入内容改写为适合指定平台发布的版本。\n"
        "要求：不新增事实、不编造数据；标题不超过 30 字；描述不超过 300 字；输出 tags 最多 10 个。\n"
        "只输出严格 JSON：{title, description, tags}。\n\n"
        f"platform: {platform}\n"
        f"title: {title}\n"
        f"description: {description}\n"
        f"tags: {tags}\n"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是严谨的自媒体文案改写助手，只输出 JSON。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=60,
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return AiRewriteResult(
        title=str(parsed.get("title", title)).strip(),
        description=str(parsed.get("description", description)).strip(),
        tags=[str(item).strip().lstrip("#") for item in (parsed.get("tags") or tags) if str(item).strip()][:10],
        provider="openai_compat",
    )
