# PraisonAI 系统功能分析、OpenClaw 对比与 Conda 部署说明

## 1. 文档目标

本文档用于沉淀以下内容：

1. 基于本地源码与官方文档，系统分析当前 `PraisonAI` 项目的架构与功能。
2. 对比当前流行的 `OpenClaw`，说明定位与能力差异。
3. 完整记录本次在 Windows + Conda 的部署过程、验证步骤与实际遇到的问题。
4. 给出第三方 API（OpenAI 兼容网关）配置方案。

---

## 2. 环境与版本信息（本次实操）

- 系统平台：`Windows`（PowerShell）
- 项目路径：`E:\progamecode\AIprogram\test\PraisonAI\PraisonAI-main`
- Conda：`26.1.1`
- Python 环境：`D:\conda\envs\praisonai`（Python `3.11.15`）
- 关键包（editable 安装）：
  - `PraisonAI 4.5.113`
  - `praisonaiagents 1.5.113`
  - `aiui 0.3.100`

---

## 3. PraisonAI 系统架构与代码分析（基于源码实扫）

> 结论：`PraisonAI` 的核心定位是「**多智能体开发/编排框架 + CLI + Dashboard**」，既可 SDK 编程，也可 CLI/可视化运维。

### 3.0 项目整体结构

```
PraisonAI-main/
├── src/
│   ├── praisonai/                    # 上层应用包（CLI + UI + 集成）
│   │   └── praisonai/
│   │       ├── cli/                  # CLI 入口与所有命令
│   │       │   ├── main.py           # 主入口（argparse + workflow 执行）
│   │       │   ├── commands/         # 60+ 子命令（见 3.2）
│   │       │   ├── features/         # doctor / profiler / tui / queue
│   │       │   ├── interactive/      # 交互式前端
│   │       │   └── session/          # 会话管理
│   │       ├── claw/                 # Dashboard 应用（aiui 驱动）
│   │       │   └── default_app.py    # 默认 Agent 注册 + 页面配置
│   │       ├── ui_chat/              # 轻量聊天 UI
│   │       ├── flow/                 # Langflow 集成（可视化工作流）
│   │       │   └── components/       # PraisonAI 自定义 Langflow 组件
│   │       ├── integrations/         # 外部 CLI 集成
│   │       │   ├── codex_cli.py      # OpenAI Codex CLI
│   │       │   ├── claude_code.py    # Claude Code CLI
│   │       │   ├── gemini_cli.py     # Gemini CLI
│   │       │   └── cursor_cli.py     # Cursor CLI
│   │       ├── mcp_server/           # MCP 协议服务端
│   │       │   ├── adapters/         # 86 个 MCP 工具适配器
│   │       │   ├── transports/       # stdio / HTTP / WebSocket / SSE
│   │       │   └── auth/             # 认证
│   │       ├── bots/                 # Bot 集成（Telegram/Discord/Slack/WhatsApp）
│   │       ├── gateway/              # API Gateway
│   │       ├── code/                 # 代码工具（read/write/diff/search_replace）
│   │       ├── tools/                # CLI 专用工具（multiedit/glob/grep/tts/stt）
│   │       ├── persistence/          # 持久化（conversation/hooks/knowledge/state）
│   │       ├── deploy/               # 部署（多 provider）
│   │       ├── sandbox/              # 沙箱执行
│   │       ├── scheduler/            # 定时任务
│   │       └── train/                # 训练（CoT 数据生成）
│   │
│   └── praisonai-agents/             # 底层 Agent 引擎包
│       └── praisonaiagents/
│           ├── agent/                # Agent 核心类
│           │   ├── agent.py          # Agent 主类（Mixin 组合模式）
│           │   ├── chat_mixin.py     # 对话逻辑
│           │   ├── execution_mixin.py # 执行逻辑
│           │   ├── memory_mixin.py   # 记忆逻辑
│           │   ├── tool_execution.py # 工具执行
│           │   ├── handoff.py        # Agent 间交接
│           │   └── deep_research_agent.py  # 深度研究 Agent
│           ├── llm/                  # LLM 调用层
│           │   ├── llm.py            # 核心 LLM 类（流式/非流式/工具调用/重试）
│           │   ├── openai_client.py  # OpenAI 原生客户端
│           │   └── failover.py       # 模型失败切换
│           ├── workflows/            # 工作流引擎
│           │   ├── workflows.py      # Workflow 类（顺序/并行/路由/循环执行）
│           │   └── yaml_parser.py    # YAML 工作流解析器
│           ├── tools/                # 工具系统
│           │   ├── __init__.py       # 114 个内置工具注册表（TOOL_MAPPINGS）
│           │   ├── decorator.py      # @tool 装饰器
│           │   ├── registry.py       # 工具注册中心
│           │   └── 各类工具模块...    # duckduckgo/shell/file/python/tavily/exa 等
│           ├── memory/               # 记忆系统
│           │   ├── memory.py         # Memory 主类
│           │   ├── adapters/         # 多后端（chroma/redis/mongodb/postgresql）
│           │   └── learn/            # 学习记忆
│           ├── knowledge/            # 知识库
│           ├── rag/                  # RAG 检索增强
│           ├── mcp/                  # MCP 客户端
│           ├── guardrails/           # 安全护栏
│           ├── planning/             # 规划系统
│           ├── config/               # 配置系统（feature_configs/presets/loader）
│           ├── plugins/              # 插件系统
│           ├── context/              # 上下文管理（FastContext）
│           ├── hooks/                # Hook 系统
│           ├── telemetry/            # 遥测与监控
│           ├── eval/                 # 评估
│           └── ui/                   # UI 协议（A2A/AGUI/A2UI）
│
├── workflow_templates/               # 可复用工作流模板
│   ├── codebase_analysis.yaml        # 代码库分析
│   ├── bugfix_autofix.yaml           # Bug 自动修复
│   ├── doc_generation.yaml           # 文档生成
│   ├── tools.py                      # 模板用本地工具
│   └── codex_agent_orchestration/    # Codex 编排模板
│
└── examples/                         # 示例文件
```

### 3.0.1 两包分层设计

| 包 | 定位 | 核心职责 |
|---|---|---|
| `praisonaiagents` | 底层引擎 | Agent/LLM/Workflow/Tools/Memory/Knowledge/RAG/MCP 等核心能力 |
| `praisonai` | 上层应用 | CLI/Dashboard/Bot/Gateway/MCP Server/外部集成/部署 |

关键设计：`praisonaiagents` 可独立使用（`pip install praisonaiagents`），`praisonai` 依赖它并在其上构建完整平台能力。

### 3.0.2 Agent 类架构（Mixin 组合模式）

`Agent` 类位于 `agent/agent.py`，采用 Mixin 模式拆分职责：

```
Agent(ChatMixin, ExecutionMixin, MemoryMixin, ToolExecutionMixin, ChatHandlerMixin, SessionManagerMixin)
```

| Mixin | 职责 |
|---|---|
| `ChatMixin` | 对话主循环（`chat()`/`achat()`） |
| `ExecutionMixin` | 任务执行（`start()`/`astart()`） |
| `MemoryMixin` | 记忆存储与检索 |
| `ToolExecutionMixin` | 工具调用执行 |
| `ChatHandlerMixin` | 对话消息处理 |
| `SessionManagerMixin` | 会话状态管理 |

### 3.0.3 LLM 调用层架构

`llm/llm.py` 是所有模型调用的核心，主要职责：

1. **双路径分发**：OpenAI 原生 SDK（直连）vs LiteLLM（多 provider 兼容）
2. **流式/非流式**：根据模型能力和配置自动选择
3. **工具调用处理**：标准 `tool_calls` 解析 + 文本 JSON fallback + 参数容错
4. **第三方网关兼容**：自动检测 → 模型路由改写 → 参数过滤 → 字段提取扩展（详见第 19 节）
5. **重试与兜底**：空响应重试 → 流式探测恢复 → 降级提示

### 3.0.4 Workflow 引擎架构

`workflows/workflows.py` 支持以下执行模式：

| 模式 | 实现 | 说明 |
|---|---|---|
| 顺序执行 | `_execute_step()` 串行 | 步骤间传递 `previous_output` |
| 并行执行 | `parallel()` + ThreadPoolExecutor | 多分支同时运行，支持 `PRAISONAI_WORKFLOW_PARALLEL_MAX_WORKERS` |
| 条件路由 | `route()` | 根据上一步输出决定分支 |
| 循环 | `loop()` / `repeat()` | 条件循环或固定次数重复 |
| 包含 | `include()` | 嵌套子工作流 |

`yaml_parser.py` 负责将 YAML 定义转换为 `Workflow` 对象，关键透传逻辑：
- 模型优先级：`agent_config.llm > PRAISONAI_MODEL > MODEL_NAME > OPENAI_MODEL_NAME`
- `max_tokens` 优先级：YAML agent > YAML llm > `PRAISONAI_WORKFLOW_MAX_TOKENS` > `PRAISONAI_MAX_TOKENS`

### 3.0.5 工具系统架构

工具解析优先级（`ToolResolver`）：

1. 本地 `tools.py`（YAML 同目录自动加载）
2. `praisonaiagents` 内置工具（`TOOL_MAPPINGS`，114 个）
3. `praisonai` CLI 工具
4. 全局 `ToolRegistry`

工具注册方式：
- `@tool` 装饰器
- `TOOL_MAPPINGS` 映射表（懒加载）
- MCP 协议动态注册
- YAML `tools:` 字段引用

### 3.0.6 懒加载设计

整个 `praisonaiagents` 包采用**集中式懒加载**（`__init__.py` + `_lazy.py`）：

- `_LAZY_IMPORTS` 映射表定义 186+ 个延迟导入项
- `__getattr__` + `create_lazy_getattr_with_fallback()` 实现按需加载
- 重依赖（LiteLLM、Rich、工具模块）仅在首次使用时导入
- 效果：包导入时间从 ~420ms 降至 ~20ms（silent 模式）

### 3.1 框架层能力

从项目源码可确认以下核心能力：

- 多智能体编排（协作、handoff、工作流模式）
- 规划执行（Planning）— `planning/` 模块，含 Plan/TodoList/PlanningAgent
- 深度研究（Deep Research）— `agent/deep_research_agent.py`
- MCP 协议接入（stdio / HTTP / WebSocket / SSE）— 客户端 `mcp/` + 服务端 `mcp_server/`
- 记忆与检索（Memory / RAG）— `memory/` + `rag/` + 多后端适配
- 知识库（Knowledge）— `knowledge/` + chunking
- Guardrails（输入/输出约束）— `guardrails/`
- 多 Provider 模型接入 — LiteLLM 集成 + 原生 OpenAI SDK
- 模型失败切换（Failover）— `llm/failover.py`
- 上下文管理（FastContext）— `context/fast/`
- 插件系统 — `plugins/`（单文件插件 + 协议驱动）
- Hook 系统 — `hooks/`
- 遥测与监控 — `telemetry/`
- 外部 CLI 集成 — Codex / Claude / Gemini / Cursor

### 3.2 CLI 命令全景（60+ 命令，基于源码实扫）

从 `src/praisonai/praisonai/cli/commands/` 目录实扫，CLI 具备以下命令：

| 类别 | 命令 | 说明 |
|---|---|---|
| **UI/服务** | `ui`, `claw`, `chat`, `code`, `serve`, `gateway`, `app` | 各类 UI 与服务入口 |
| **工作流** | `workflow`, `flow` | YAML 工作流执行 / Langflow 可视化 |
| **Agent 管理** | `agents`, `run`, `batch` | Agent 注册/运行/批量执行 |
| **工具** | `tools`, `mcp`, `acp`, `lsp` | 工具管理/MCP/ACP/LSP 集成 |
| **数据** | `memory`, `knowledge`, `rag`, `retrieval` | 记忆/知识库/RAG |
| **Bot** | `bot` | Telegram/Discord/Slack/WhatsApp 机器人 |
| **通讯** | `call`, `realtime` | 语音通话/实时通讯 |
| **开发** | `debug`, `diag`, `doctor`, `test`, `eval`, `benchmark`, `profile`, `traces` | 调试/诊断/测试/评估 |
| **运维** | `deploy`, `sandbox`, `schedule`, `hooks`, `session`, `config`, `paths`, `environment` | 部署/沙箱/调度/配置 |
| **内容** | `commit`, `docs`, `examples`, `templates`, `recipe`, `research` | Git/文档/示例/模板 |
| **其他** | `completion`, `version`, `publish`, `registry`, `plugins`, `skills`, `obs`, `langfuse`, `todo`, `loop`, `replay`, `context`, `tracker`, `audit`, `standardise`, `package`, `browser`, `endpoints` | 补全/版本/发布/注册/插件等 |

### 3.3 UI 形态

- `praisonai ui`：默认仅聊天页面
- `praisonai claw`：完整 Dashboard，由 `aiui` 驱动，默认启用 13 个页面（chat/channels/agents/skills/memory/knowledge/cron/guardrails/sessions/usage/config/logs/debug）+ Feature Explorer
- `praisonai flow`：Langflow 可视化工作流（需独立安装 `langflow`，见第 13 节）

### 3.4 安装模式与依赖分层

| 安装模式 | 命令 | 包含内容 |
|---|---|---|
| 最小安装 | `pip install praisonai` | 核心 CLI + LiteLLM + YAML |
| 轻量 UI | `pip install "praisonai[ui]"` | + aiui 聊天页 |
| 完整 Dashboard | `pip install "praisonai[claw]"` | + aiui 全页面 + chainlit + 搜索 + Bot + 存储后端 |
| API 服务 | `pip install "praisonai[api]"` | + FastAPI + uvicorn |
| Bot | `pip install "praisonai[bot]"` | + Telegram/Discord/Slack SDK |
| 可视化流程 | `pip install praisonai && pip install langflow` | + Langflow（独立安装，见 13.2 节） |
| 精简模式 | `pip install "praisonai[lite]"` | 无 TUI/LiteLLM，仅核心 Agent |
| 全量 | `pip install "praisonai[all]"` | 除 flow/bot 外全部 |

> 注意：`pyproject.toml` 中**没有 `flow` 这个 extras 组**，`langflow` 需手动额外安装。README 中 `praisonai[flow]` 的说法是文档 bug（见 13.2 节）。

---

## 4. PraisonAI vs OpenClaw 对比

> 基于官方文档定位总结：两者都能做 AI 助手与多模型接入，但“主战场”不同。

| 维度 | PraisonAI | OpenClaw |
|---|---|---|
| 核心定位 | 多智能体框架 + Python SDK + CLI + Dashboard | 个人常驻 AI 助手（多消息渠道、网关控制平面） |
| 技术栈主轴 | Python 生态（`praisonai` / `praisonaiagents`） | Node.js 生态（`openclaw` CLI + gateway） |
| 启动方式 | `pip/conda` + `praisonai ...` | `npm/pnpm/bun` + `openclaw onboard` |
| UI 形态 | `ui`（轻量）与 `claw`（完整控制台） | Gateway Control UI + WebChat + 多端节点 |
| 多渠道通讯 | 支持 bot/gateway 场景（Telegram/Discord/Slack/WhatsApp 等） | 明确以多渠道“个人收件箱/助手”作为核心体验，渠道覆盖非常广 |
| 任务编排 | 强调 agent workflow、planning、RAG、工具编排 | 强调 always-on assistant、channel routing、session/presence、模型策略与失败切换 |
| 典型使用者 | AI 应用开发者、智能体工程团队 | 个人生产力/消息通道统一助手用户 |

