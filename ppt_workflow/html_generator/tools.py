"""HTML PPT 生成器 — 本地工具集。

生成乔布斯风格的 HTML 演示网站，自带模板、转场动画、键盘/触屏导航。
"""

from __future__ import annotations

import json
import os
from pathlib import Path


_TEMPLATE_DIR = Path(__file__).parent


def read_html_template() -> str:
    """读取 HTML 演示模板。

    Returns:
        模板 HTML 内容，包含 {{TITLE}} 和 {{SLIDES}} 占位符。
    """
    template_path = _TEMPLATE_DIR / "template.html"
    return template_path.read_text(encoding="utf-8")


def write_file(file_path: str, content: str) -> str:
    """将内容写入文件。

    Args:
        file_path: 输出文件路径。
        content: 文件内容。

    Returns:
        "SUCCESS: <path> (<size> bytes)" 或 "ERROR: <message>"。
    """
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        Path(file_path).write_text(content, encoding="utf-8")
        size = os.path.getsize(file_path)
        return f"SUCCESS: {file_path} ({size} bytes)"
    except Exception as exc:
        return f"ERROR: {exc}"


def verify_html_ppt(file_path: str) -> str:
    """验证生成的 HTML PPT 文件。

    检查：文件存在、大小合理、包含必要结构（.slide 元素、deck 容器）。

    Args:
        file_path: HTML 文件路径。

    Returns:
        JSON 字符串，包含 status、slide_count、size_bytes、issues 等字段。
    """
    issues = []

    if not os.path.exists(file_path):
        return json.dumps({"status": "FAIL", "reason": "file not found"}, ensure_ascii=False)

    size = os.path.getsize(file_path)
    if size < 500:
        return json.dumps(
            {"status": "FAIL", "reason": f"file too small: {size} bytes"},
            ensure_ascii=False,
        )

    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except Exception as exc:
        return json.dumps({"status": "FAIL", "reason": str(exc)}, ensure_ascii=False)

    # 统计 slide 数量
    slide_count = content.count('class="slide ')
    if slide_count == 0:
        # 也尝试单引号
        slide_count = content.count("class='slide ")
    if slide_count == 0:
        issues.append("no slides found (missing class='slide ...')")

    # 检查基础结构
    if "deck" not in content:
        issues.append("missing deck container")
    if "<script>" not in content and "<script " not in content:
        issues.append("missing navigation script")

    # 检查 slide 类型分布
    has_title = "slide--title" in content
    has_content = "slide--content" in content
    has_end = "slide--end" in content

    if not has_title:
        issues.append("missing title slide")
    if not has_content:
        issues.append("missing content slides")
    if not has_end:
        issues.append("missing end slide")

    # 检查未替换的占位符
    if "{{TITLE}}" in content or "{{SLIDES}}" in content:
        issues.append("unreplaced template placeholders found")

    status = "PASS" if not issues else "WARN" if slide_count > 0 else "FAIL"

    return json.dumps(
        {
            "status": status,
            "file": file_path,
            "size_bytes": size,
            "slide_count": slide_count,
            "has_title_slide": has_title,
            "has_content_slides": has_content,
            "has_end_slide": has_end,
            "issues": issues,
        },
        ensure_ascii=False,
    )
