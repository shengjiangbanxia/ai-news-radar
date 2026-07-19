#!/usr/bin/env python3
"""Explainable interest filter for private AI/PC/server news radars."""

from __future__ import annotations

import re
from typing import Any


INTEREST_TERMS: dict[str, tuple[str, ...]] = {
    "ai": (
        "ai", "artificial intelligence", "machine learning", "large language model",
        "ai model", "ai agent", "agent", "inference", "training", "multimodal",
        "reasoning", "generative ai", "foundation model", "vision-language model",
        "transformer", "diffusion", "fine-tuning", "embedding", "vector database",
        "rag", "computer vision", "speech recognition", "robotics", "autonomous",
        "llm", "gpt", "claude", "gemini", "deepseek", "qwen", "llama",
        "openai", "anthropic", "智谱", "大模型", "语言模型", "人工智能",
        "机器学习", "智能体", "推理", "训练", "多模态", "生成式 ai",
        "基础模型", "视觉语言模型", "向量数据库", "检索增强", "计算机视觉",
        "语音识别", "机器人", "自动驾驶", "模型论文", "大模型论文",
    ),
    "pc": (
        "pc", "personal computer", "notebook", "laptop", "windows", "macbook",
        "desktop", "workstation", "client computing", "copilot+ pc", "chromeos",
        "apple", "qualcomm", "snapdragon", "intel", "amd", "arm", "mediatek",
        "cpu", "soc", "processor", "ryzen", "core ultra", "npu", "display",
        "audio", "usb-c", "thunderbolt", "webcam", "headset", "microphone",
        "keyboard", "touchpad", "on-device ai", "edge ai", "local ai",
        "高通", "苹果", "联发科", "笔记本", "台式机", "工作站", "个人电脑",
        "客户端计算", "处理器", "显示器", "音频", "摄像头", "耳机", "麦克风",
        "键盘", "触控板", "端侧 ai", "边缘 ai", "本地 ai",
    ),
    "server_industry": (
        "server", "datacenter", "data center", "ai infrastructure", "gpu", "hbm",
        "memory", "dram", "nand", "semiconductor", "foundry", "wafer", "tsmc",
        "cxmt", "samsung", "sumsung", "micron", "sk hynix", "kioxia", "nvidia",
        "broadcom", "marvell", "asml", "accelerator", "rack", "cluster", "cxl",
        "nvlink", "infiniband", "ethernet", "optical interconnect", "silicon photonics",
        "cowos", "advanced packaging", "liquid cooling", "ssd", "hyperscaler",
        "cloud infrastructure", "supercomputer", "台积电", "长鑫", "三星", "海力士",
        "美光", "镁光", "英伟达", "博通", "阿斯麦", "服务器", "数据中心",
        "加速器", "机架", "集群", "内存", "存储", "半导体", "晶圆", "芯片",
        "算力", "光互连", "硅光", "先进封装", "液冷", "云基础设施", "超级计算机",
    ),
}

_WORD_TERMS = {
    "ai", "pc", "npu", "gpu", "cpu", "soc", "llm", "gpt", "hbm", "amd",
    "arm", "rag", "cxl", "ssd",
}

# These words occur frequently outside the target industries. They can support
# a match, but cannot establish AI relevance by themselves.
CONTEXT_ONLY_TERMS = {"agent", "inference", "training", "reasoning", "robotics", "autonomous"}


def _term_matches(text: str, term: str) -> bool:
    if term in _WORD_TERMS:
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text, re.I) is not None
    return term.lower() in text


def score_personal_interest(record: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        str(record.get(key) or "")
        for key in ("title", "summary", "source", "site_name")
    ).lower()
    categories: list[str] = []
    signals: list[str] = []
    for category, terms in INTEREST_TERMS.items():
        matched = sorted({term for term in terms if _term_matches(text, term)})
        qualifying = [term for term in matched if term not in CONTEXT_ONLY_TERMS]
        if qualifying:
            categories.append(category)
            signals.extend(matched)
    return {
        "is_interesting": bool(categories),
        "categories": categories,
        "signals": sorted(set(signals)),
        "excluded_topics": [],
        "reason": "matched_interest" if categories else "no_interest_signal",
    }


def add_personal_interest_fields(record: dict[str, Any]) -> dict[str, Any]:
    result = score_personal_interest(record)
    out = dict(record)
    out["personal_interest_match"] = result["is_interesting"]
    out["personal_interest_categories"] = result["categories"]
    out["personal_interest_signals"] = result["signals"]
    out["personal_interest_excluded_topics"] = result["excluded_topics"]
    out["personal_interest_reason"] = result["reason"]
    return out