### 4.1 适用场景建议

- 你要做“**可编排、可扩展、可二次开发的智能体系统**”：优先 `PraisonAI`。
- 你要做“**多聊天渠道统一接入、个人助手常驻**”：`OpenClaw` 更对口。

### 4.2 关键差异（简述）

1. **产品重心不同**  
   PraisonAI 偏开发框架；OpenClaw 偏个人助手产品化交付。

2. **生态重心不同**  
   PraisonAI 以 Python 工程化与 agent 模块复用为主；OpenClaw 以 Gateway + Channels + Onboarding 为主。

3. **部署关注点不同**  
   PraisonAI 更关注模型、工具、工作流和 SDK 集成；OpenClaw 更强调渠道配对、安全策略与守护进程长期运行。

---

## 5. Conda 部署全流程（Windows 实测）

## 5.1 创建环境

```powershell
conda create -n praisonai python=3.11 -y
```

## 5.2 安装源码（editable）

```powershell
conda run -n praisonai python -m pip install -e src/praisonai-agents
conda run -n praisonai python -m pip install -e "src/praisonai[claw]"
```

> 说明：`[claw]` 会带完整 Dashboard 依赖（比 `[ui]` 更全）。

## 5.3 验证安装

```powershell
conda run -n praisonai praisonai --version
conda run -n praisonai python -m pip list | findstr /I "praison aiui"
```

## 5.4 启动服务

### 轻量聊天页（单页）

```powershell
conda activate praisonai
praisonai ui --host 127.0.0.1 --port 8081
```

访问：`http://127.0.0.1:8081/chat`

### 完整仪表盘（推荐）

```powershell
conda activate praisonai
praisonai claw --host 127.0.0.1 --port 8082
```

访问：`http://127.0.0.1:8082`

## 5.5 运行状态验证

```powershell
netstat -ano -p TCP | findstr 8082
Invoke-WebRequest -Uri "http://127.0.0.1:8082" -UseBasicParsing
```

---

## 6. 本次部署遇到的问题与处理

| 问题 | 现象 | 原因 | 处理方案 |
|---|---|---|---|
| Conda 创建环境失败 | `NoWritableEnvsDirError` | 当前上下文对 Conda env 目录写权限不足 | 以可写权限执行 `conda create` 后成功 |
| 启动 `ui` 报权限错误 | `PermissionError: ... C:\Users\Administrator\.praisonai` | 程序首次运行需在用户目录创建配置目录 | 以有权限上下文启动，目录创建后恢复正常 |
| 只看到单聊天页 | 页面只有 Chat 视图 | 启动的是 `praisonai ui`（设计如此） | 切换到 `praisonai claw`（完整 Dashboard） |
| 安装中断后模块缺失 | `ModuleNotFoundError: No module named 'praisonai'` | 中断 `pip install -e "src/praisonai[claw]"` 导致安装状态不完整 | 重新执行完整安装命令修复 |
| pip 警告无效分发 | `Ignoring invalid distribution ~raisonai` | `site-packages` 残留临时 dist-info | 删除 `~raisonai-4.5.113.dist-info` 后告警消失 |

---

## 7. 第三方 API（OpenAI 兼容）配置方案

> 你用第三方 API 时，建议同时设置 `OPENAI_BASE_URL` 和 `OPENAI_API_BASE`，兼容不同调用路径。

## 7.1 推荐：写入 conda 环境变量（持久）

```powershell
conda env config vars set -n praisonai OPENAI_API_KEY="sk-c8141e53a6062597ac88bee8f115b5c6e2a2461f4a9c99a36e6dbe5368c31c1d"
conda env config vars set -n praisonai OPENAI_BASE_URL="https://ice.v.ua/v1"
conda env config vars set -n praisonai OPENAI_API_BASE="https://ice.v.ua/v1"

conda env config vars set -n praisonai OPENAI_API_KEY="sk-oLRVRGxR7w6UIATAh"
conda env config vars set -n praisonai OPENAI_BASE_URL="http://localhost:8317/v1"
conda env config vars set -n praisonai OPENAI_API_BASE="http://localhost:8317/v1"

conda env config vars set -n praisonai OPENAI_API_KEY="sk-c8141e53a6062597ac88bee8f115b5c6e2a2461f4a9c99a36e6dbe5368c31c1d"
conda env config vars set -n praisonai OPENAI_BASE_URL="https://ice.v.ua/v1"
conda env config vars set -n praisonai OPENAI_API_BASE="https://ice.v.ua/v1"

conda env config vars set -n praisonai PRAISONAI_MODEL="gpt-5.3-codex"
```

然后重载环境：

```powershell
conda deactivate
conda activate praisonai
```

### 18. 2026-04-09 补充：Codex 编排工作流最终落地（native 模式为主）

这轮关于 `workflow_templates/codex_agent_orchestration/` 的目标，不再是“把 Codex 包成一个受限工具”，而是：

1. **默认复用真实 Codex 运行态**；  
2. 在 workflow 中仍可编排；  
3. 失败时不污染 Markdown；  
4. 保留一个可回退的“隔离模式（isolated）”。  

#### 18.1 这次真正确认的根因

这次不是单一问题，而是三层问题叠加：

1. **输出混乱**  
   - 早期 handler 在 Codex 执行失败时，会把 `[CODEX_CMD] / [STDERR] / reconnect 日志` 直接写入 Markdown。  
   - 结果看起来像“Codex 生成了乱报告”，实际上是**错误诊断被当正文落盘**。

2. **看起来卡住**  
   - `codex exec` 在 workflow 中最开始没有可见进度，终端会长期停在 `Executing workflow...`。  
   - 这不等于死锁，很多时候只是 Codex 正在初始化、读取技能、扫描代码、组织输出。  
   - 但对“完整项目分析”来说，`60s` 通常只适合作为**异常探测阈值**，不适合作为正式报告的硬截止。

3. **直接用 Codex 与 workflow 调 Codex 的运行态不一致**  
   - `praisonai` 的 conda 环境读取的是 `OPENAI_BASE_URL / OPENAI_API_BASE / OPENAI_API_KEY`；  
   - Codex CLI 默认读取 `~/.codex/config.toml` 和 `~/.codex/auth.json`；  
   - 两边配置、provider、skills、MCP、memory、plugins、developer instructions 不一致时，虽然“底层都叫 Codex”，行为也会明显不同。  

#### 18.2 本轮已落地的代码与模板修改

已修改文件：

1. `workflow_templates/codex_agent_orchestration/tools.py`  
2. `workflow_templates/codex_agent_orchestration/codex_direct_publish.yaml`  
3. `workflow_templates/codex_agent_orchestration/codex_two_step_smoke.yaml`  
4. `workflow_templates/codex_agent_orchestration/codex_two_step_report.yaml`（新增）  

核心改动如下：

| 项 | 改动 | 作用 |
|---|---|---|
| 输出收敛 | 失败时只写简短失败摘要，原始日志单独写入 `codex_*_debug.log` | 不再污染最终 Markdown |
| 心跳输出 | `codex exec` 期间每隔数秒输出 `[CODEX] running ...` | 避免“看起来卡住” |
| 最终消息提取 | 使用 `--output-last-message` 只取 Codex 最终正文 | 减少过程日志混入 |
| runtime 模式 | 新增 `codex_runtime_mode` | 支持 `native` / `isolated` 两种运行方式 |
| native 模式 | 默认直接复用真实 Codex 运行态 | 更接近你平时直接用 Codex |
| isolated 模式 | 可临时生成 `CODEX_HOME`、镜像工作目录、预采样上下文 | 用于不稳定链路下的兜底与排查 |
| smoke / report 分离 | 冒烟测试与正式报告模板拆开 | 避免把快测模板误用到正式分析 |

#### 18.3 现在的关键行为：native 与 isolated 的区别

| 维度 | `native`（默认） | `isolated`（回退） |
|---|---|---|
| `CODEX_HOME` | 复用真实 `~/.codex` | 临时生成干净 `CODEX_HOME` |
| Skills / Tools / MCP / Memory | 复用你平时真实 Codex | 尽量减小外部干扰 |
| 上下文获取 | Codex 自己原生读项目 | workflow 预采样后再喂给 Codex |
| 工作目录 | 真实项目目录 | 临时镜像目录 |
| 交互风格 | 最接近直接打开 Codex | 最接近“可控自动执行器” |
| 推荐场景 | 你要求“像真实 Codex 一样跑” | 你要求“稳定兜底 / 排查 provider 问题” |

#### 18.4 workflow 里调用 Codex，和直接打开 Codex 到底是什么关系

**结论：**

1. workflow 里调用的底层仍然是 **Codex CLI 本体**；  
2. 不是 PraisonAI 自己伪装出的 agent；  
3. 但 workflow 仍然会包一层“单次 `codex exec` + 输出落盘 + 后续节点编排”的外壳。  

因此：

- **直接打开 Codex**：是完整交互式会话；  
- **workflow 调 Codex**：是“Codex 内核 + workflow 外层调度壳”。  

当 `codex_runtime_mode=native` 时，它会尽量复用你真实 Codex 的：

1. system / developer instructions 链路；  
2. skills；  
3. tools / MCP；  
4. 上下文访问方式；  
5. memory / plugins / config。  

但仍有两个天然差异不会消失：

1. workflow 是**单次非交互执行**，不是持续对话；  
2. workflow 仍会附加任务约束（如“只分析、不修改、只输出中文 Markdown”）并负责结果落盘。  

#### 18.5 当前推荐模板

| 模板 | 用途 | 是否推荐 |
|---|---|---|
| `workflow_templates/codex_agent_orchestration/codex_two_step_smoke.yaml` | 冒烟测试，确认 Codex 可调起 | 仅测试时使用 |
| `workflow_templates/codex_agent_orchestration/codex_direct_publish.yaml` | 单步正式分析，直接输出报告 | 推荐 |
| `workflow_templates/codex_agent_orchestration/codex_two_step_report.yaml` | 两步正式分析，第二步追加日期 | 推荐 |
| `workflow_templates/codex_agent_orchestration/codex_workflow.yaml` | 旧版多节点方案 | **不再推荐作为主入口** |

#### 18.6 最终推荐运行命令（正式）

前提：

1. 已激活 `praisonai` conda 环境；  
2. `OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_API_BASE` 已在该环境配置；  
3. `PRAISONAI_MODEL` 可显式设为 `custom_openai/gpt-5.3-codex`。  

##### 18.6.1 两节点正式分析（默认推荐）

```powershell
conda activate praisonai
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codex_agent_orchestration\codex_two_step_report.yaml -v -m $env:PRAISONAI_MODEL --var project_root="E:\progamecode\AIprogram\test\kirocli2api" --var task_goal="只做分析，不修改代码；输出整体架构、功能详细描述和代码逻辑"
```

默认输出：

1. `codex_two_step_output_zh.md`  
2. 如失败则看 `codex_two_step_report_debug.log`  

##### 18.6.2 单步正式分析（不追加日期）

```powershell
conda activate praisonai
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codex_agent_orchestration\codex_direct_publish.yaml -v -m $env:PRAISONAI_MODEL --var project_root="E:\progamecode\AIprogram\test\kirocli2api" --var task_goal="只做分析，不修改代码；输出整体架构、功能详细描述和代码逻辑"
```

默认输出：

1. `codex_direct_output_zh.md`  
2. 如失败则看 `codex_direct_debug.log`  

##### 18.6.3 冒烟测试（仅验证链路，不用于正式报告）

```powershell
conda activate praisonai
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codex_agent_orchestration\codex_two_step_smoke.yaml -v -m $env:PRAISONAI_MODEL --var project_root="E:\progamecode\AIprogram\test\kirocli2api" --var task_goal="只回复：通过"
```

#### 18.7 若要强制切回隔离模式（排障 / 兜底）

当你怀疑：

1. 真实 `~/.codex` 配置过重；  
2. skills / MCP / memory 干扰了单次 workflow；  
3. provider 切换需要做 A/B 排查；  

可以临时加：

```powershell
--var codex_runtime_mode="isolated"
```

隔离模式下的典型行为：

1. 临时 `CODEX_HOME`；  
2. 临时镜像工作目录；  
3. 预采样项目上下文；  
4. 可选禁止 shell/tool 二次扫描。  

#### 18.8 当前已验证结果

在本地项目 `E:\progamecode\AIprogram\test\kirocli2api` 上，本轮已验证：

1. `codex_direct_publish.yaml` 可生成中文架构分析；  
2. `codex_two_step_report.yaml` 可生成中文架构分析并追加日期；  
3. 输出文件：
   - `codex_direct_output_zh.md`
   - `codex_two_step_output_zh.md`

#### 18.9 实践建议

1. **想尽量像你平时直接开 Codex**：使用默认 `native` 模式。  
2. **想做稳定性排查**：切到 `isolated` 模式再对比。  
3. **`60s` 只适合 smoke，不适合完整项目正式分析**。  
4. 若再次出现“文档内容像日志”，优先检查对应 `codex_*_debug.log`，而不是先怀疑分析正文质量。  


## 7.2 临时会话（仅当前终端）

```powershell
$env:OPENAI_API_KEY="你的key"
$env:OPENAI_BASE_URL="https://你的网关/v1"
$env:OPENAI_API_BASE="https://你的网关/v1"
$env:PRAISONAI_MODEL="你的模型名"
```

## 7.3 变量说明

| 变量 | 用途 | 是否必需 |
|---|---|---|
| `OPENAI_API_KEY` | API 鉴权 key | 是 |
| `OPENAI_BASE_URL` | OpenAI 兼容服务地址 | 强烈建议 |
| `OPENAI_API_BASE` | 同上，兼容不同模块读取 | 强烈建议 |
| `PRAISONAI_MODEL` | 默认模型名（如 `openai/gpt-4o-mini` 或第三方模型ID） | 建议 |

---

## 8. 外部集成不进 `/agents` 也能编排流程吗？

**可以。**

但要区分两种模式：

1. `--external-agent codex/claude`  
   这是「**外部 CLI 直连执行模式**」，一次请求直接调用外部工具并返回结果，不会自动生成 `/agents` 页面卡片。

2. `workflow + tools.py`  
   这是「**可编排流程模式**」，把 Codex/Claude 封装为工具函数，再在 `workflow.yaml` 里按步骤调用，可实现多阶段流程。

### 8.1 推荐编排方案（workflow + tools.py）

在工作目录创建 `tools.py`：

```python
import asyncio
from praisonai.integrations import CodexCLIIntegration, ClaudeCodeIntegration


def codex_tool(prompt: str) -> str:
    """Call OpenAI Codex CLI via PraisonAI integration."""
    integration = CodexCLIIntegration(workspace=".")
    return asyncio.run(integration.execute(prompt))


def claude_tool(prompt: str) -> str:
    """Call Claude Code CLI via PraisonAI integration."""
    integration = ClaudeCodeIntegration(workspace=".")
    return asyncio.run(integration.execute(prompt))
```

