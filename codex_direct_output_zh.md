## 整体架构

该项目是一个 **Go + Gin 的协议适配网关**，核心目标是把上游客户端（OpenAI/Anthropic 风格请求）转换并转发到 **Amazon Q**，再将返回结果按客户端期望格式回传。

架构分层可概括为：

1. **入口层**
- `main.go`：初始化日志、加载环境变量、初始化可用 bearer、启动 token 刷新器、启动 Gin 服务。
- `router.go`：注册 API 路由与中间件。

2. **鉴权层**
- `Middleware/Auth.go`：对 `/v1/*` 进行统一 Bearer/API Key 校验（`BEARER_TOKEN`）。

3. **协议处理层（API）**
- `API/ChatCompletions.go`（未展开）：OpenAI ChatCompletions 入口。
- `API/Messages.go`：Anthropic Messages 入口，支持流式/非流式、web_search 工具分流。
- `API/CountTokens.go`：Anthropic 口径的输入 token 估算。
- `API/Models.go`：拉取 Amazon Q 模型并适配为 OpenAI/Anthropic 两种模型列表格式。
- `API/DebugToken.go`、`API/DebugAnthropic2Q.go`：调试辅助端点。
- `API/NotFound.go`：兜底 404。

4. **模型定义层（Models）**
- `Models/OpenAI.go`、`Models/Anthropic.go`、`Models/Q.go`：三套协议结构体与（反）序列化细节。
- `Models/Tokens.go`：刷新 token、access token 数据模型。

5. **转换与基础能力层（Utils）**
- 协议映射：`Anthropic2Q.go`、`Openai2Q.go`、`Q2Openai.go`、`Anthropic2Q/Q2Anthropic`（后者未见完整文件）。
- token 管理：`GetBearer.go`（账号加载、access token 刷新、轮换、禁用逻辑）。
- 网络：`Proxy.go`（代理 + uTLS + 强制 HTTP/1.1）。
- 校验：`Validation.go`。
- 日志：`Logger.go`。
- 内容修正：`EnsureNonEmptyContent.go`、`removeBase64Header.go`、`getExtension.go`。

---

## 功能详细描述

1. **统一 API 网关能力**
- 暴露 `/v1/chat/completions`、`/v1/messages`、`/v1/messages/count_tokens`、`/v1/models`。
- 同时保留 `/debug/*` 端点便于诊断 token 与映射逻辑。

2. **双协议兼容**
- 输入兼容 OpenAI 与 Anthropic 请求结构。
- 输出可按请求头/路径语义返回 OpenAI 或 Anthropic 风格响应。

3. **Amazon Q 转发与模型发现**
- `Models.go` 通过固定 AWS 风格 Header + `Authorization: Bearer <token>` 调 Q 的模型列表接口。
- 返回结果扩展出 `-thinking` 变体模型，增强兼容性。

4. **工具调用与多模态支持**
- OpenAI/Anthropic 请求中的 tools 会被转换为 Q 的 tool schema。
- OpenAI 图像（base64 data URL）可被拆解并映射到 Q 的 image 字段。
- 流式响应中会累积 Q 的 tool_use 事件，拼装成 OpenAI tool_calls。

5. **token 生命周期管理**
- 支持从 CSV 或远程 API 加载账号（由 `ACCOUNT_SOURCE` 控制）。
- 刷新 access token，维护可用 token 池与轮转索引，失败账号可禁用/封禁。
- 服务启动前先获取一次 bearer；后台刷新器持续保活。

6. **部署与运行**
- Docker 多阶段构建（`golang:1.24-alpine` -> `alpine`）。
- 默认端口 `4000`，可通过 `.env` 覆盖。
- `docker-compose` 通过只读挂载 `.env` 和资源目录运行。

---

## 关键代码逻辑与调用链

1. **启动链路**
- `main.main`
-> `Utils.InitLoggers`
-> `godotenv.Load`
-> `Utils.GetBearer`（预热 token）
-> `Utils.StartTokenRefresher`
-> `setupRouter`
-> `gin.Run`.

2. **鉴权链路（/v1）**
- `router.setupRouter`
-> `Middleware.BearerAuth`
-> 校验 `x-api-key` 或 `Authorization: Bearer ...`
-> 失败直接 401/500，中止后续处理。

3. **Anthropic 请求主链**
- `API.Messages`
-> `ShouldBindJSON`
-> `Utils.ValidateAnthropicRequest`
-> 若检测 `web_search` 工具：走 MCP 分支（流式/非流式）
-> 否则走 Amazon Q 分支：
  - `Utils.MapAnthropicToAmazonQ`
  - 组装 AWS 风格请求头 + bearer
  - 请求 Q 接口
  - 将返回映射为 Anthropic 响应（流式/非流式）。

4. **OpenAI 请求主链（推断）**
- `API.ChatCompletions`（文件未展开）
-> `Utils.ValidateChatCompletionRequest`
-> `Utils.MapOpenAiToAmazonQ`
-> 调用 Q
-> `Utils.ProcessQStreamToOpenAI`（流式时）或对应非流式转换
-> 输出 OpenAI chat completion 格式。

5. **模型列表链路**
- `API.ListModels`
-> `fetchQModels`（调用 Q ListAvailableModels）
-> 根据请求头判断输出格式：
  - OpenAI：`handleOpenAIModels`
  - Anthropic：`handleAnthropicModels`.

6. **token 管理链路**
- `Utils.GetBearer`（内部 `sync.Once` 初始化）
-> 按 `ACCOUNT_SOURCE` 从 CSV/API 加载 refresh token
-> `GetAccessTokenFromRefreshToken`（逐个尝试）
-> 维护 `RefreshTokens`、`ActiveTokens`、索引与锁
-> 后台定时刷新（`StartTokenRefresher`）。

---

## 不确定性与边界说明

1. `API/ChatCompletions.go`、`API/DebugAnthropic2Q.go`、`API/DebugToken.go` 以外部分、`Utils/Q2Anthropic.go`、`Utils/EnsureNonEmptyContent.go`、`Utils/removeBase64Header.go`、`Utils/GetBearer.go` 后半段均未完整展开，因此：
- OpenAI 非流式最终响应字段细节；
- Anthropic 流式事件拼装细节；
- token 刷新调度策略（精确周期、淘汰条件）；
存在不确定性。

2. `Models/Q.go`、`Models/OpenAI.go`、`Models/Anthropic.go` 内容被截断，以下项仅能部分确认：
- 全量 SSE 事件类型覆盖范围；
- 某些 tool/result block 的完整序列化行为；
- 个别字段默认值与边界处理。

3. 从已给片段看，环境状态 `OperatingSystem` 在映射时写死为 `macos`，是否有平台自适应逻辑无法确认（可能在未展开代码中处理）。