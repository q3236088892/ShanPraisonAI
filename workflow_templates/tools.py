"""
Local tools for YAML workflows under workflow_templates/.

These tools are auto-loaded by `praisonai workflow run <yaml>` when the YAML
file is in the same folder as this tools.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


def _safe_limit(items: List[str], max_items: int) -> List[str]:
    if max_items <= 0:
        return []
    return items[:max_items]


def list_repo_files(directory: str = ".", max_items: int = 80) -> str:
    """
    List files recursively under a directory.

    Args:
        directory: Target directory path (default: current directory).
        max_items: Maximum number of paths returned.

    Returns:
        Newline-separated relative file paths.
    """
    base = Path(directory).resolve()
    if not base.exists():
        return f"[ERROR] directory not found: {directory}"
    if not base.is_dir():
        return f"[ERROR] not a directory: {directory}"

    files: List[str] = []
    for p in base.rglob("*"):
        if p.is_file():
            try:
                files.append(str(p.relative_to(base)).replace("\\", "/"))
            except Exception:
                files.append(str(p))

    files = _safe_limit(sorted(files), max_items)
    return "\n".join(files)


def list_repo_dirs(directory: str = ".", max_items: int = 60) -> str:
    """
    List directories recursively under a directory.

    Args:
        directory: Target directory path.
        max_items: Maximum number of directories returned.

    Returns:
        Newline-separated relative directory paths.
    """
    base = Path(directory).resolve()
    if not base.exists():
        return f"[ERROR] directory not found: {directory}"
    if not base.is_dir():
        return f"[ERROR] not a directory: {directory}"

    dirs: List[str] = []
    for p in base.rglob("*"):
        if p.is_dir():
            try:
                dirs.append(str(p.relative_to(base)).replace("\\", "/"))
            except Exception:
                dirs.append(str(p))

    dirs = _safe_limit(sorted(dirs), max_items)
    return "\n".join(dirs)


def read_text_file(filepath: str, max_chars: int = 2500) -> str:
    """
    Read a text file as UTF-8 with fallback to replacement mode.

    Args:
        filepath: File path to read.
        max_chars: Maximum number of chars returned.

    Returns:
        File content (possibly truncated).
    """
    p = Path(filepath)
    if not p.exists():
        return f"[ERROR] file not found: {filepath}"
    if not p.is_file():
        return f"[ERROR] not a file: {filepath}"

    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[ERROR] failed to read file: {filepath}\n{e}"

    if max_chars > 0 and len(text) > max_chars:
        text = text[:max_chars] + "\n...[truncated]..."
    return text


def grep_in_file(filepath: str, keyword: str, max_lines: int = 20) -> str:
    """
    Find lines containing a keyword in a text file.

    Args:
        filepath: File path to scan.
        keyword: Keyword to match.
        max_lines: Maximum number of matched lines returned.

    Returns:
        Newline-separated "line_no: content".
    """
    p = Path(filepath)
    if not p.exists():
        return f"[ERROR] file not found: {filepath}"
    if not p.is_file():
        return f"[ERROR] not a file: {filepath}"

    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[ERROR] failed to read file: {filepath}\n{e}"

    out: List[str] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if keyword in line:
            out.append(f"{idx}: {line}")
            if len(out) >= max_lines:
                break

    if not out:
        return "[NO_MATCH]"
    return "\n".join(out)