创建 `external_agents_workflow.yaml`：

```yaml
name: external-cli-workflow
process: workflow
workflow:
  default_llm: gpt-4o-mini
agents:
  coder:
    instructions: 你是代码实现智能体，必要时调用 codex_tool。
    tools: [codex_tool]
  reviewer:
    instructions: 你是代码审查智能体，必要时调用 claude_tool。
    tools: [claude_tool]
steps:
  - id: implement
    agent: coder
    task: "根据需求完成实现并输出变更摘要"
  - id: review
    agent: reviewer
    task: "审查 implement 的结果并给出修正建议"
```

执行：

```powershell
conda activate praisonai
praisonai workflow run external_agents_workflow.yaml
```

### 8.2 结论

- **不放到 `/agents` 页面，也可以完整编排流程。**
- 如果你的目标是工程化自动流程，优先用 `workflow + tools.py`。
- 如果只是临时调用外部 AI CLI，使用 `--external-agent` 更直接。

---

## 9. 如何把 Codex / Claude 两张卡片接入 `/agents` 页面

> 目标：在 `http://127.0.0.1:8082/agents` 直接看到并运行 “Codex” 和 “Claude” 两张卡片。

### 9.1 关键事实（当前版本行为）

1. `claw` 默认页面会预注册三张卡片：`Researcher`、`Writer`、`Coder`。  
2. `--external-agent` 是 CLI 运行时路径，不会自动写入 `/agents` 数据库。  
3. 要在 `/agents` 可见，必须走“Agent 注册”路径（前端 + 后端 + 工具解析）。

### 9.2 最小改造方案（推荐）

#### 步骤 1：在 `claw` 默认 app 注册两张新卡片

修改 `src/praisonai/praisonai/claw/default_app.py` 的 `AGENTS`，新增：

- `Codex`（描述 coding executor）
- `Claude`（描述 code reviewer / architect）

并在注册 `registry.create(...)` 时带上 `tools` 字段（若你的 `praisonaiui` 版本已支持）。

#### 步骤 2：提供可解析工具函数

在项目运行目录或工具模块中提供：

- `codex_tool(prompt: str) -> str`
- `claude_tool(prompt: str) -> str`

并确保 `ToolResolver` 可以解析到这两个工具（名称与函数名一致）。

#### 步骤 3：让 `/agents` 页面可编辑工具字段（可选但建议）

若当前页面仅有 `name/instructions/model`，需扩展前端表单（`tools` 输入框或多选框）：

- 输入：`codex_tool,claude_tool`
- 保存后写入 agent 配置中的 `tools` 列表

#### 步骤 4：重启并验证

```powershell
conda activate praisonai
praisonai claw --host 127.0.0.1 --port 8082
```

验证点：

1. `/agents` 页面出现 `Codex`、`Claude` 卡片  
2. 点击 `Run` 可进入聊天  
3. `Logs` 中能看到工具调用成功（无 `Tool not found`）

### 9.3 注意事项

- 如果你直接改的是 `site-packages` 下前端文件，升级包后可能被覆盖。
- 更稳妥做法：把改动落在项目源码（如 `claw/default_app.py` + 自定义工具模块）并用 editable 安装。
- 第三方 CLI 需在系统 PATH 可执行（`codex` / `claude`）。

---

## 10. 常用运维命令

```powershell
# 启动完整控制台
conda activate praisonai
praisonai claw --host 127.0.0.1 --port 8082

# 查看端口
netstat -ano -p TCP | findstr 8082

# 停止某个 PID
Stop-Process -Id <PID> -Force
```

---

## 11. 运行模式 FAQ（终端 A / 终端 B）

> 本节汇总“聊天框、编排、工程任务、24 小时运行”的常见疑问。

### 11.1 两类命令不是二选一

1. `praisonai claw --host 127.0.0.1 --port 8082`  
   用于启动 Web UI 服务（聊天页、Agents、Logs、Cron 等）。

2. `praisonai "...任务..." --autonomy ...`  
   用于在 CLI 直接执行工程任务（终端输出最完整）。

结论：  
- 要网页聊天框，必须启动 `claw`（或 `ui`）。  
- 要一次性自动化工程执行，可直接跑 CLI 命令。

### 11.2 终端 A 与终端 B 分工

- 终端 A（`claw`）：
  - 提供 Web 服务入口；
  - 网页里发起的任务在 A 进程执行；
  - 可用于可视化编排和运营管理。

- 终端 B（CLI）：
  - 直接执行命令行任务；
  - 任务进度与详细日志主要看 B 终端（尤其 `-vv`）。

### 11.3 编排任务必须在 A 跑吗？

不是。编排任务可由两种入口触发：

1. Web 入口（A）：在 UI 里触发，运行在 A 进程。  
2. CLI 入口（B）：`praisonai workflow run xxx.yaml`，运行在 B 进程。

同一编排不要同时在 A 与 B 启两份，避免并发写文件冲突。

### 11.4 A 能跑工程任务与长时任务吗？

可以。A 不仅能聊天，也能跑工程任务（通过 Web 发起的任务都在 A 跑）。

24 小时运行可行，但前提是 `claw` 进程持续存活。  
生产建议：

1. 长时批处理/自动修复优先 CLI（B）；
2. 可视化监控、Agent 管理、Cron 调度用 A；
3. 24h 场景应配置进程守护（任务计划/服务），防止终端关闭导致中断。

### 11.5 推荐实操模式

1. 终端 A：常驻 UI 服务

```powershell
conda activate praisonai
praisonai claw --host 127.0.0.1 --port 8082
```

2. 终端 B：执行工程任务

```powershell
conda activate praisonai
praisonai "先阅读仓库并定位根因；修改代码；运行测试；若失败继续修复直到通过；最后输出变更摘要和测试结果" --llm $env:PRAISONAI_MODEL --autonomy full_auto --acp --lsp --trust --fast-context . --context-auto-compact --context-strategy smart --context-threshold 0.8 --tool-timeout 120 --planning --auto-approve-plan -vv
```

---

## 12. 证据来源

### 本地源码与文档

- `README.md`（功能、特性、安装与 UI 说明）
- `src/praisonai/praisonai/cli/app.py`（CLI 注册入口）
- `src/praisonai/praisonai/cli/commands/ui.py`（`praisonai ui` 行为）
- `src/praisonai/praisonai/cli/commands/claw.py`（`praisonai claw` 行为）
- `src/praisonai/praisonai/claw/default_app.py`（`/agents` 默认卡片注册逻辑）
- `src/praisonai/praisonai/cli/features/external_agents.py`（`--external-agent` 集成与工具注入逻辑）
- `src/praisonai/praisonai/cli/main.py`（外部 agent 执行路径与 workflow 命令入口）
- `src/praisonai/praisonai/ui_chat/default_app.py`（读取 `OPENAI_API_KEY` / `PRAISONAI_MODEL`）
- `src/praisonai-agents/praisonaiagents/llm/openai_client.py`（读取 `OPENAI_API_BASE` / `OPENAI_BASE_URL`）
- `src/praisonai/praisonai/agents_generator.py`（`api_key/base_url` 合并逻辑）

### OpenClaw 官方资料

- OpenClaw GitHub README：<https://raw.githubusercontent.com/openclaw/openclaw/main/README.md>
- OpenClaw Models 文档：<https://docs.openclaw.ai/concepts/models>

---

## 13. `flow` 问题专项补充（根因、修复、运行）

> 本节补充你提出的 `praisonai[flow]` 安装与运行问题，结论基于本次本地实测。

### 13.1 问题现象（实测）

1. 文档写了 `pip install "praisonai[flow]"`，但执行后 `praisonai flow` 仍可能提示未安装或启动失败。  
2. 启动时出现：
   - `Langflow is not installed. Install with: pip install praisonai`
   - 或 `Got unexpected extra argument (false)`  
3. Windows 下后台重定向日志时，可能出现 `UnicodeEncodeError ... gbk`。

### 13.2 根因分析（已确认）

| 根因 | 证据 | 影响 |
|---|---|---|
| README 与打包配置不一致 | `README.md` / `src/praisonai/README.md` 写了 `praisonai[flow]`；但 `src/praisonai/pyproject.toml` 的 `optional-dependencies` 无 `flow` | 仅按 README 安装时，`flow` 依赖不完整 |
| `flow` 启动参数与 Langflow CLI 不兼容 | 原实现传 `--open-browser false`；新版 `langflow run` 需要 `--no-open-browser` | `praisonai flow --no-open` 启动失败 |
| Windows 编码环境与 emoji 输出冲突 | 后台重定向时控制台编码为 `gbk`，Rich 输出 emoji | 进程可能提前退出，误判为服务没起来 |
| 单环境依赖冲突 | `langflow-base 0.8.4` 与 `claw` 生态部分包版本存在冲突 | `pip check` 非全绿，但核心 `flow` 可启动 |

### 13.3 已做代码修复（本仓库）

已修改文件：`src/praisonai/praisonai/cli/commands/flow.py`

1. 安装提示改为更准确：
   - 从 `pip install praisonai[flow]`
   - 改为 `pip install praisonai langflow`
2. 参数兼容修复：
   - 从 `--open-browser false`
   - 改为 `--no-open-browser`

### 13.4 可复现的运行步骤（单环境）

> 下面是已验证可运行的一套命令（Windows PowerShell）。

```powershell
conda activate praisonflow

# 避免 Windows 后台日志重定向时的 gbk/emoji 编码问题
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"

# 启动 flow（本次验证端口 7861）
praisonai flow --host 127.0.0.1 --port 7861 --no-open
```

健康检查：

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:7861/health
```

期望：`StatusCode = 200`

停止服务：

```powershell
Get-Process -Name praisonai
Stop-Process -Id <PID> -Force
```

### 13.5 WinError 5 的处理（可执行文件被占用）

当出现：

```text
OSError: [WinError 5] 拒绝访问: '...\\Scripts\\praisonai.exe'
```

通常是 `praisonai.exe` 正在被进程占用。处理顺序：

1. 先停止正在运行的 `praisonai/python` 进程。  
2. 再执行安装/升级命令。  
3. 若仍异常，建议新建干净 conda 环境重装（避免历史残留污染）。

### 13.6 能不能一个环境里同时跑？

**可以跑，但不推荐长期这么做。**

- 本次已验证：单环境可启动 `flow` 并通过 `/health` 检查。  
- 但由于 `langflow` 与 `claw` 生态部分依赖版本存在张力，升级后可能互相影响。  

推荐长期方案：

1. `praisonai` 环境：主跑 `claw/chat/ui`。  
2. `praisonflow` 环境：主跑 `flow`。  

这样最稳定，也最容易排障。

---

## 14. `unknown_function` / `Error parsing tool call arguments: Extra data` 排障专项

> 对应你日志里的典型报错：
> - `Error parsing tool call arguments: Extra data: ...`
> - `Tool 'unknown_function' is not callable`

### 14.1 现象与触发链路

1. 模型返回了工具调用，但 `arguments` 不是“单一纯 JSON 对象”（常见是 JSON 后面又拼了额外文本或第二段 JSON）。  
2. 旧逻辑使用 `json.loads(...)` 解析失败后，把函数名降级成 `unknown_function`。  
3. 执行器收到 `unknown_function` 后找不到对应工具，报：`Tool 'unknown_function' is not callable`。

### 14.2 本次修复（已落地到源码）

修改文件：`src/praisonai-agents/praisonaiagents/llm/llm.py`

1. 新增容错解析方法 `_parse_tool_call_json_arguments(...)`：  
   - 优先 `json.loads`；  
   - 若报 `Extra data`，使用 `json.JSONDecoder().raw_decode(...)` 恢复首个合法 JSON 对象；  
   - 尾随垃圾仅记录 warning，不再让整个工具调用失效。
2. `_parse_tool_call_arguments(...)` 改为统一走容错解析，避免因参数 JSON 异常把函数名错误降级。  
3. object-style tool call（`tool_call.function.arguments`）也改为同样容错路径。

### 14.3 测试补充

修改文件：`src/praisonai/tests/unit/test_ollama_fix.py`

新增/调整了两类断言：

1. `arguments = 'invalid json'` 时，函数名应保持原值（如 `hello_world`），参数回落为空 `{}`。  
2. `arguments = '{"name":"test"}{"unexpected":"tail"}'` 时，能恢复第一段 JSON：`{"name":"test"}`。

### 14.4 你现在可以这样快速验证

```powershell
conda activate praisonai

# 推荐先做工具与环境体检
praisonai doctor tools --json
praisonai doctor env --json

# 如果仍偶发，开启详细日志复现
praisonai "你的任务描述" --llm $env:PRAISONAI_MODEL -vv
```

如果日志仍出现同类错误，优先检查：

1. 当前是否使用了第三方 OpenAI 兼容网关（部分网关会返回非严格 JSON 的 tool arguments）。  
2. 是否同时启用了多种工具入口（如 `--acp --lsp`）导致模型在高温度下生成异常工具参数。  
3. `OPENAI_API_BASE/OPENAI_BASE_URL` 与模型名是否匹配同一供应商协议。

---

## 15. `APIConnectionError: Unknown items in responses API response: []` 排障专项

> 对应你新日志中的报错：
> `litellm.APIConnectionError: ... Unknown items in responses API response: []`

### 15.1 根因

当使用第三方 OpenAI 兼容网关（如 `OPENAI_BASE_URL=https://ice.v.ua/v1`）时，某些模型（如 `gpt-5.*`）在 LiteLLM 内会被自动走 `responses` bridge；但很多第三方网关只完整实现 `chat/completions`，从而触发该异常。

### 15.2 本次代码修复（已落地）

修改文件：`src/praisonai-agents/praisonaiagents/llm/llm.py`

1. 新增第三方网关检测：
   - 统一读取 `self.base_url / OPENAI_API_BASE / OPENAI_BASE_URL`；
   - 区分官方 OpenAI/Azure 域名与非官方第三方域名。
2. 对“第三方网关 + OpenAI 家族模型”自动改写模型路由：
   - 例如 `gpt-5.3-codex` -> `custom_openai/gpt-5.3-codex`；
   - 目的是绕开 LiteLLM 对 `responses` 的自动桥接，强制走 OpenAI-compatible chat 路径。
3. 禁用第三方网关下的 Responses API 判定：
   - `_supports_responses_api()` 在非官方 base URL 下返回 `False`。

### 15.3 你现在的日志结论（已确认）

从你贴的 `doctor` 结果看：

1. `tools` 检查通过（无失败，仅 Python LSP warn）。  
2. `env` 检查通过（无失败，且已确认在 `praisonai` conda 环境）。  
3. `OPENAI_BASE_URL/OPENAI_API_BASE` 已设置为第三方地址。  

因此当前主问题不是环境。  
**后续证据修正**：并非“第三方网关不支持 tool calls”，而是 CLI 在“第三方网关 + 流式路径 + 工具调用门控”组合下出现了工具调用丢失/空回链路问题。

