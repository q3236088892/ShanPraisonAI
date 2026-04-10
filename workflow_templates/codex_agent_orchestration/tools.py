"""
Tools for codex_workflow.yaml.

Place this file in the same directory as codex_workflow.yaml so
`praisonai workflow run ...` can auto-load these functions as workflow tools.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional


def _to_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _to_int(value: object, default: int, minimum: int = 1) -> int:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except Exception:
        return default
    return max(parsed, minimum)


def _truncate(text: str, max_chars: int) -> str:
    limit = _to_int(max_chars, 12000, minimum=200)
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[truncated at {limit} chars]..."


def _extract_section(text: str, start_marker: str, end_marker: Optional[str] = None) -> str:
    start = text.find(start_marker)
    if start < 0:
        return ""
    start += len(start_marker)
    if end_marker:
        end = text.find(end_marker, start)
        if end < 0:
            end = len(text)
    else:
        end = len(text)
    return text[start:end].strip()


def _tail_lines(text: str, max_lines: int = 30, max_chars: int = 2000) -> str:
    if not text:
        return ""
    lines = [line.rstrip() for line in str(text).splitlines() if line.strip()]
    tail = "\n".join(lines[-_to_int(max_lines, 30, minimum=1) :])
    return _truncate(tail, _to_int(max_chars, 2000, minimum=200))


def _split_csv(text: object) -> List[str]:
    if text is None:
        return []
    items = []
    for item in str(text).split(","):
        value = item.strip()
        if value:
            items.append(value)
    return items


def _read_text_with_replace(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _is_text_candidate(path: Path) -> bool:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name in {
        "readme",
        "readme.md",
        "license",
        "dockerfile",
        "makefile",
        ".env.example",
        ".gitignore",
    }:
        return True
    return suffix in {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".kts",
        ".c",
        ".cc",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".php",
        ".rb",
        ".swift",
        ".scala",
        ".sh",
        ".ps1",
        ".bat",
        ".cmd",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".env",
        ".md",
        ".sql",
        ".xml",
        ".gradle",
        ".properties",
    }


def _file_priority(relative_path: str) -> tuple[int, int, str]:
    text = relative_path.replace("\\", "/").lower()
    name = Path(text).name
    stem = Path(text).stem
    priority = 5
    if name in {
        "readme",
        "readme.md",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "go.mod",
        "cargo.toml",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "dockerfile",
        "docker-compose.yml",
        ".env.example",
    }:
        priority = 0
    elif stem in {"main", "app", "server", "index", "router", "routes", "manage"}:
        priority = 1
    elif any(part in text for part in ("/api/", "/controller", "/service", "/model", "/route", "/utils/", "/middleware/", "/cmd/", "/internal/", "/src/")):
        priority = 2
    elif text.count("/") == 0:
        priority = 3
    return (priority, len(text), text)


def _build_project_context(
    root: Path,
    excludes: List[str],
    budget_chars: int = 60000,
    max_files: int = 80,
    max_file_chars: int = 5000,
) -> str:
    exclude_dirs = {item.strip().lower() for item in excludes if item.strip()}
    candidate_paths: List[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part.lower() in exclude_dirs for part in rel.parts[:-1]):
            continue
        if not _is_text_candidate(path):
            continue
        try:
            if path.stat().st_size > 200_000:
                continue
        except Exception:
            continue
        candidate_paths.append(path)

    file_list = [str(p.relative_to(root)).replace("\\", "/") for p in candidate_paths]
    file_list.sort()
    selected = sorted(candidate_paths, key=lambda p: _file_priority(str(p.relative_to(root))))

    chunks: List[str] = []
    used = 0
    header = (
        "以下是预采样项目上下文，请优先基于这些内容完成分析；只有在明显不足时再自行补充读取。\n\n"
        "## 文件清单\n"
        + "\n".join(file_list[:max_files])
    )
    chunks.append(header)
    used += len(header)

    for path in selected:
        rel = str(path.relative_to(root)).replace("\\", "/")
        try:
            text = _read_text_with_replace(path)
        except Exception:
            continue
        snippet = _truncate(text, max_file_chars)
        block = f"\n\n## 文件: {rel}\n```text\n{snippet}\n```"
        if used + len(block) > budget_chars:
            break
        chunks.append(block)
        used += len(block)

    return "".join(chunks)


def _resolve_dir(directory: str) -> Optional[Path]:
    p = Path(directory).resolve()
    if not p.exists() or not p.is_dir():
        return None
    return p


def _resolve_file(file_path: str) -> Optional[Path]:
    p = Path(file_path).resolve()
    if not p.exists() or not p.is_file():
        return None
    return p


def _find_codex_binary() -> Optional[str]:
    for name in ("codex", "codex.cmd", "codex.exe"):
        found = shutil.which(name)
        if found:
            return found

    home = Path.home()
    extra_candidates = [
        home / "AppData" / "Roaming" / "npm-global" / "codex.cmd",
        home / "AppData" / "Roaming" / "npm" / "codex.cmd",
        home / "scoop" / "shims" / "codex.cmd",
        home / "scoop" / "shims" / "codex.exe",
    ]
    for p in extra_candidates:
        if p.exists():
            return str(p)
    return None


def _run_subprocess(
    cmd: List[str],
    timeout: int,
    cwd: Optional[Path] = None,
    stdin_text: Optional[str] = None,
    extra_env: Optional[dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    runner_cmd: List[str] = cmd
    if os.name == "nt" and cmd and cmd[0].lower().endswith((".cmd", ".bat")):
        runner_cmd = ["cmd", "/c", *cmd]
    run_env = os.environ.copy()
    if extra_env:
        run_env.update({k: str(v) for k, v in extra_env.items() if v is not None})
    return subprocess.run(
        runner_cmd,
        cwd=str(cwd) if cwd else None,
        input=stdin_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=run_env,
    )


def _create_mirror_workspace(source: Path, excludes: List[str]) -> Path:
    staging_root = Path.cwd() / ".tmp_codex_workspaces"
    staging_root.mkdir(parents=True, exist_ok=True)
    target = staging_root / f"codex_analysis_{int(time.time() * 1000)}_{os.getpid()}_{source.name}"
    ignore = shutil.ignore_patterns(*excludes) if excludes else None
    shutil.copytree(source, target, ignore=ignore)
    return target


def _create_temp_codex_home(
    *,
    base_url: str,
    api_key: str,
    model: str,
    reasoning_effort: str,
) -> Path:
    staging_root = Path.cwd() / ".tmp_codex_homes"
    staging_root.mkdir(parents=True, exist_ok=True)
    home_dir = staging_root / f"codex_home_{int(time.time() * 1000)}_{os.getpid()}"
    home_dir.mkdir(parents=True, exist_ok=True)

    config_text = (
        'model_provider = "custom"\n'
        f'model = "{model}"\n'
        f'model_reasoning_effort = "{reasoning_effort}"\n'
        "disable_response_storage = true\n"
        'network_access = "enabled"\n'
        "\n"
        "[model_providers.custom]\n"
        'name = "custom"\n'
        'wire_api = "responses"\n'
        "requires_openai_auth = true\n"
        f'base_url = "{base_url}"\n'
        "\n"
        "[features]\n"
        "rmcp_client = false\n"
        "apps = false\n"
    )
    (home_dir / "config.toml").write_text(config_text, encoding="utf-8")
    (home_dir / "auth.json").write_text(
        json.dumps({"OPENAI_API_KEY": api_key}, ensure_ascii=False),
        encoding="utf-8",
    )
    return home_dir


def _run_subprocess_with_heartbeat(
    cmd: List[str],
    timeout: int,
    cwd: Optional[Path] = None,
    stdin_text: Optional[str] = None,
    heartbeat_sec: int = 15,
    extra_env: Optional[dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    runner_cmd: List[str] = cmd
    if os.name == "nt" and cmd and cmd[0].lower().endswith((".cmd", ".bat")):
        runner_cmd = ["cmd", "/c", *cmd]

    beat = _to_int(heartbeat_sec, 15, minimum=3)
    run_env = os.environ.copy()
    if extra_env:
        run_env.update({k: str(v) for k, v in extra_env.items() if v is not None})
    stdout_path = Path(tempfile.mkstemp(prefix="codex_stdout_", suffix=".log")[1])
    stderr_path = Path(tempfile.mkstemp(prefix="codex_stderr_", suffix=".log")[1])
    proc: Optional[subprocess.Popen[str]] = None

    try:
        with stdout_path.open("w", encoding="utf-8", errors="replace") as out_f, stderr_path.open(
            "w", encoding="utf-8", errors="replace"
        ) as err_f:
            proc = subprocess.Popen(
                runner_cmd,
                cwd=str(cwd) if cwd else None,
                stdin=subprocess.PIPE if stdin_text is not None else None,
                stdout=out_f,
                stderr=err_f,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=run_env,
            )

            if stdin_text is not None and proc.stdin is not None:
                proc.stdin.write(stdin_text)
                proc.stdin.close()

            start = time.monotonic()
            next_beat = beat
            while True:
                return_code = proc.poll()
                elapsed = int(time.monotonic() - start)

                if return_code is not None:
                    break

                if elapsed >= timeout:
                    proc.kill()
                    proc.wait(timeout=5)
                    raise subprocess.TimeoutExpired(runner_cmd, timeout)

                if elapsed >= next_beat:
                    out_size = stdout_path.stat().st_size if stdout_path.exists() else 0
                    err_size = stderr_path.stat().st_size if stderr_path.exists() else 0
                    print(
                        f"[CODEX] running {elapsed}s... stdout={out_size}B stderr={err_size}B",
                        flush=True,
                    )
                    next_beat += beat

                time.sleep(1)

        stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
        final_code = proc.returncode if proc is not None else 1
        return subprocess.CompletedProcess(runner_cmd, final_code, stdout_text, stderr_text)
    finally:
        try:
            stdout_path.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            stderr_path.unlink(missing_ok=True)
        except Exception:
            pass


def list_files(directory: str = ".", pattern: str = "*", max_items: int = 200) -> str:
    """
    List files recursively.
    """
    base = _resolve_dir(directory)
    if base is None:
        return f"[ERROR] invalid directory: {directory}"

    items: List[str] = []
    for p in base.rglob(pattern):
        if p.is_file():
            try:
                items.append(str(p.relative_to(base)).replace("\\", "/"))
            except Exception:
                items.append(str(p))

    items = sorted(items)[: _to_int(max_items, 200, minimum=1)]
    if not items:
        return "[EMPTY]"
    return "\n".join(items)


def read_file(file_path: str, max_chars: int = 4000) -> str:
    """
    Read a UTF-8 text file with fallback replacement.
    """
    p = _resolve_file(file_path)
    if p is None:
        return f"[ERROR] invalid file: {file_path}"

    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"[ERROR] read failed: {exc}"

    return _truncate(text, max_chars)


def grep_in_file(file_path: str, keyword: str, max_lines: int = 40) -> str:
    """
    Return matched lines as 'line_no: content'.
    """
    p = _resolve_file(file_path)
    if p is None:
        return f"[ERROR] invalid file: {file_path}"
    if not keyword:
        return "[ERROR] keyword is empty"

    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"[ERROR] read failed: {exc}"

    matches: List[str] = []
    line_limit = _to_int(max_lines, 40, minimum=1)
    for idx, line in enumerate(text.splitlines(), start=1):
        if keyword in line:
            matches.append(f"{idx}: {line}")
            if len(matches) >= line_limit:
                break

    if not matches:
        return "[NO_MATCH]"
    return "\n".join(matches)


def execute_command(
    command: str,
    cwd: str = ".",
    timeout_sec: int = 300,
    max_chars: int = 12000,
) -> str:
    """
    Run shell command and return structured output.
    """
    if not command or not command.strip():
        return "[ERROR] command is empty"

    base = _resolve_dir(cwd)
    if base is None:
        return f"[ERROR] invalid cwd: {cwd}"

    timeout = _to_int(timeout_sec, 300, minimum=1)
    try:
        proc = subprocess.run(
            command,
            cwd=str(base),
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return (
            "[COMMAND]\n"
            f"{command}\n"
            "[CWD]\n"
            f"{base}\n"
            f"[TIMEOUT] {timeout}s"
        )
    except Exception as exc:
        return f"[ERROR] command execution failed: {exc}"

    stdout = _truncate(proc.stdout or "", max_chars)
    stderr = _truncate(proc.stderr or "", max_chars)
    return (
        "[COMMAND]\n"
        f"{command}\n"
        "[CWD]\n"
        f"{base}\n"
        f"[EXIT_CODE] {proc.returncode}\n"
        "[STDOUT]\n"
        f"{stdout}\n"
        "[STDERR]\n"
        f"{stderr}"
    )


def check_codex_cli() -> str:
    """
    Check whether Codex CLI is available in PATH.
    """
    codex_bin = _find_codex_binary()
    if not codex_bin:
        return "[ERROR] codex not found in PATH"

    try:
        proc = _run_subprocess([codex_bin, "--version"], timeout=20)
    except Exception as exc:
        return f"[ERROR] failed to check codex version: {exc}"

    version_text = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0:
        return (
            f"[ERROR] codex exists but check failed (exit={proc.returncode})\n"
            f"binary={codex_bin}\n"
            f"output={version_text}"
        )
    return f"[OK] codex available\nbinary={codex_bin}\nversion={version_text}"


def codex_exec(
    task: str,
    workspace: str = ".",
    model: str = "",
    full_auto: bool = True,
    sandbox: str = "workspace-write",
    json_output: bool = False,
    timeout_sec: int = 1800,
    poll_sec: int = 15,
    max_chars: int = 20000,
    extra_args: str = "",
    output_last_message_file: str = "",
    skip_git_repo_check: bool = False,
    ephemeral: bool = False,
    codex_home: str = "",
) -> str:
    """
    Run `codex exec` and return structured stdout/stderr.
    """
    if not task or not task.strip():
        return "[ERROR] task is empty"

    base = _resolve_dir(workspace)
    if base is None:
        return f"[ERROR] invalid workspace: {workspace}"

    codex_bin = _find_codex_binary()
    if not codex_bin:
        return "[ERROR] codex not found in PATH"

    # IMPORTANT (Windows compatibility):
    # pass prompt via stdin (`-`) to avoid argument truncation/splitting
    # when task contains newlines or special characters.
    cmd: List[str] = [codex_bin, "exec", "--cd", str(base)]

    if model and str(model).strip():
        cmd.extend(["--model", str(model).strip()])

    if _to_bool(full_auto, default=True):
        cmd.append("--full-auto")

    sandbox_text = str(sandbox or "").strip()
    if sandbox_text:
        cmd.extend(["--sandbox", sandbox_text])

    if _to_bool(json_output, default=False):
        cmd.append("--json")

    output_last_message_path = str(output_last_message_file or "").strip()
    if output_last_message_path:
        cmd.extend(["--output-last-message", output_last_message_path])

    if _to_bool(skip_git_repo_check, default=False):
        cmd.append("--skip-git-repo-check")

    if _to_bool(ephemeral, default=False):
        cmd.append("--ephemeral")

    if extra_args and str(extra_args).strip():
        try:
            cmd.extend(shlex.split(str(extra_args)))
        except Exception:
            return f"[ERROR] invalid extra_args: {extra_args}"

    # Read prompt from stdin
    cmd.append("-")

    timeout = _to_int(timeout_sec, 1800, minimum=30)
    poll = _to_int(poll_sec, 15, minimum=3)
    extra_env = {}
    if codex_home and str(codex_home).strip():
        extra_env["CODEX_HOME"] = str(codex_home).strip()
    print(
        f"[CODEX] start: workspace={base} timeout={timeout}s sandbox={sandbox_text or 'default'}",
        flush=True,
    )
    try:
        proc = _run_subprocess_with_heartbeat(
            cmd,
            timeout=timeout,
            cwd=base,
            stdin_text=task,
            heartbeat_sec=poll,
            extra_env=extra_env,
        )
    except subprocess.TimeoutExpired:
        return (
            "[CODEX_CMD]\n"
            + " ".join(cmd)
            + "\n[TIMEOUT]\n"
            + f"{timeout}s"
        )
    except Exception as exc:
        return f"[ERROR] codex execution failed: {exc}"

    stdout = _truncate(proc.stdout or "", max_chars)
    stderr = _truncate(proc.stderr or "", max_chars)
    last_message = ""
    if output_last_message_path:
        try:
            last_message = Path(output_last_message_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            last_message = ""
    return (
        "[CODEX_CMD]\n"
        + " ".join(cmd)
        + "\n"
        + f"[EXIT_CODE] {proc.returncode}\n"
        + "[LAST_MESSAGE]\n"
        + _truncate(last_message, max_chars)
        + "\n"
        + "[STDOUT]\n"
        + stdout
        + "\n"
        + "[STDERR]\n"
        + stderr
    )


def run_codex_direct_publish(context: object) -> str:
    """
    Workflow handler for single-step direct publish.
    This bypasses LLM tool-orchestration and calls Codex CLI directly.
    """
    variables = getattr(context, "variables", {}) or {}

    project_root = str(variables.get("project_root", "."))
    task_goal = str(variables.get("task_goal", "")).strip()
    codex_model = str(variables.get("codex_model", "")).strip()
    codex_full_auto = _to_bool(variables.get("codex_full_auto", False), default=False)
    codex_sandbox = str(variables.get("codex_sandbox", "read-only")).strip() or "read-only"
    codex_timeout_sec = _to_int(variables.get("codex_timeout_sec", 60), 60, minimum=10)
    codex_poll_sec = _to_int(variables.get("codex_poll_sec", 15), 15, minimum=3)
    codex_extra_args = str(variables.get("codex_extra_args", "")).strip()
    codex_output_mode = str(variables.get("codex_output_mode", "brief")).strip().lower()
    codex_debug_file = str(variables.get("codex_debug_file", "")).strip()
    codex_runtime_mode = str(variables.get("codex_runtime_mode", "native")).strip().lower() or "native"
    codex_isolated_copy = _to_bool(
        variables.get("codex_isolated_copy", codex_runtime_mode != "native"),
        default=(codex_runtime_mode != "native"),
    )
    codex_use_temp_home = _to_bool(
        variables.get("codex_use_temp_home", codex_runtime_mode != "native"),
        default=(codex_runtime_mode != "native"),
    )
    codex_preload_context = _to_bool(
        variables.get("codex_preload_context", codex_runtime_mode != "native"),
        default=(codex_runtime_mode != "native"),
    )
    codex_allow_native_tools = _to_bool(
        variables.get("codex_allow_native_tools", codex_runtime_mode == "native"),
        default=(codex_runtime_mode == "native"),
    )
    codex_ephemeral = _to_bool(
        variables.get("codex_ephemeral", codex_runtime_mode != "native"),
        default=(codex_runtime_mode != "native"),
    )
    codex_reasoning_effort = str(variables.get("codex_reasoning_effort", "medium")).strip() or "medium"
    codex_context_budget_chars = _to_int(variables.get("codex_context_budget_chars", 60000), 60000, minimum=5000)
    codex_copy_excludes = _split_csv(
        variables.get(
            "codex_copy_excludes",
            ".git,node_modules,.venv,venv,__pycache__,dist,build,coverage,.pytest_cache,.next,.turbo",
        )
    )

    if not task_goal:
        task_goal = "Analyze the project architecture, features, and key code logic."

    check_result = check_codex_cli()
    if check_result.startswith("[ERROR]"):
        return check_result

    source_root = _resolve_dir(project_root)
    if source_root is None:
        return f"[ERROR] invalid workspace: {project_root}"

    temp_root: Optional[Path] = None
    temp_codex_home: Optional[Path] = None
    exec_workspace = source_root
    exec_sandbox = codex_sandbox
    skip_git_repo_check = False
    if codex_isolated_copy:
        temp_root = _create_mirror_workspace(source_root, codex_copy_excludes)
        exec_workspace = temp_root
        skip_git_repo_check = True
        if exec_sandbox == "read-only":
            exec_sandbox = "workspace-write"

    output_last_message_path = Path(tempfile.mkstemp(prefix="codex_last_message_", suffix=".md")[1])

    env_base_url = (os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or "").strip()
    env_api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    home_model = codex_model.strip()
    if not home_model:
        env_model = (os.getenv("PRAISONAI_MODEL") or "").strip()
        if "/" in env_model:
            env_model = env_model.split("/")[-1].strip()
        home_model = env_model or "gpt-5.4"
    if codex_use_temp_home and env_base_url and env_api_key:
        temp_codex_home = _create_temp_codex_home(
            base_url=env_base_url,
            api_key=env_api_key,
            model=home_model,
            reasoning_effort=codex_reasoning_effort,
        )

    prompt_parts = [
        f"请在目录 \"{project_root}\" 执行任务：\n{task_goal}",
        (
            "硬性约束：\n"
            "1) 只分析，不修改任何代码、配置、文档和文件；\n"
            "2) 输出中文 markdown，覆盖：整体架构、功能详细描述、关键代码逻辑与调用链；\n"
            "3) 若信息不足请显式标注不确定性；\n"
            "4) 不要输出执行过程、寒暄、说明性前言，只输出最终报告正文。"
        ),
    ]

    if codex_allow_native_tools:
        prompt_parts.append(
            "请按 Codex 原生方式自行读取项目、使用你当前可用的 skills 和 tools 完成分析。"
        )
    else:
        prompt_parts.append(
            "默认禁止执行任何 shell/tool 调用、禁止再次读取文件，只允许基于下述预采样上下文直接完成分析；如果上下文不足，只在报告中标注不确定性，不要自行补充扫描。"
        )

    if codex_preload_context:
        project_context = _build_project_context(
            source_root,
            excludes=codex_copy_excludes,
            budget_chars=codex_context_budget_chars,
        )
        prompt_parts.append(project_context)

    codex_task = "\n\n".join(prompt_parts)
    try:
        exec_result = codex_exec(
            task=codex_task,
            workspace=str(exec_workspace),
            model=codex_model,
            full_auto=codex_full_auto,
            sandbox=exec_sandbox,
            timeout_sec=codex_timeout_sec,
            poll_sec=codex_poll_sec,
            extra_args=codex_extra_args,
            output_last_message_file=str(output_last_message_path),
            skip_git_repo_check=skip_git_repo_check,
            ephemeral=codex_ephemeral,
            codex_home=str(temp_codex_home) if temp_codex_home else "",
        )
        if codex_output_mode == "raw":
            return f"{check_result}\n\n{exec_result}"

        exit_code_text = _extract_section(exec_result, "[EXIT_CODE]", "[LAST_MESSAGE]").strip()
        last_message_text = _extract_section(exec_result, "[LAST_MESSAGE]", "[STDOUT]").strip()
        stdout_text = _extract_section(exec_result, "[STDOUT]", "[STDERR]").strip()
        stderr_text = _extract_section(exec_result, "[STDERR]").strip()
        exit_code = None
        if exit_code_text:
            first_line = exit_code_text.splitlines()[0].strip()
            try:
                exit_code = int(first_line)
            except Exception:
                exit_code = None

        clean_body = last_message_text or stdout_text
        if exit_code == 0 and clean_body:
            return clean_body

        debug_hint = ""
        if codex_debug_file:
            try:
                debug_path = Path(codex_debug_file)
                if not debug_path.is_absolute():
                    debug_path = Path.cwd() / debug_path
                debug_path.parent.mkdir(parents=True, exist_ok=True)
                debug_path.write_text(f"{check_result}\n\n{exec_result}\n", encoding="utf-8")
                debug_hint = f"\n调试日志：{debug_path}"
            except Exception as exc:
                debug_hint = f"\n调试日志写入失败：{exc}"

        brief_stderr = _tail_lines(stderr_text, max_lines=24, max_chars=2400)
        if not brief_stderr:
            brief_stderr = _tail_lines(exec_result, max_lines=24, max_chars=2400)

        status_text = str(exit_code) if exit_code is not None else "unknown"
        return (
            "## Codex 执行失败\n\n"
            f"- exit_code: {status_text}\n"
            f"- workspace: {project_root}\n"
            f"- effective_workspace: {exec_workspace}\n"
            f"- sandbox: {exec_sandbox}{debug_hint}\n\n"
            "```text\n"
            f"{brief_stderr or '未捕获到错误输出'}\n"
            "```"
        )
    finally:
        try:
            output_last_message_path.unlink(missing_ok=True)
        except Exception:
            pass
        if temp_root is not None:
            try:
                shutil.rmtree(temp_root, ignore_errors=True)
            except Exception:
                pass
        if temp_codex_home is not None:
            try:
                shutil.rmtree(temp_codex_home, ignore_errors=True)
            except Exception:
                pass


def append_current_date(context: object) -> str:
    """
    Append current date to previous step output.
    """
    variables = getattr(context, "variables", {}) or {}
    previous = getattr(context, "previous_result", None)
    if previous is None:
        previous = variables.get("codex_analysis_text", "")
    body = str(previous or "").strip()
    if not body:
        body = "[EMPTY_ANALYSIS_OUTPUT]"

    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"{body}\n\n---\n生成日期：{date_str}\n"
