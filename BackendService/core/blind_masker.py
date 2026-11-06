"""盲盒名称自动脱敏器与明文还原校验器（交底书 §3.3 / Grok 交底书 §2.2、§2.3）。

规则：
- 仅保留 2 个“非直白暴露全称”的汉字，其余汉字用 '*' 一对一**等长**替换；
- blind_name 长度严格等于 full_name 长度，且保留的明文汉字数严格为 2；
- description / summary_100w 不得出现 full_name（允许保留省市区位）。
"""
from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Tuple

HANZI_RE = re.compile(r"[一-龥]")

# 正文泄露全称时的脱敏代称
DEFAULT_PLACEHOLDER = "这座秘境"


def hanzi_indices(text: str) -> List[int]:
    """返回所有汉字字符的下标（0 基）。"""
    return [i for i, ch in enumerate(text) if HANZI_RE.match(ch)]


def hanzi_count(text: str) -> int:
    return len(hanzi_indices(text))


def default_keep_indices(indices: Sequence[int]) -> List[int]:
    """默认保留 2 个汉字：取约 1/3 与 2/3 位置，制造悬念提示且不直白暴露全称。"""
    n = len(indices)
    if n == 0:
        return []
    if n <= 2:
        return list(indices)
    first = indices[n // 3]
    second = indices[2 * n // 3]
    if first == second:
        second = indices[(2 * n // 3 + 1) % n]
    return [first, second]


def mask_full_name(full_name: str, keep_indices: Optional[Sequence[int]] = None) -> str:
    """将 full_name 脱敏为 blind_name（仅保留 2 个汉字，其余汉字替换为 '*'）。

    keep_indices 未提供时使用默认选字规则；提供时须为汉字下标序列。
    """
    idxs = hanzi_indices(full_name)
    keep = set(default_keep_indices(idxs)) if keep_indices is None else set(int(i) for i in keep_indices)
    out: List[str] = []
    for i, ch in enumerate(full_name):
        if HANZI_RE.match(ch) and i not in keep:
            out.append("*")
        else:
            out.append(ch)
    return "".join(out)


def validate_blind_name(full_name: str, blind_name: str) -> Tuple[bool, List[str]]:
    """校验 blind_name 是否符合脱敏规范，返回 (是否合规, 错误原因列表)。"""
    errors: List[str] = []
    if len(blind_name) != len(full_name):
        errors.append(f"长度不匹配：full={len(full_name)}，blind={len(blind_name)}")
    kept = [i for i, ch in enumerate(blind_name) if HANZI_RE.match(ch)]
    if len(kept) != 2:
        errors.append(f"保留汉字数应为 2，实际为 {len(kept)}")
    for i in kept:
        if i >= len(full_name):
            errors.append(f"位置 {i} 越界")
        elif blind_name[i] != full_name[i]:
            errors.append(f"位置 {i} 保留字 '{blind_name[i]}' 与原文 '{full_name[i]}' 不符")
    return (len(errors) == 0, errors)


def contains_full_name(text: str, full_name: str) -> bool:
    return bool(full_name) and full_name in text


def sanitize_text(
    text: str,
    forbidden: Iterable[str],
    placeholder: str = DEFAULT_PLACEHOLDER,
) -> str:
    """将正文中出现的禁用词（景点全称等）替换为代称，返回替换后的文本。"""
    out = text
    for word in forbidden:
        if word:
            out = out.replace(word, placeholder)
    return out