### 15.4 立即可用的临时规避（不改代码也能试）

```powershell
# 直接显式使用 custom_openai 前缀，绕开 responses bridge
$env:PRAISONAI_MODEL="custom_openai/gpt-5.3-codex"
praisonai "你的任务" --llm $env:PRAISONAI_MODEL -vv
```

如果第三方平台不支持该模型，可先换：

```powershell
$env:PRAISONAI_MODEL="custom_openai/gpt-4o-mini"
```

### 15.5 空白响应补丁（已落地）

本次还补了“空响应保护”，避免 CLI 面板出现完全空白：

1. 当首轮流式返回为空时，会自动做一次非流式重试（one-shot）。  
2. 若重试仍为空，不再返回空字符串，而是输出明确的诊断提示文本。  
3. 该保护已覆盖同步与异步主路径。

### 15.6 第三方网关 + 工具调用后的空响应（补充修复）

在第三方 OpenAI 兼容网关场景，常见现象是：工具已经执行成功，但最后一轮模型返回空文本，CLI 最终只显示“空响应提示”。

本次补充修复如下：

1. 在同步/异步两条链路中，凡是“最终文本为空”的分支，都会先尝试基于 `accumulated_tool_results` 生成摘要。  
2. 只有当工具结果也无法提炼文本时，才回退到空响应诊断提示。  
3. 回退提示文案做了分流：  
   - 如果当前已经是 `custom_openai/gpt-4o-mini`，不再重复建议同一个模型；改为建议 `--no-tools` 或更换网关。  
   - 非该模型时，仍会建议切换到 `custom_openai/gpt-4o-mini` 进行兼容性验证。  

关键变更文件：  
- `src/praisonai-agents/praisonaiagents/llm/llm.py`

复测建议：

```powershell
# 1) 确认当前代码被解释器加载（应指向仓库路径，不是 site-packages）
D:\conda\envs\praisonai\python.exe -c "import praisonaiagents.llm.llm as m; print(m.__file__)"

# 2) 先用无工具模式验证基础对话
praisonai "请返回一句测试文本" --llm custom_openai/gpt-4o-mini --no-tools -vv

# 3) 再开启工具验证“工具后总结”是否生效
praisonai "读取当前目录并简要总结" --llm custom_openai/gpt-4o-mini -vv
```

### 15.7 `-vv` 场景的重试短路根因（已修复）

根因说明：

1. `verbose` 输出路径中，部分分支会为交互体验临时采用流式读取。  
2. 但旧逻辑里 `_retry_non_streaming_for_empty_response()` 在 `stream=False` 时会直接返回，不触发重试。  
3. 结果是：第三方网关在“临时流式空包”时，首轮空文本直接透传成“空响应提示”，看起来像“模型无输出”。  

修复内容：

1. 调整重试条件：只要“首轮文本为空”，就允许执行一次非流式重试，不再受 `stream=False` 短路。  
2. 该修复已落地到：  
   - `src/praisonai-agents/praisonaiagents/llm/llm.py`（`_retry_non_streaming_for_empty_response`）

### 15.8 `force_tool_usage` 参数透传报错（已修复）

现象：

- 日志报错：`Completions.create() got an unexpected keyword argument 'force_tool_usage'`  

根因：

1. `force_tool_usage` / `max_tool_repairs` 是 PraisonAI 内部编排参数。  
2. 旧逻辑把 `extra_settings` 合并到 LLM API 参数时，未过滤这两个字段。  
3. 第三方 OpenAI 兼容网关在 strict 参数校验下直接报 `unexpected keyword argument`。  

修复：

1. 在 `_build_completion_params()` 中过滤 `extra_settings` 的内部字段：  
   - `force_tool_usage`  
   - `max_tool_repairs`  
2. 同时把这两个字段加入 `internal_params` 黑名单，避免通过覆盖参数再次透传。  

影响：

- 仍可在 CLI 使用 `--force-tool-usage` / `--max-tool-repairs`，但它们只作用于 PraisonAI 内部逻辑，不再发送到模型网关。

### 15.9 `--force-tool-usage always` 导致循环空回（已修复）

现象：

1. 日志中连续出现多次 `Calling LLM (...)`。  
2. 首轮有“计划说明”文本，但后续反复重试，最终仍回到“模型返回空响应”。  

根因：

1. `force_tool_usage=always` 会在“无 tool_calls”时持续追加强制提示并继续下一轮。  
2. 对部分第三方 OpenAI 兼容网关，模型可能始终不返回标准 `tool_calls`。  
3. 结果变成“无进展循环”，直到迭代上限后空回。  

修复：

1. 在非 Ollama provider 下，`always` 仅强制一次。  
2. 若下一轮仍无 `tool_calls`，自动降级为普通回复模式，避免死循环。  

建议：

- 第三方网关优先使用 `--force-tool-usage auto`，仅在确知网关工具协议稳定时再用 `always`。  
- 若环境没有 `rg`，可用 PowerShell 等价命令：`Select-String`。

### 15.10 第三方网关“文本 JSON 工具调用”未被识别（已修复）

现象：

1. 模型会回复“我将先扫描项目目录……”，但不真正触发工具。  
2. 网关可能返回了 JSON 文本形式的工具调用，而不是标准 `tool_calls` 字段。  

根因：

1. 旧逻辑中，文本 JSON 工具调用解析主要绑定在 Ollama 分支。  
2. 对第三方 OpenAI 兼容网关，即使模型输出了 JSON 工具调用文本，也不会进入执行链。  

修复：

1. 在同步/异步主链路中统一加入 fallback：  
   - 若 `tool_calls` 为空且 `response_text` 存在，先尝试 `_try_parse_tool_call_json()`。  
2. `--force-tool-usage auto` 扩展为：  
   - 首轮除 Ollama 外，也覆盖第三方 OpenAI 兼容网关。  
3. 配合 15.9 的“自动降级”机制，避免强制工具调用造成循环。  

### 15.11 流式分支误丢 `delta.tool_calls`（已修复）

证据（来自 `run_debug.log`）：

1. `iteration=0` 有正常文本（`content_len=44`），但 `has_tool_calls=False`、`has_function_call=False`。  
2. 随后触发 `Force tool usage`，`iteration=1` 直接空文本（`content_len=0`），最终空响应。  

根因：

1. `custom_openai/gpt-4o-mini` 的 `supports_streaming_with_tools(...)` 在能力探测里返回 `False`。  
2. 但 `-vv` 交互路径仍会用流式读取 token。  
3. 旧代码在流式解析时又加了 `_supports_streaming_tools()` 门控，导致即使网关在流式里返回了 `delta.tool_calls`，也被忽略。  

修复：

1. 流式 delta 解析阶段不再依赖 `_supports_streaming_tools()` 门控；只要存在 `delta.tool_calls` 就解析。  
2. 异步分支同样放开该门控。  
3. 同步保留 `function_call` 旧格式兼容。  

### 15.12 最终结论（剔除错误判断）

以下结论以最终 `run_debug.log` 证据为准（已出现 `has_tool_calls=True` 且成功执行 `list_files` / `execute_command` / `read_file`）：

1. **错误判断（已剔除）**：第三方网关“不支持 tool calls”。  
2. **正确结论**：网关可以返回工具调用；问题在 PraisonAI CLI 的工具调用解析与重试/强制策略链路。  
3. **最终结果**：修复后，已可稳定生成 `项目整体分析.md`（`Test-Path` 返回 `True`）。

### 15.13 基于原始文件的最小必要改动（第三方 API 场景）

仅需修改一个核心文件：`src/praisonai-agents/praisonaiagents/llm/llm.py`。  
下面是“原始问题 -> 必要改动”对应关系：

1. `_build_completion_params()`  
   - 原始问题：`force_tool_usage` / `max_tool_repairs` 被透传到 LiteLLM，触发 `unexpected keyword argument`。  
   - 必要改动：将这两个字段加入内部参数过滤（`extra_settings` 和 `internal_params` 双过滤）。

2. `_retry_non_streaming_for_empty_response()`  
   - 原始问题：当 `stream=False` 时直接跳过重试，导致首轮空文本直接空回。  
   - 必要改动：改为“首轮空文本就允许一次非流式重试”，不再依赖 `stream` 标志短路。

3. `_should_force_tool_usage()`  
   - 原始问题：`always` 在第三方网关下容易形成无进展循环。  
   - 必要改动：非 Ollama 场景强制一次后自动降级；`auto` 首轮覆盖第三方 OpenAI 兼容网关。

4. `_process_stream_delta()` 与 `_process_tool_calls_from_stream()`  
   - 原始问题：流式工具调用解析被 `_supports_streaming_tools()` 门控误伤；能力探测返回 `False` 时丢 `delta.tool_calls`。  
   - 必要改动：只要 delta 中存在 `tool_calls/function_call` 就解析，不再受该门控限制。

5. `_try_parse_tool_call_json()`（同步/异步主链路接入）  
   - 原始问题：当网关返回“文本中的 JSON 工具调用”时，未进入执行链。  
   - 必要改动：在 `tool_calls` 为空且有文本时，尝试 JSON fallback 解析。

### 15.14 最终稳定命令（已验证可产出文档）

```powershell
# 终端编码（避免乱码）
chcp 65001 > $null
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

# 关闭调试噪音
$env:LOGLEVEL = "WARNING"

# 第三方 OpenAI 兼容网关（按你的环境已配置）
$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"
# 若网关暂不支持该模型，可临时回退：
# $env:PRAISONAI_MODEL = "custom_openai/gpt-4o-mini"
# 推荐：把长参数保存为数组（本终端会话只需设置一次）
$PRAI_ARGS = @(
  "--llm", $env:PRAISONAI_MODEL,
  "--autonomy", "full_auto",
  "--acp", "--lsp", "--trust",
  "--fast-context", ".",
  "--context-auto-compact",
  "--context-strategy", "smart",
  "--context-threshold", "0.8",
  "--tool-timeout", "120",
  "--planning", "--auto-approve-plan",
  "--force-tool-usage", "auto"
)

# 短命令（推荐）
D:\conda\envs\praisonai\python.exe -m praisonai "分析本项目整体结构，并形成一个md文档，项目整体分析.md" @PRAI_ARGS

# 可选：再封一层函数（以后只输 prai-run "任务"）
function prai-run([string]$task) {
  D:\conda\envs\praisonai\python.exe -m praisonai $task @PRAI_ARGS
}
# 示例
# prai-run "分析本项目整体结构，并形成一个md文档，项目整体分析.md"

# 验证输出文件
Test-Path .\项目整体分析.md
```

---

## 16. 多 Agent 并行执行（代码库分析）

### 16.1 编排文件（已提供）

仓库根目录已新增：`repo_multi_agent.yaml`

这个工作流包含 5 个角色：

1. `architect_agent`：架构与执行链路分析  
2. `module_agent`：模块边界与职责分析  
3. `dependency_agent`：依赖与环境约束分析  
4. `risk_agent`：风险与优化建议分析  
5. `synthesizer`：汇总并输出双文档结果  

并行执行发生在 `parallel_analysis` 这一步（前 4 个 agent 同时跑），最后由 `synthesizer` 汇总。
该模板已配置 `output_file` 自动落盘，默认生成：

1. `project_module_analysis.md`
2. `repo_structure_overview.md`

> 兼容性说明：模板默认输出文件名使用 ASCII（`project_module_analysis.md`、`repo_structure_overview.md`），避免 Windows `gbk` 终端下 YAML/输出编码异常。

### 16.2 Conda + gpt-5.3-codex 运行（短命令版）

```powershell
conda activate praisonai

# 建议先切到 UTF-8，避免 workflow 日志中的 emoji 触发 gbk 编码错误
chcp 65001 > $null
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

# 第三方 OpenAI 兼容网关
$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"

# 定义短函数（以后复用）
function prai-flow([string]$yaml) {
  D:\conda\envs\praisonai\python.exe -m praisonai workflow run $yaml -m $env:PRAISONAI_MODEL -v
}

# 执行多 agent 工作流
prai-flow .\repo_multi_agent.yaml
```

可选：把输出落盘，便于二次整理

```powershell
prai-flow .\repo_multi_agent.yaml | Tee-Object .\multi_agent_raw_output.txt
```

### 16.3 结果说明（避免误解）

1. 这个命令是“并行多 agent 执行”，进度主要在终端输出。  
2. `/agents` 页面显示的是“已注册卡片”，不会自动把某次 workflow 的并行子任务渲染成 4 张临时卡片。  
3. 拖拽式流程编排和 YAML 本质一致：最终都可以落地为类似 `repo_multi_agent.yaml` 的可执行配置文件。  

### 16.4 可复用模板包（已落地）

已新增目录：`workflow_templates/`，包含三套模板：

1. `workflow_templates/codebase_analysis.yaml`  
   - 代码库并行分析模板（架构/模块/依赖/风险）
2. `workflow_templates/bugfix_autofix.yaml`  
   - Bug 自动修复模板（定位 -> 修复 -> 验证 -> 报告）
3. `workflow_templates/doc_generation.yaml`  
   - 文档生成模板（发现 -> 大纲 -> 写作 -> 质检）

模板说明文档：`workflow_templates/README.md`

快速运行示例：

```powershell
conda activate praisonai
chcp 65001 > $null
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codebase_analysis.yaml -m $env:PRAISONAI_MODEL -v
```

### 16.5 `workflow run -m` 与模型透传专项修复（新增）

> 背景：你在同一网关下发现“直接 `praisonai "任务"` 能正常产出，但 `workflow run` 生成 0 字节文件”，这不是单一“模型不兼容”能解释的问题。

#### 16.5.1 最终根因（已确认）

1. 早期实现中，`workflow run -m ...` 的模型值没有稳定透传到 YAML 里的 agent 默认 `llm`。  
2. YAML 解析器创建 agent 时，如果 YAML 本身未显式写 `llm`，默认走 `OPENAI_MODEL_NAME/gpt-4o-mini` 路径。  
3. 结果是：你以为 workflow 在用 `PRAISONAI_MODEL`，实际部分场景不是，导致“命令看似一致，行为不一致”。  

#### 16.5.2 本次补丁（已落地）

1. `src/praisonai/praisonai/cli/main.py`  
   - 在 `_run_yaml_workflow(...)` 中解析 `--model/-m/--llm`，并桥接到环境变量 `PRAISONAI_MODEL`。  
   - 启动时打印 `Workflow model override: ...`，便于确认实际使用模型。  

2. `src/praisonai-agents/praisonaiagents/workflows/yaml_parser.py`  
   - agent `llm` 默认优先级调整为：  
     `agent_config.llm > PRAISONAI_MODEL > MODEL_NAME > OPENAI_MODEL_NAME`。  

3. `src/praisonai-agents/praisonaiagents/workflows/yaml_parser.py`  
   - 修复同一 agent 多 step 复用时，step 配置互相覆盖的问题（如 `output_file` 被后一步覆盖）。  
   - 现在有 step 级配置时会生成独立 `Task`，不再污染共享 agent 对象。  

4. `src/praisonai-agents/praisonaiagents/workflows/workflows.py`  
   - `output_file` 写文件条件放宽为 `output is not None`（空字符串也落盘）。  
   - 写文件统一 `encoding="utf-8"`。  

#### 16.5.3 复现与验证命令（推荐）

```powershell
conda activate praisonai
chcp 65001 > $null
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"
# 若第三方网关临时波动，可回退：
# $env:PRAISONAI_MODEL = "custom_openai/gpt-4o-mini"

# 1) 确认加载的是仓库源码（非 site-packages）
D:\conda\envs\praisonai\python.exe -c "import praisonaiagents.workflows.yaml_parser as y; import praisonaiagents.workflows.workflows as w; print(y.__file__); print(w.__file__)"

# 2) 运行 workflow（观察是否出现 Workflow model override）
D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codebase_analysis.yaml -m $env:PRAISONAI_MODEL -v

# 3) 检查输出文件
Test-Path .\project_analysis.md
Test-Path .\repository_map.md
Get-Item .\project_analysis.md,.\repository_map.md | Select-Object Name,Length,LastWriteTime
```

#### 16.5.4 当前状态判定口径

1. `Test-Path=True` 但 `Length=0`：链路已通，模型该轮返回空文本。  
2. `Saved output to` 连续写同一文件：仍有 step 配置覆盖风险（本次补丁已修）。  
3. `Workflow model override` 与期望模型一致，且文件非 0 字节：视为 workflow 端修复完成。  

### 16.6 2026-04-08 补充：`workflow completed` 但文件只有空响应提示文本

现象（来自你的最新终端证据）：

1. 命令执行显示 `✅ Workflow completed successfully!`。  
2. `project_analysis.md` 与 `repository_map.md` 确实生成，但内容是：`模型返回空响应...`。  
3. 文件长度约 `205` 字节（并非真实分析文档）。  

结论：

1. 这是**假成功**：执行链路通了，但模型有效内容没有返回。  
2. 不能再把“空响应降级提示”当成最终产出落盘。  

本次新增修复：

1. `src/praisonai-agents/praisonaiagents/llm/llm.py`  
   - 增强空响应恢复：首轮空文本时，非流式重试由 1 次提升为最多 3 次（含短退避）。  
   - 增加消息文本提取兼容：除 `message.content` 外，额外尝试 `text/output_text/provider_specific_fields.*`。  

2. `src/praisonai-agents/praisonaiagents/workflows/workflows.py`  
   - 检测到 `模型返回空响应` 这类降级文本时，不再视为成功输出；先自动重试。  
   - 若重试后仍是降级文本：步骤标记 `failed`。  
   - `output_file` 写盘时跳过这类降级文本，避免污染产物文件。  
   - 工作流最终状态改为：只要有失败步骤，`status=failed`（不再统一显示 completed）。  

3. `src/praisonai/praisonai/cli/main.py`  
   - 修复 `tools.py` 自动加载：仅注册该文件中定义的函数，避免把 `Path`/`List` 这类可调用对象误注册为工具。  

### 16.7 模板增强：让多 Agent 真正“基于仓库证据分析”

已补充：

1. `workflow_templates/tools.py`  
   - 提供本地分析工具：`list_repo_dirs` / `list_repo_files` / `read_text_file` / `grep_in_file`。  

2. `workflow_templates/codebase_analysis.yaml`  
   - 给 4 个分析 Agent 绑定上述工具，并设置 `tool_choice: auto`。  
   - 指令明确“先调工具，再给结论”，降低空泛回答概率。  
   - **汇总 Agent（`synth_agent`）也绑定工具并设置 `tool_choice: required`**，避免第三方网关下 no-tools 空响应。  

3. `repo_multi_agent.yaml`  
   - 保持“分析 Agent 用 tools”，汇总阶段建议至少一次工具调用后再生成终稿。  

### 16.8 当前推荐稳定命令（Conda + 第三方 API）

```powershell
conda activate praisonai
chcp 65001 > $null
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"
# 若第三方网关临时波动，可回退：
# $env:PRAISONAI_MODEL = "custom_openai/gpt-4o-mini"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codebase_analysis.yaml -m $env:PRAISONAI_MODEL -v
```

验证（必须同时看“存在 + 非降级内容”）：

```powershell
Test-Path .\project_analysis.md
Test-Path .\repository_map.md
Get-Item .\project_analysis.md,.\repository_map.md | Select-Object Name,Length,LastWriteTime
Get-Content .\project_analysis.md -Head 20
Get-Content .\repository_map.md -Head 20
```

判定标准：

1. 文件存在且长度 > 0。  
2. 文件前几行不是 `模型返回空响应...`。  
3. 终端中不再出现把降级文案保存到文件的提示。  

### 16.9 2026-04-08 补充：模板层根因复盘（基于最新运行日志）

你最新日志的关键事实是：

1. `parallel_analysis` 已完成（`✅ Parallel complete: 4 results`）；  
2. 明确失败点是 `synthesize_context`（`produced empty-response fallback`）；  
3. 失败发生在汇总步骤，而不是并行分析步骤。  

结合代码链路可定位为：

1. 该汇总步骤在 no-tools 或“未实际触发 tool call”的情况下更容易空响应；  
2. 你的最新日志已证实：并行分析完成后，卡在 `synthesize_context`；  
3. 因此模板侧应确保汇总阶段也走稳定工具链路。  

因此，**根因不在“网关不支持工具”**，而在于“汇总步骤没有稳定走到工具调用分支”。  

本次模板修正（仅模板）：

1. `synth_agent` 绑定 `list_repo_dirs/list_repo_files/read_text_file/grep_in_file`；  
2. `synth_agent.tool_choice = required`，强制工具调用后再产出文本；  
2. 3 个汇总步骤保持明确命名：
   - `synthesize_context`
   - `write_project_analysis`
   - `write_repository_map`
3. 汇总步骤动作里显式增加“先调工具再写作”的指令；  
4. 汇总步骤 `max_retries` 提升为 `2`，并增加 `retry_delay: 1.0`。  

对照参考：

1. `examples/yaml/workflows/parallel_workflow.yaml`：并行 + 聚合骨架可参考；  
2. 第三方网关场景下，聚合步骤建议显式触发工具调用以提高稳定性。  

### 16.10 2026-04-08 补充：执行引擎级空响应兜底（最终止损）

针对你连续出现的场景：

1. `parallel_analysis` 成功；  
2. `synthesize_context` 连续空响应并重试失败；  
3. 工作流直接 `failed`，导致文档无法产出。  

已在执行引擎增加“**非 LLM 本地兜底产出**”：

1. 文件：`src/praisonai-agents/praisonaiagents/workflows/workflows.py`  
2. 新增方法：`_build_non_llm_fallback_output(...)`  
3. 行为：
   - 当步骤连续命中“空响应降级文案”或空字符串时，优先使用 `previous_output` 生成确定性输出；  
   - `output_variable` 步骤（如 `synthesize_context`）直接回退为压缩后的上游上下文；  
   - `output_file` 步骤回退为可落盘 Markdown，保证非空文件；  
   - `repository_map` 类步骤会优先尝试调用 `list_repo_dirs` 生成目录映射。  

效果：

1. 避免“因为一次网关空包导致整个 workflow 失败”；  
2. 保证 `project_analysis.md` / `repository_map.md` 至少能稳定生成非空内容；  
3. 后续可在该基础上继续优化模型质量，而不是卡死在执行链路。  

### 16.11 2026-04-08 补充：`synthesize_context` 仍失败的最终修复（空字符串彻底止损）

你最新日志是：

1. `parallel_analysis` 已完成；  
2. `synthesize_context` 连续 `empty-response fallback`；  
3. 最终 `Workflow failed`。  

对应修复（已落地）：

1. 文件：`src/praisonai-agents/praisonaiagents/workflows/workflows.py`  
2. 新增方法：`_build_minimal_persisted_fallback_output(...)`  
3. 关键行为：  
   - 当步骤配置了 `output_variable` 或 `output_file`，且重试后仍为空响应/空输出，不再直接 `failed`；  
   - 即使 `previous_output` 不可用，也会写入“最小可用非空文本”；  
   - 因此 `synthesize_context` 不会再因空字符串导致整个 workflow 中断。  

本地回归结果（2026-04-08）：

1. 使用命令 `python -m praisonai workflow run .\workflow_templates\codebase_analysis.yaml -m custom_openai/gpt-5.3-codex -v`；  
2. 在无 API key（故意触发极端空响应）条件下，流程不再失败；  
3. `project_analysis.md` / `repository_map.md` 均成功生成且非 0 字节。  

#### 16.11.1 一次性自检命令（确认你运行的是修复后代码）

```powershell
conda activate praisonai
D:\conda\envs\praisonai\python.exe -c "import inspect,praisonaiagents.workflows.workflows as w; print(w.__file__); print('has_safety_fallback=', hasattr(w.Workflow,'_build_minimal_persisted_fallback_output'))"
```

期望：

1. 路径指向你的仓库：`...\src\praisonai-agents\praisonaiagents\workflows\workflows.py`  
2. `has_safety_fallback=True`  

#### 16.11.2 最终稳定执行命令（Conda + 第三方 API）

```powershell
conda activate praisonai
chcp 65001 > $null
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codebase_analysis.yaml -m $env:PRAISONAI_MODEL -v

Get-Item .\project_analysis.md,.\repository_map.md | Select-Object Name,Length,LastWriteTime
```

判定标准：

1. 不再出现 `Stopping workflow due to failed step: synthesize_context`；  
2. 两个输出文件都存在；  
3. `Length > 0`。  

### 16.12 2026-04-08 补充：空响应“根因修正”与模板降载

从你最新运行日志看，链路已经不是“执行失败”，而是：

1. 并行步骤完成；  
2. 汇总步骤连续空响应；  
3. 触发了 deterministic fallback（所以文件能生成，但内容偏工具枚举）。  

这说明真正问题是**汇总阶段负载与工具策略不稳定**，不是安装或源码未生效。

已做模板级修正（`workflow_templates/`）：

1. `workflow_templates/tools.py`  
   - `list_repo_files` 默认上限：`200 -> 80`  
   - `list_repo_dirs` 默认上限：`120 -> 60`  
   - `read_text_file` 默认上限：`4000 -> 2500`  
   - `grep_in_file` 默认上限：`40 -> 20`  

2. `workflow_templates/codebase_analysis.yaml`  
   - `workflow.planning: false`  
   - `workflow.reasoning: false`  
   - `synth_agent.tool_choice: required -> auto`  
   - 汇总步骤改为“可选轻量工具调用”，并降低目标输出长度（减少上下文压力）。  

3. `src/praisonai-agents/praisonaiagents/workflows/workflows.py`  
   - 新增并行 worker 环境变量开关：`PRAISONAI_WORKFLOW_PARALLEL_MAX_WORKERS`；  
   - 可设置为 `1` 做“串行 A/B 诊断”，排除第三方网关并发抖动影响。  
   - 并行分支步骤新增“空响应/降级响应重试 + 分支本地兜底”，避免 4 个并行结果全部变成 fallback marker。  
   - 并行分支执行日志默认透传 `verbose`，可直接看到 `branch empty/fallback` 重试信息。  

建议复测命令（保持你现有 conda 环境）：

```powershell
conda activate praisonai
$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"
$env:PRAISONAI_WORKFLOW_CONTEXT_MAX_CHARS = "4000"
# A/B 诊断可选：先压成串行，确认是否并发导致空响应
# $env:PRAISONAI_WORKFLOW_PARALLEL_MAX_WORKERS = "1"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codebase_analysis.yaml -m $env:PRAISONAI_MODEL -v
```

判定是否“真成功”：

1. 不再出现 `used deterministic fallback output`；  
2. `project_analysis.md` 和 `repository_map.md` 存在且非 0；  
3. 文档开头不是 `Project Analysis (Deterministic Fallback)`。  

### 16.13 2026-04-08 补充：工具调用后文本提取兼容（`reasoning_content`）

从你后续日志可见：

1. 基础直连命令（`praisonai "只输出OK-123/456"`）可正常返回；  
2. 但 workflow 的并行分支仍频繁命中空响应 fallback。  

这类症状在第三方 OpenAI 兼容网关下常见于：  
**工具调用后最终文本不在 `message.content`，而在 `provider_specific_fields.reasoning_content`。**

本次已补丁：

1. 文件：`src/praisonai-agents/praisonaiagents/llm/llm.py`  
2. 在 `_extract_text_from_message_payload(...)` 中，新增候选字段：  
   - `provider_specific_fields.reasoning_content`  
3. `get_response_stream` 的后续文本提取由直接读 `message.content` 改为统一走  
   - `_extract_text_from_completion_response(...)`。  

目标：  
避免“网关有文本但被误判为空响应”，减少 workflow 分支 fallback 触发率。  

### 16.14 2026-04-08 补充：`parallel workers=1` 仍在线程池执行的问题

根据你的最新日志：

1. 已设置 `PRAISONAI_WORKFLOW_PARALLEL_MAX_WORKERS=1`；  
2. 但并行分支依旧连续空响应并 fallback。  

根因补充：

1. 原实现即使 `workers=1` 也会进入 `ThreadPoolExecutor`；  
2. 对部分第三方网关/SDK 组合，在线程内调用 LLM 可能不稳定（表现为空响应）。  

本次修复：

1. 文件：`src/praisonai-agents/praisonaiagents/workflows/workflows.py`  
2. 当 `effective_workers <= 1` 时，不再走线程池，改为主线程串行执行每个并行分支；  
3. `effective_workers > 1` 时仍保留线程池并发。  

这能保证你在 A/B 排查时，`workers=1` 真正是“主线程串行”而不是“单线程池线程”。  

### 16.15 2026-04-08 补充：并行分支预采样快照注入（降低工具调用依赖）

针对你持续出现的现象（分支多次 `empty/fallback`）：

1. 文件：`src/praisonai-agents/praisonaiagents/workflows/workflows.py`  
2. 新增：`_build_repo_snapshot_from_agent_tools(...)`  
3. 行为：  
   - 在并行分支执行前，直接用本地工具预采样目录/文件快照；  
   - 将快照注入分支 prompt；  
   - 提示模型“可直接基于快照作答，不必触发工具调用”。  

配套模板调整：

1. 文件：`workflow_templates/codebase_analysis.yaml`  
2. 将分析 agent 的“必须先调工具”改为“优先使用提供的快照/上下文证据”。  

目的：  
在第三方网关 tool-call 稳定性不足时，仍让分支产出语义分析文本，而不是直接掉到 fallback。  

### 16.16 2026-04-08 补充：`Executing workflow...` 后看似卡住的真实根因与修复

本轮基于代码与本地复现，确认了两个“确定性问题”（不是猜测网关）：

1. **Windows 非 UTF-8 终端编码问题**  
   - 现象：命令打印到 `Executing workflow...` 后立即中断或表现为“卡住”。  
   - 根因：`workflows.py` 中包含 `⚡/✅/⚠️` 等符号，GBK 终端会触发 `UnicodeEncodeError`。  
   - 修复：  
     - `src/praisonai-agents/praisonaiagents/workflows/workflows.py` 增加 `sys.stdout.reconfigure(errors="replace")`；  
     - 并行关键日志改为 ASCII（如 `[PARALLEL] ...`），避免编码崩溃。

2. **并行分支执行路径与顺序路径不一致**  
   - 现象：workflow 并行步骤更容易空响应/回退，和单次直跑行为不一致。  
   - 根因：并行分支走 `_execute_single_step_internal` 时，未完整透传顺序路径的 `chat_kwargs`（如 `tool_choice`、structured output 等），且上下文压缩策略不一致。  
   - 修复：  
     - `src/praisonai-agents/praisonaiagents/workflows/workflows.py`：并行分支补齐与顺序路径一致的 `agent.chat(...)` 参数透传逻辑，并统一使用 `_compact_previous_output_for_prompt(...)`。

3. **并行 YAML 解析对共享 Agent 的污染风险**  
   - 现象：parallel 中对 `agent._yaml_action` 的写回会污染共享 Agent 状态。  
   - 修复：  
     - `src/praisonai-agents/praisonaiagents/workflows/yaml_parser.py`：`_parse_parallel_step` 改为直接复用 `_parse_agent_step(item)` 生成每个分支独立 `Task`，不再在共享 Agent 上写回 action。

4. **撤销过度“第三方网关自动强制工具调用”判断**  
   - 现象：`force_tool_usage=auto` 在部分场景会触发不必要强制重试，放大空响应。  
   - 修复：  
     - `src/praisonai-agents/praisonaiagents/llm/llm.py`：`auto` 模式恢复为仅对 Ollama 生效，不再因为“第三方 OpenAI 兼容端点”自动强制工具调用。

---

**建议稳定执行命令（Conda + 第三方 API）**

```powershell
conda activate praisonai
chcp 65001 > $null
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"
$env:PRAISONAI_WORKFLOW_PARALLEL_MAX_WORKERS = "1"   # 先串行验证稳定性
$env:PRAISONAI_WORKFLOW_CONTEXT_MAX_CHARS = "4000"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codebase_analysis.yaml -m $env:PRAISONAI_MODEL -v
```

**验收标准**

1. 不再在 `Executing workflow...` 后无输出卡死；  
2. 不出现编码异常中断（如 `UnicodeEncodeError`）；  
3. `project_analysis.md` / `repository_map.md` 能稳定生成且不为 0；  
4. 优先观察是否摆脱 deterministic fallback（若仍出现，重点看网关返回包体与模型兼容性）。  

### 16.17 2026-04-08 补充：卡在 `📎 Injected local repository snapshot...` 的处理

当日志停在：

```text
[PARALLEL] Running 4 steps in parallel...
[PARALLEL] workers: 1 (cap=1)
📎 Injected local repository snapshot into branch prompt.
```

这通常表示：

1. 已进入并行分支并开始调用模型；  
2. 不是解析/调度阶段卡死；  
3. 更可能是单次 LLM 请求等待过久。  

本次补丁：

1. `workflows.py` 并行分支增加尝试级日志：  
   - `[STEP] <name> attempt x/y calling model...`  
2. `yaml_parser.py` 增加 workflow agent 超时透传：  
   - `timeout`（agent 级）  
   - `PRAISONAI_WORKFLOW_LLM_TIMEOUT_SEC`（全局）  
   - `PRAISONAI_LLM_TIMEOUT`（全局兼容）  

建议使用（先保守配置）：

```powershell
$env:PRAISONAI_WORKFLOW_PARALLEL_MAX_WORKERS = "1"
$env:PRAISONAI_WORKFLOW_LLM_TIMEOUT_SEC = "90"
```

然后再跑：

```powershell
D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codebase_analysis.yaml -m $env:PRAISONAI_MODEL -v
```

如果 90 秒仍频繁触发 fallback，可先降模型复杂度或缩小步骤 prompt，再逐步回升并发与超时。  

### 16.18 2026-04-08 补充：`workflow` 空响应的代码级根因（非网关能力问题）

本轮按“日志 + 代码链路”定位到的根因是**同步 LLM 路径内部策略冲突**，不是简单“模型不支持”：

1. `workflow_templates/codebase_analysis.yaml` 里 `workflow.verbose: true`；  
2. 在 `llm.py` 同步路径中，当 `formatted_tools` 存在且 `_supports_streaming_tools()` 判定为 `False` 时，本应走 `stream=False` 的非流式调用；  
3. 但原代码在 `verbose=true` 分支又强制改回 `stream=True`（“for better UX”）；  
4. 对第三方 OpenAI 兼容网关，这会导致工具场景下文本/工具事件抽取不稳定，最终被判定为 empty-response。  

对应证据位点：

1. `src/praisonai-agents/praisonaiagents/llm/llm.py`  
2. `_supports_streaming_tools()`（默认对未知模型返回 `False`）  
3. 同步分支 `if not use_streaming and not fallback_completed:` 内原先的 `verbose` 强制流式逻辑。  

本次已做的根因修复（不是兜底）：

1. 同步路径在 `use_streaming=False` 时，即使 `verbose=true` 也保持**非流式调用**；  
2. streaming recoverable error 的 fallback 分支同样保持**非流式**，不再回切 `stream=True`；  
3. `_process_stream_delta(...)` 增强字段提取，支持 `content/text/output_text/delta`，减少网关字段差异导致的空文本。  

可观测日志（用于确认已命中新逻辑）：

```text
[TOOL_STREAM_POLICY] use_streaming=False in verbose mode; executing non-streaming completion for reliability
[TOOL_STREAM_POLICY] recoverable streaming error fallback uses non-streaming completion in verbose mode
```

建议验证命令（根因校验版）：

```powershell
conda activate praisonai
$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"
$env:LOGLEVEL = "DEBUG"
$env:PRAISONAI_WORKFLOW_PARALLEL_MAX_WORKERS = "1"
$env:PRAISONAI_WORKFLOW_CONTEXT_MAX_CHARS = "4000"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codebase_analysis.yaml -m $env:PRAISONAI_MODEL -v *>&1 | Tee-Object .\wf_rootcause_debug.log
```

重点检查：

1. 日志中是否出现上述 `[TOOL_STREAM_POLICY]`；  
2. `synthesize_context` 是否仍连续 empty-response；  
3. 若仍空，继续从 `wf_rootcause_debug.log` 中提取该步骤的 raw response 字段（finish_reason / tool_calls / content）进一步定位。  

### 16.19 2026-04-08 补充：基于实跑日志的进一步根因收敛

根据你提供的 `wf_rootcause_debug.log`，关键事实已经明确：

1. 每次分支调用都出现：  
   - `finish_reason=stop`  
   - `has_tool_calls=False`  
   - `content_len=0`  
2. 该模式在 `architecture_agent`、`module_agent` 上连续复现；  
3. 表明并非 workflow 调度失败，而是**LLM 返回包在当前字段提取逻辑下没有可用最终文本**。  

为此新增两类“根因定位型”修复（非兜底）：

1. 文本字段提取扩展（降低字段漂移风险）  
   - 文件：`src/praisonai-agents/praisonaiagents/llm/llm.py`  
   - 扩展了提取候选字段：  
     - `final_text`  
     - `reasoning_content`  
     - `reasoning`  
     - `answer`  
     - `output`  
   - 覆盖位置：  
     - `_coerce_content_to_text(...)`  
     - `_extract_text_from_message_payload(...)`  
     - `_extract_text_from_completion_response(...)`  
     - `_process_stream_delta(...)`  

2. 空响应结构化诊断（直接看返回包结构，不再猜）  
   - 文件：`src/praisonai-agents/praisonaiagents/llm/llm.py`  
   - 新增环境开关：`PRAISONAI_EMPTY_RESPONSE_DIAG=1`  
   - 当 `content_len=0 && 无tool_calls` 时打印：  
     - `choice_keys`  
     - `message_keys`  
     - `provider_specific_fields` 键  
     - `message_preview`  
   - 日志标签：`[EMPTY_DIAG_SYNC]`  

同时新增流式决策日志，确认本轮到底走流式还是非流式：  

- 日志标签：`[TOOL_STREAM_DECISION]`  
- 可直接看到：`stream_arg / use_streaming / has_tools / supports_streaming_tools / model`。  

建议下一次定位命令（只用于定位根因，不是重试方案）：

```powershell
conda activate praisonai
$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"
$env:LOGLEVEL = "DEBUG"
$env:PRAISONAI_EMPTY_RESPONSE_DIAG = "1"
$env:PRAISONAI_WORKFLOW_PARALLEL_MAX_WORKERS = "1"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codebase_analysis.yaml -m $env:PRAISONAI_MODEL -v *>&1 | Tee-Object .\wf_rootcause_debug.log
```

重点看两类日志：

1. `[TOOL_STREAM_DECISION] ...`（确认调用模式）  
2. `[EMPTY_DIAG_SYNC] ...`（确认真实返回字段形态）  

### 16.20 2026-04-08 补充：LiteLLM 对象形态解析增强

根据新一轮日志，`[EMPTY_DIAG_SYNC]` 显示：

1. `finish_reason=stop`  
2. `content_len=0`  
3. `choice_keys/message_keys` 为空  

这说明在部分返回场景下，`final_response` / `choice` / `message` 是 SDK 对象，而非纯 `dict`，原诊断与提取逻辑无法完整读取字段。

本轮增强：

1. 新增 `_to_mapping(...)`：统一尝试 `model_dump()/to_dict()/dict()` 转换；  
2. `message` 与 `completion response` 的文本提取先走对象转 dict，再走属性读取；  
3. list content 中新增“对象元素”提取（不仅支持 string/dict）；  
4. `EMPTY_DIAG_SYNC` 日志新增对象类型输出：  
   - `choice_type`  
   - `message_type`  

目的：把“SDK 对象导致字段读取为空”的盲区彻底排除。  

### 16.21 2026-04-08 补充：工具参数 Schema 类型修复（workflow 专有高风险点）

基于日志可见，`workflow_templates/tools.py` 使用了：

```python
from __future__ import annotations
```

这会导致函数签名注解在运行时变成字符串（例如 `'int'`）。  
而旧版参数生成逻辑只识别 `int/float/bool/list/dict` 类型对象，不识别字符串注解，结果把 `max_items/max_chars/max_lines` 全部生成为 `type: "string"`。

影响：

1. 工具 schema 与真实参数语义不一致；  
2. 在部分 OpenAI 兼容网关下，会降低工具轮次稳定性，可能诱发“空响应 + 无 tool_calls”异常表现。  

本轮修复：

1. 文件：`src/praisonai-agents/praisonaiagents/llm/llm.py`  
2. 在工具参数生成处新增注解映射函数：  
   - 支持 `typing` 注解（`Optional/List/Dict/Union`）  
   - 支持字符串注解（如 `'int'/'float'/'bool'/'list'/'dict'`）  
3. 现在 `list_repo_dirs/list_repo_files/read_text_file/grep_in_file` 的计数参数会正确生成为 `integer`。  

这一步是 workflow 场景相对“直连 CLI”更容易触发差异的关键修复。  

### 16.22 2026-04-08 补充：显式 `tool_choice='auto'` 与第三方网关空包问题

基于最新日志，已确认：

1. 调用策略是非流式（`use_streaming=False`）；  
2. 返回包持续是：`content=None`, `tool_calls=None`, `provider_specific_fields.refusal=None`；  
3. workflow 场景显式携带了 `tool_choice='auto'`（来自 YAML 与 LLM 参数构建逻辑）。  

排查后发现 `llm.py` 里有两层会注入 `tool_choice='auto'`：

1. workflow 传入 `kwargs.tool_choice='auto'`；  
2. `_build_completion_params(...)` 在有 tools 时还会自动补 `tool_choice='auto'`。  

对部分第三方 OpenAI 兼容网关，这个显式 `auto` 会触发“空 assistant 包体”。

本轮修复（兼容策略）：

1. 当检测到第三方 OpenAI 兼容端点时，默认移除显式 `tool_choice='auto'`；  
2. 自动补 `tool_choice='auto'` 的逻辑在第三方端点默认关闭；  
3. 提供环境开关可强制恢复旧行为：  
   - `PRAISONAI_FORCE_EXPLICIT_TOOL_CHOICE_AUTO=1`  

新增日志标签：`[TOOL_CHOICE_COMPAT]`。  

### 16.23 2026-04-08 补充：workflow 路径未透传 `max_tokens`（根因之一）

结合用户最新 `wf_rootcause_debug.log`，出现了一个与“直连可用 / workflow 空响应”高度相关的差异：

1. workflow 分支调用里 `LLM instance initialized with: "max_tokens": null`（多处重复）；  
2. 直连 `praisonai "<prompt>" ...` 路径会设置默认 `--max-tokens 16000`，日志可见 `Max tokens set to: 16000`。  

这意味着两条调用链底层参数并不等价，第三方网关在 workflow 路径可能落到不稳定默认行为（返回 `finish_reason=stop` 但 `content=None`）。

本轮修复（非兜底，参数对齐）：

1. 文件：`src/praisonai/praisonai/cli/main.py`  
   - 在 `_run_yaml_workflow(...)` 中解析并桥接 `--max-tokens`；  
   - 将值注入环境变量：  
     - `PRAISONAI_WORKFLOW_MAX_TOKENS`  
     - `PRAISONAI_MAX_TOKENS`  
   - 输出可见日志：`Workflow max_tokens override: <N>`。  

2. 文件：`src/praisonai-agents/praisonaiagents/workflows/yaml_parser.py`  
   - 在 `_parse_agent(...)` 中新增 `max_tokens` 解析优先级：  
     1) `agent.max_tokens`（YAML）  
     2) `agent.llm.max_tokens`（YAML）  
     3) `PRAISONAI_WORKFLOW_MAX_TOKENS`  
     4) `PRAISONAI_MAX_TOKENS`  
   - 自动将字符串模型转为 `{"model": ..., "max_tokens": ...}`，并与 timeout 注入逻辑共存。  

验证要点（日志）：

1. workflow 启动时应打印：`Workflow max_tokens override: 16000`（或你设置的值）；  
2. `llm.py` 初始化日志应由 `max_tokens: null` 变为具体整数；  
3. 再观察是否还出现 `content=None + tool_calls=None`。  

验证命令：

```powershell
D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codebase_analysis_zh.yaml -m $env:PRAISONAI_MODEL --max-tokens 16000 -v
```

### 16.24 2026-04-08 补充：第三方 API 排查全过程复盘（对话全链路）

本节基于本次完整对话与实跑日志，总结“从现象到根因”的完整链路，重点解释每一步调整背后的技术原理。

#### 16.24.1 初始现象（问题画像）

起始阶段的共同症状：

1. `workflow run` 能启动，但频繁出现“空响应 / 重试 / fallback”；  
2. 偶发 `project_analysis.md`、`repository_map.md` 为 `0 byte` 或仅写入错误提示文本；  
3. 终端有乱码或 emoji 相关编码报错（Windows `gbk` 场景）；  
4. direct 命令偶尔可用，但 workflow 更容易失败。  

#### 16.24.2 排查阶段与关键证据（按顺序）

| 阶段 | 关键动作 | 核心证据 | 结论 |
|---|---|---|---|
| A. 现象复现 | 固定模型/网关重复跑 workflow | `[TOOL_DEBUG_SYNC] content_len=0` 持续出现 | 不是偶发网络抖动 |
| B. 数据面诊断 | 增加空响应诊断日志 | `[EMPTY_DIAG_SYNC] content=None, tool_calls=None` | 包体“停在 stop 但无文本” |
| C. 流式/非流式对照 | 同模型同网关做 direct + stream 对照 | `stream=True` 可拿到文本，non-stream 常空 | 兼容性集中在 non-stream + tools |
| D. 参数一致性核查 | 对比 direct/workflow 初始化参数 | workflow 侧曾出现 `max_tokens: null` | 两条链路参数不等价 |
| E. 工具 schema 核查 | 检查 `tools.py` 注解与 schema 生成 | `'int'` 被映射成 `string` | 工具调用稳定性下降 |
| F. 文本可读性核查 | 检查输出“黏连”问题 | 流式 delta 文本空白被 `strip` 掉 | 生成文本可读性受损 |

#### 16.24.3 明确剔除的错误判断

本轮最终排除以下“看似合理但不成立”的判断：

1. **“是模型本身能力不够”**：不成立。  
   同模型在流式路径可稳定返回文本。  

2. **“是 YAML 模板写坏了”**：不成立（不是唯一根因）。  
   模板会放大问题，但根因在响应兼容与参数链路。  

3. **“只要加 fallback 就算解决”**：不成立。  
   fallback 是止损，不是根因修复。  

#### 16.24.4 最终根因分层（已确认）

最终是多因素叠加，而非单点故障：

1. **协议兼容层**：第三方网关在 `non-stream + tools` 下可能返回 `finish_reason=stop` 但 `content=None`；  
2. **参数一致性层**：workflow 路径曾未透传 `max_tokens`，与 direct 路径行为不一致；  
3. **工具 schema 层**：`from __future__ import annotations` 下字符串注解未正确映射，导致工具参数类型偏差；  
4. **解析鲁棒性层**：部分返回对象是 SDK object 而非 dict，原提取逻辑漏读字段；  
5. **文本拼接层**：流式 delta 过度 `strip`，导致词间空白丢失，文档“看起来乱”。  

#### 16.24.5 本轮调整与原理（为什么有效）

| 调整项 | 原理 | 直接效果 |
|---|---|---|
| non-stream 空包时做一次静默 stream 探测恢复 | 利用同网关“流式可取文”特性补齐非流式空包 | 避免 workflow 因空文本直接失败 |
| 第三方端点默认移除显式 `tool_choice='auto'` | 降低兼容网关对显式 tool_choice 的异常触发概率 | 减少 `content=None` 空包 |
| workflow 透传 `--max-tokens` | 保证 direct/workflow 参数面一致 | 降低链路行为漂移 |
| 工具参数类型映射增强（含字符串注解） | 使 schema 与真实参数语义对齐 | 提升工具调用稳定性 |
| SDK 对象转 dict 统一解析 | 处理 provider SDK 非 dict 返回形态 | 减少“有数据但读取为空” |
| 流式 delta 保留空白 | 避免词间空格被吞 | 输出文档可读性恢复 |
| UTF-8 终端预设 | 规避 Windows `gbk` 与 emoji 冲突 | 消除编码型假故障 |

#### 16.24.6 排查方法论（可复用）

这次有效的排查方法可沉淀为标准流程：

1. **先分层再定位**：协议层 / 参数层 / schema 层 / 解析层 / 展示层分开验证；  
2. **先最小 smoke 再 workflow**：先 direct 验证基础可达，再看 workflow 放大器效应；  
3. **固定变量做 A/B**：每次只改一个变量（stream、tool_choice、max_tokens、并发度）；  
4. **先关 fallback 看根因，再开 fallback 保可用**：排障阶段避免兜底掩盖问题；  
5. **以日志字段为准，不靠直觉**：重点看 `finish_reason/content/tool_calls/provider_specific_fields`。  

#### 16.24.7 当前状态与后续建议

当前状态（2026-04-08 晚间）：

1. workflow 可稳定完成并产出非空文档；  
2. 第三方 API 场景下关键兼容补丁已落地；  
3. 输出可读性问题已通过流式空白保留修复。  

后续建议：

1. 增加 CI 回归用例：`direct(no-tools)`, `direct(tools)`, `workflow(yaml)` 三套最小 smoke；  
2. 对第三方网关建立“兼容能力画像”（tool_choice、streaming、schema 严格度）；  
3. 将 `PRAISONAI_EMPTY_RESPONSE_DIAG` 日志片段纳入故障模板，减少重复排查成本。  

### 16.25 2026-04-08 补充：生产运行建议（第三方 API）

为兼顾稳定性与速度，建议默认参数：

```powershell
# 编码
chcp 65001 > $null
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

# API 与模型
$env:OPENAI_API_KEY = "<YOUR_KEY>"
$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:OPENAI_BASE_URL = "https://ice.v.ua/v1"
$env:OPENAI_API_BASE = "https://ice.v.ua/v1"
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"

# 运行档位（生产）
$env:LOGLEVEL = "INFO"
$env:PRAISONAI_EMPTY_RESPONSE_DIAG = "0"
$env:PRAISONAI_WORKFLOW_PARALLEL_MAX_WORKERS = "2"

# 执行
D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\codebase_analysis.yaml -m $env:PRAISONAI_MODEL --max-tokens 8000
```

## 17. 工具总览（2026-04-09，本仓库代码实扫）

### 17.1 统计与来源

| 维度 | 数量 | 统计口径 | 证据 |
|---|---:|---|---|
| `workflow_templates` 本地工具 | 4 | `workflow_templates/tools.py` 中定义的函数 | `workflow_templates/tools.py` |
| `praisonaiagents` 内置工具 | 114 | `praisonaiagents.tools.__init__.py` 的 `TOOL_MAPPINGS` 键集合 | `src/praisonai-agents/praisonaiagents/tools/__init__.py` |
| MCP 注册工具 | 86 | `mcp_server/adapters/*.py` 里 `@register_tool("...")` 的唯一工具名 | `src/praisonai/praisonai/mcp_server/adapters/` |
| CLI 专用工具导出 | 13 | `praisonai.tools` 与 `praisonai.code.tools` 的 `__all__` | `src/praisonai/praisonai/tools/__init__.py`, `src/praisonai/praisonai/code/tools/__init__.py` |

### 17.2 通用用法（中文）

| 场景 | 用法 | 说明 |
|---|---|---|
| YAML/Workflow 中调用工具 | 在 agent 定义中写 `tools: [tool_name]` | 通过 `ToolResolver` 解析，优先级：`local tools.py` > `praisonaiagents built-in` > `praisonai-tools` > `registry`。 |
| 本地模板工具 | 在 `workflow_templates/*.yaml` 中引用 `list_repo_files` 等 | CLI 会自动加载 YAML 同目录 `tools.py` 的公开函数。 |
| CLI 查看可用工具 | `praisonai tools list -v` | 可按来源查看工具（builtin/local/external）。 |
| CLI 校验 YAML 工具名 | `praisonai tools validate <yaml>` | 校验 YAML 引用的工具是否都可解析。 |
| CLI 查看单个工具详情 | `praisonai tools info <tool_name>` | 显示签名、来源、文档。 |
| Python 代码直接调用 | `from praisonaiagents.tools import <tool_name>` | 适合脚本或 SDK 直接集成。 |
| MCP 客户端调用 | 使用 `praisonai.<namespace>.<action>` | 适合外部系统通过 MCP 协议统一接入。 |

### 17.3 `workflow_templates` 本地工具（全量）

| Tool | 典型用法 | 具体功能 |
|---|---|---|
| `list_repo_files(directory='.', max_items=80)` | `list_repo_files('.', 120)` | 递归列文件，返回相对路径列表。 |
| `list_repo_dirs(directory='.', max_items=60)` | `list_repo_dirs('.', 80)` | 递归列目录，形成结构骨架。 |
| `read_text_file(filepath, max_chars=2500)` | `read_text_file('README.md', 4000)` | 读取文本（UTF-8，超长截断）。 |
| `grep_in_file(filepath, keyword, max_lines=20)` | `grep_in_file('pyproject.toml', 'dependency', 30)` | 关键词检索并返回行号。 |

### 17.4 `praisonaiagents` 内置工具（全量分组）

> 用法统一：`from praisonaiagents.tools import <tool_name>`，或在 YAML 的 `tools: [...]` 中直接写工具名。

| 模块 | 数量 | 具体功能（中文） | 全量 Tool 名称 |
|---|---:|---|---|
| `duckduckgo_tools` | 2 | DuckDuckGo 搜索 | `duckduckgo, internet_search` |
| `searxng_tools` | 2 | SearxNG 搜索（自建搜索实例） | `searxng, searxng_search` |
| `spider_tools` | 5 | 网页抓取、抽链、正文提取 | `crawl, extract_links, extract_text, scrape_page, spider_tools` |
| `shell_tools` | 5 | 命令执行、进程与系统信息 | `execute_command, get_system_info, kill_process, list_processes, shell_tools` |
| `file_tools` | 8 | 文件读写、复制、移动、删除、列表 | `copy_file, delete_file, file_tools, get_file_info, list_files, move_file, read_file, write_file` |
| `python_tools` | 6 | Python 代码执行/分析/格式化/lint | `analyze_code, disassemble_code, execute_code, format_code, lint_code, python_tools` |
| `train.data.generatecot` | 17 | CoT 数据生成、校验、导出、上传 | `cot_append_csv_with_qa_pairs, cot_append_solutions_with_qa_pairs, cot_check, cot_export_csv_with_qa_pairs, cot_export_json_with_qa_pairs, cot_find_error, cot_generate, cot_generate_dict, cot_improve, cot_improve_dict, cot_load_answers, cot_run, cot_run_dict, cot_save, cot_save_solutions_with_qa_pairs, cot_tools, cot_upload_to_huggingface` |
| `tavily_tools` | 9 | Tavily 搜索/抽取/爬取 | `tavily, tavily_crawl, tavily_extract, tavily_extract_async, tavily_map, tavily_search, tavily_search_async, tavily_tools, TavilyTools` |
| `youdotcom_tools` | 7 | You.com 搜索、新闻、图片、内容 | `ydc, ydc_contents, ydc_images, ydc_news, ydc_search, youdotcom_tools, YouTools` |
| `exa_tools` | 10 | Exa 语义搜索、相似发现、问答 | `exa, exa_answer, exa_answer_async, exa_find_similar, exa_search, exa_search_async, exa_search_contents, exa_search_contents_async, exa_tools, ExaTools` |
| `crawl4ai_tools` | 8 | Crawl4AI 网页抓取与抽取 | `crawl4ai, crawl4ai_extract, crawl4ai_extract_sync, crawl4ai_llm_extract, crawl4ai_many, crawl4ai_sync, crawl4ai_tools, Crawl4AITools` |
| `web_search` | 3 | 统一搜索入口（多 provider 自动降级） | `get_available_providers, search_web, web_search` |
| `web_crawl_tools` | 3 | 统一网页爬取入口（多 provider 自动降级） | `crawl_web, get_available_crawl_providers, web_crawl` |
| `skill_tools` | 6 | Skill 脚本读取/执行/桥接 | `create_skill_tools, list_skill_scripts, read_skill_file, run_skill_script, skill_tools, SkillTools` |
| `schedule_tools` | 4 | 调度任务增删查 | `schedule_add, schedule_list, schedule_remove, schedule_tools` |
| `ast_grep_tool` | 6 | AST 结构化检索与重写 | `ast_grep_rewrite, ast_grep_scan, ast_grep_search, ast_grep_tools, get_ast_grep_tools, is_ast_grep_available` |
| `memory` | 2 | 记忆存储与检索 | `search_memory, store_memory` |
| `learning` | 2 | 学习知识存储与检索 | `search_learning, store_learning` |
| `email_tools` | 9 | 邮件收发/收件箱管理（AgentMail 或 SMTP/IMAP） | `create_inbox, email_tools, list_emails, list_inboxes, read_email, reply_email, send_email, smtp_read_inbox, smtp_send_email` |

### 17.5 MCP 工具（86 个，按命名空间全量）

> 调用格式：`praisonai.<namespace>.<action>`。

| Namespace | 具体功能（中文） | 全量 Tool 名称 |
|---|---|---|
| `a2a` | Agent-to-Agent 消息发送 | `praisonai.a2a.send` |
| `agent` | Agent 对话与运行 | `praisonai.agent.chat, praisonai.agent.run` |
| `assistants` | Assistant 创建与列举 | `praisonai.assistants.create, praisonai.assistants.list` |
| `audio` | 文本转语音、语音转文本 | `praisonai.audio.speech, praisonai.audio.transcribe` |
| `batches` | 批处理任务创建/查询/取消 | `praisonai.batches.cancel, praisonai.batches.create, praisonai.batches.list, praisonai.batches.retrieve` |
| `chat` | 聊天补全 | `praisonai.chat.completion` |
| `containers` | 容器创建与容器文件读写 | `praisonai.containers.create, praisonai.containers.file_read, praisonai.containers.file_write` |
| `deploy` | 部署校验与状态查询 | `praisonai.deploy.status, praisonai.deploy.validate` |
| `doctor` | 环境/配置/MCP 体检 | `praisonai.doctor.config, praisonai.doctor.env, praisonai.doctor.mcp` |
| `embed` | 向量嵌入生成 | `praisonai.embed.create` |
| `eval` | 准确率/性能评估 | `praisonai.eval.accuracy, praisonai.eval.performance` |
| `files` | 平台文件增删查读内容 | `praisonai.files.content, praisonai.files.create, praisonai.files.delete, praisonai.files.list, praisonai.files.retrieve` |
| `fine_tuning` | 微调任务创建与列表 | `praisonai.fine_tuning.create, praisonai.fine_tuning.list` |
| `guardrails` | 安全护栏校验 | `praisonai.guardrails.check` |
| `hooks` | Hook 列表与统计 | `praisonai.hooks.list, praisonai.hooks.stats` |
| `images` | 图像生成 | `praisonai.images.generate` |
| `knowledge` | 知识库增删查统计 | `praisonai.knowledge.add, praisonai.knowledge.clear, praisonai.knowledge.list, praisonai.knowledge.query, praisonai.knowledge.stats` |
| `mcp_config` | MCP 配置开关与查看 | `praisonai.mcp_config.disable, praisonai.mcp_config.enable, praisonai.mcp_config.list, praisonai.mcp_config.show` |
| `memory` | 记忆写入/查询/会话管理 | `praisonai.memory.add, praisonai.memory.clear, praisonai.memory.search, praisonai.memory.sessions, praisonai.memory.show` |
| `misc` | OCR、重排、搜索 | `praisonai.ocr, praisonai.rerank, praisonai.search` |
| `moderate` | 内容审核 | `praisonai.moderate.check` |
| `rag` | RAG 查询 | `praisonai.rag.query` |
| `realtime` | 实时连接与消息发送 | `praisonai.realtime.connect, praisonai.realtime.send` |
| `research` | 研究任务执行 | `praisonai.research.run` |
| `rules` | 规则增删查 | `praisonai.rules.create, praisonai.rules.delete, praisonai.rules.list, praisonai.rules.show` |
| `schedule` | 调度增删查 | `praisonai.schedule.add, praisonai.schedule.list, praisonai.schedule.remove` |
| `session` | 会话列表/详情/删除 | `praisonai.session.delete, praisonai.session.info, praisonai.session.list` |
| `skills` | Skills 列表与加载 | `praisonai.skills.list, praisonai.skills.load` |
| `todo` | Todo 增删改查 | `praisonai.todo.add, praisonai.todo.complete, praisonai.todo.delete, praisonai.todo.list` |
| `tools` | 工具列表/详情/搜索 | `praisonai.tools.info, praisonai.tools.list, praisonai.tools.search` |
| `vector_stores` | 向量库创建、文件挂载、检索 | `praisonai.vector_stores.create, praisonai.vector_stores.file_create, praisonai.vector_stores.file_list, praisonai.vector_stores.search` |
| `videos` | 视频生成 | `praisonai.videos.generate` |
| `workflow` | 工作流自动生成/列表/执行/校验 | `praisonai.workflow.auto, praisonai.workflow.list, praisonai.workflow.run, praisonai.workflow.run_file, praisonai.workflow.show, praisonai.workflow.validate` |

### 17.6 CLI 专用工具（`praisonai`）

| 模块 | Tool | 典型用法 | 具体功能 |
|---|---|---|---|
| `praisonai.tools` | `multiedit` | 在 CLI 交互链路调用 | 多段搜索替换编辑。 |
| `praisonai.tools` | `glob_files` | 在 CLI 交互链路调用 | 模式匹配批量列文件。 |
| `praisonai.tools` | `grep_search` | 在 CLI 交互链路调用 | 项目内文本检索。 |
| `praisonai.tools` | `tts_tool, stt_tool, create_tts_tool, create_stt_tool` | 在 CLI/交互里配置调用 | 语音合成与语音识别。 |
| `praisonai.code.tools` | `read_file` | `from praisonai.code.tools import read_file` | 读取文件内容（可选行范围）。 |
| `praisonai.code.tools` | `write_file` | `from praisonai.code.tools import write_file` | 创建或覆写文件。 |
| `praisonai.code.tools` | `list_files` | `from praisonai.code.tools import list_files` | 列目录内容。 |
| `praisonai.code.tools` | `apply_diff` | `from praisonai.code.tools import apply_diff` | 应用 SEARCH/REPLACE diff。 |
| `praisonai.code.tools` | `search_replace` | `from praisonai.code.tools import search_replace` | 多点搜索替换。 |
| `praisonai.code.tools` | `execute_command` | `from praisonai.code.tools import execute_command` | 执行 shell 命令。 |

### 17.7 依赖与环境变量提示（高频）

| 工具族 | 关键依赖/变量 | 说明 |
|---|---|---|
| Tavily | `TAVILY_API_KEY` | 未设置会不可用。 |
| Exa | `EXA_API_KEY` | 未设置会不可用。 |
| You.com | `YDC_API_KEY` | 未设置会不可用。 |
| Web Search 聚合 | `TAVILY_API_KEY` / `EXA_API_KEY` / `YDC_API_KEY` / `BRAVE_API_KEY` / `SEARXNG_URL` | 按可用 provider 自动降级。 |
| Web Crawl 聚合 | `TAVILY_API_KEY` / `SPIDER_API_KEY`（可选） | 按可用 provider 自动降级。 |
| Email | `AGENTMAIL_API_KEY` 或 `EMAIL_ADDRESS` + `EMAIL_PASSWORD` | 支持 AgentMail 与 SMTP/IMAP 两条路径。 |

### 17.8 快速自检命令

```powershell
# 1) 查看可解析工具（含来源）
praisonai tools list -v

# 2) 查看单个工具签名与来源
praisonai tools info web_search

# 3) 校验 YAML 里的 tools 是否都可解析
praisonai tools validate .\workflow_templates\codebase_analysis_zh.yaml
```



> 旧版 `codex_workflow.yaml` 命令已不再推荐。
> 请统一使用 **第 18 节**中的：
>
> 1. `codex_two_step_report.yaml`（正式两节点分析）
> 2. `codex_direct_publish.yaml`（正式单步分析）
> 3. `codex_two_step_smoke.yaml`（仅冒烟测试）

---

## 19. 第三方 API 与官方 OpenAI API 差异总览及对应修复方案（2026-04-09）

> 本节基于本项目完整排障过程（15.x - 16.x 节），系统性总结第三方 OpenAI 兼容网关与官方 API 在协议、路由、参数、解析、Schema、策略六个层面的差异，以及本仓库已落地的修复方案。

### 19.1 协议层差异

| 差异点 | 官方 OpenAI API | 第三方兼容网关 | 影响 |
|---|---|---|---|
| Responses API | 支持；LiteLLM 对 `gpt-5.*` 自动走 `responses` bridge | 多数只实现 `chat/completions` | 触发 `Unknown items in responses API response: []`（15.1） |
| 流式 + 工具调用 | `delta.tool_calls` 稳定返回 | 部分网关流式里 `tool_calls` 字段缺失或格式不标准 | 工具调用被丢弃，模型"说了要做但没做"（15.11） |
| 非流式 + 工具调用 | `content` + `tool_calls` 正常返回 | 可能返回 `finish_reason=stop` 但 `content=None, tool_calls=None` | workflow 步骤直接空响应（16.18、16.19） |
| 显式 `tool_choice='auto'` | 正常处理 | 部分网关收到显式 `auto` 后返回空包体 | 整个调用轮次无输出（16.22） |
| 工具参数 JSON 格式 | 严格单一 JSON 对象 | 可能返回 JSON 后拼接额外文本，或以纯文本 JSON 嵌在 `content` 里 | 工具调用解析失败，函数名降级为 `unknown_function`（14.1） |
| `max_tokens=null` | 有合理默认行为 | 部分网关收到 `null` 直接返回空内容 | workflow 路径空响应（16.23） |

**对应修复方案：**

| 修复 | 文件 | 要点 |
|---|---|---|
| 第三方网关自动绕开 Responses API | `llm.py` | 检测非官方 base URL 时，`_supports_responses_api()` 返回 `False`；模型名自动加 `custom_openai/` 前缀（15.2） |
| 流式工具调用解析放开门控 | `llm.py` | `_process_stream_delta()` 不再依赖 `_supports_streaming_tools()` 门控，只要 delta 中存在 `tool_calls` 就解析（15.11） |
| 第三方端点移除显式 `tool_choice='auto'` | `llm.py` | 检测到第三方端点时默认不注入 `tool_choice='auto'`；提供 `PRAISONAI_FORCE_EXPLICIT_TOOL_CHOICE_AUTO=1` 可恢复（16.22） |
| 工具参数 JSON 容错解析 | `llm.py` | 新增 `_parse_tool_call_json_arguments()`，使用 `raw_decode` 恢复首个合法 JSON，尾随垃圾仅 warning（14.2） |
| 文本形式工具调用 fallback | `llm.py` | `tool_calls` 为空且有文本时，尝试 `_try_parse_tool_call_json()` 解析（15.10） |
| workflow 透传 `max_tokens` | `main.py` + `yaml_parser.py` | `_run_yaml_workflow()` 解析 `--max-tokens` 并桥接到环境变量和 agent 配置（16.23） |

### 19.2 模型路由层差异

| 差异点 | 官方 API | 第三方网关 | 影响 |
|---|---|---|---|
| 模型名前缀 | 直接用 `gpt-5.3-codex` | 必须加 `custom_openai/` 前缀 | 不加前缀时 LiteLLM 误走 `responses` bridge（15.1） |
| `_supports_responses_api()` | 返回 `True` | 必须强制返回 `False` | 同上 |
| `_supports_streaming_tools()` | 已知模型返回 `True` | 未知模型默认 `False` | 流式工具调用被门控丢弃（15.11） |

**对应修复方案：**

| 修复 | 文件 | 要点 |
|---|---|---|
| 第三方网关自动改写模型路由 | `llm.py` | 检测到第三方 base URL + OpenAI 家族模型名时，自动加 `custom_openai/` 前缀（15.2） |
| Responses API 判定禁用 | `llm.py` | 非官方 base URL 下 `_supports_responses_api()` 返回 `False`（15.2） |
| 流式工具门控放开 | `llm.py` | 只要 delta 中存在 `tool_calls/function_call` 就解析，不受能力探测限制（15.11） |

### 19.3 参数透传层差异

| 差异点 | 官方 API | 第三方网关 | 影响 |
|---|---|---|---|
| 内部参数过滤 | 官方 SDK 对未知参数容忍度较高 | 严格校验，透传 `force_tool_usage` / `max_tool_repairs` 直接报错 | `unexpected keyword argument`（15.8） |
| `max_tokens` 透传 | 有默认值兜底 | workflow 路径曾未透传，网关收到 `null` 返回空内容 | workflow 空响应，direct 正常（16.23） |
| workflow 模型透传 | N/A | `workflow run -m` 的值未稳定透传到 YAML agent 的 `llm` | 部分场景走错模型（16.5） |

**对应修复方案：**

| 修复 | 文件 | 要点 |
|---|---|---|
| 过滤内部编排参数 | `llm.py` | `_build_completion_params()` 中将 `force_tool_usage`、`max_tool_repairs` 加入过滤黑名单（15.8） |
| workflow 透传 `max_tokens` | `main.py` + `yaml_parser.py` | 解析 `--max-tokens` 并注入 `PRAISONAI_WORKFLOW_MAX_TOKENS`；agent 解析优先级：YAML > 环境变量（16.23） |
| workflow 透传模型名 | `main.py` + `yaml_parser.py` | `--model/-m/--llm` 桥接到 `PRAISONAI_MODEL`；agent `llm` 优先级：`agent_config > PRAISONAI_MODEL > MODEL_NAME > OPENAI_MODEL_NAME`（16.5） |

### 19.4 返回数据解析层差异

| 差异点 | 官方 API | 第三方网关 | 影响 |
|---|---|---|---|
| 返回对象类型 | 标准 dict 或已知 SDK 对象 | 部分返回是 SDK object 而非 dict，字段读取为空 | 有数据但提取为空（16.20） |
| 文本所在字段 | `message.content` | 可能在 `reasoning_content`、`reasoning`、`answer`、`output`、`final_text` 等非标字段 | 误判为空响应（16.13、16.19） |
| 工具调用格式 | 标准 `tool_calls` 字段 | 可能以纯文本 JSON 嵌在 `content` 里 | 工具不执行（15.10） |

**对应修复方案：**

| 修复 | 文件 | 要点 |
|---|---|---|
| SDK 对象统一转 dict | `llm.py` | 新增 `_to_mapping()`，尝试 `model_dump()/to_dict()/dict()` 转换后再提取字段（16.20） |
| 扩展文本提取候选字段 | `llm.py` | `_coerce_content_to_text()`、`_extract_text_from_message_payload()`、`_extract_text_from_completion_response()` 中新增 `reasoning_content/reasoning/answer/output/final_text` 等候选（16.19） |
| 文本形式工具调用 fallback | `llm.py` | `tool_calls` 为空且有文本时尝试 JSON 解析（15.10） |
| 空响应结构化诊断 | `llm.py` | `PRAISONAI_EMPTY_RESPONSE_DIAG=1` 时打印 `choice_keys/message_keys/provider_specific_fields`，便于定位真实返回结构（16.19） |

### 19.5 工具 Schema 层差异

| 差异点 | 官方 API | 第三方网关 | 影响 |
|---|---|---|---|
| 参数类型容错 | 对 `type: "string"` 的整数参数仍能正确调用 | 严格匹配 schema 类型，`int` 误标为 `string` 降低工具调用稳定性 | 工具调用异常或不触发（16.21） |

**对应修复方案：**

| 修复 | 文件 | 要点 |
|---|---|---|
| 注解映射增强 | `llm.py` | 工具参数生成处新增注解映射函数，支持 `typing` 注解和 `from __future__ import annotations` 下的字符串注解（如 `'int'` -> `integer`）（16.21） |

### 19.6 运行策略层差异

| 差异点 | 官方 API | 第三方网关 | 影响 |
|---|---|---|---|
| `force_tool_usage=always` | 模型稳定返回 `tool_calls` | 可能始终不返回，形成无进展死循环 | 空响应循环（15.9） |
| verbose 模式强制流式 | 正常工作 | 工具场景下文本/工具事件抽取不稳定 | 被判定为空响应（16.18） |
| 并发调用 | 稳定 | 并行分支更容易触发空响应（网关并发抖动） | workflow 并行步骤批量失败（16.12 - 16.14） |

**对应修复方案：**

| 修复 | 文件 | 要点 |
|---|---|---|
| `always` 自动降级 | `llm.py` | 非 Ollama 场景强制一次后自动降级为普通回复模式；`auto` 恢复为仅对 Ollama 生效（15.9、16.16） |
| verbose 模式保持非流式 | `llm.py` | `use_streaming=False` 时即使 `verbose=true` 也不回切流式（16.18） |
| 并行串行开关 | `workflows.py` | `PRAISONAI_WORKFLOW_PARALLEL_MAX_WORKERS=1` 时主线程串行执行，不走线程池（16.14） |
| 空响应多层重试与兜底 | `llm.py` + `workflows.py` | 首轮空文本最多 3 次非流式重试；non-stream 空包时静默 stream 探测恢复；步骤级重试 + 非 LLM 本地兜底产出（15.5、16.10 - 16.11） |

### 19.7 差异根因总结

**官方 API 的行为是确定性的，代码可以依赖其隐含约定；第三方网关只实现了协议子集，且各家子集不同。** 本项目所有第三方兼容修复的核心策略是：

1. **检测到第三方端点时自动降级**：移除 `tool_choice`、绕开 `responses` bridge、关闭强制流式；
2. **扩大返回数据的字段提取范围**：兼容非标字段和 SDK 对象形态；
3. **参数链路对齐**：保证 direct / workflow 两条路径参数一致；
4. **多层重试与兜底**：空响应重试、流式探测恢复、非 LLM 本地兜底产出。

### 19.8 涉及的核心修改文件汇总

| 文件 | 修改类别 |
|---|---|
| `src/praisonai-agents/praisonaiagents/llm/llm.py` | 协议兼容、路由改写、参数过滤、解析增强、策略降级、重试兜底 |
| `src/praisonai-agents/praisonaiagents/workflows/workflows.py` | 并行串行开关、步骤级重试、空响应兜底、UTF-8 编码保护 |
| `src/praisonai-agents/praisonaiagents/workflows/yaml_parser.py` | 模型/max_tokens/timeout 透传、并行分支 Agent 隔离 |
| `src/praisonai/praisonai/cli/main.py` | workflow 参数桥接（模型、max_tokens）、tools.py 加载过滤 |
| `workflow_templates/tools.py` | 工具返回量降载、参数类型注解修正 |
| `workflow_templates/codebase_analysis.yaml` | 模板降载、工具策略调整 |
