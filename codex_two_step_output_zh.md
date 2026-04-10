## 整体架构

### 1) 系统定位
该项目是一个 **Amazon Q API 适配网关**，对外兼容两类上游协议风格：
- OpenAI Chat Completions 风格（`/v1/chat/completions`）
- Anthropic Messages 风格（`/v1/messages`、`/v1/messages/count_tokens`）

核心职责是把请求在不同协议之间做转换，并转发到 Amazon Q（`AMAZON_Q_URL`），再把响应转换回客户端期望格式。

### 2) 分层与模块
- 入口层：`main.go`
  - 加载环境变量、初始化日志、初始化/刷新 Bearer、启动 Gin 服务。
- 路由层：`router.go`
  - `/v1/*` 受 `Middleware/BearerAuth.go` 保护。
  - debug 路由不鉴权：`/debug/token`、`/debug/anthropic2q`。
- API 处理层：`API/*.go`
  - 协议入口、参数绑定校验、流式/非流式分发、模型列表、token 统计、调试接口。
- 模型层：`Models/*.go`
  - OpenAI / Anthropic / Amazon Q 结构体定义，含多态 JSON 反序列化逻辑。
- 工具层：`Utils/*.go`
  - 协议映射（`Openai2Q`、`Anthropic2Q`、`Q2Openai`）
  - 鉴权 token 拉取与轮换（`GetBearer`）
  - 网络与 TLS 指纹（`Proxy` + uTLS）
  - 校验、日志、内容兜底等通用能力。

### 3) 部署架构
- `Dockerfile` 两阶段构建：Go 编译 -> Alpine 运行。
- `docker-compose.yml` 暴露 `4000`，挂载 `.env`（只读）与 `resources`（日志/账号数据）。

---

## 功能详细描述

### 1) 鉴权与访问控制
- 业务 API（`/v1/*`）要求 `BEARER_TOKEN`：
  - 支持 `Authorization: Bearer <token>` 或 `x-api-key`。
  - 缺失/格式错误/不匹配返回 401。
- 服务内部访问 Amazon Q 使用另一套 Bearer（`Utils.GetBearer()` 获取），与外部调用 token 分离。

### 2) 协议兼容与转换
- OpenAI -> Q：`Utils/MapOpenAiToAmazonQ`
  - 处理 `system/user/assistant/tool` 消息、工具定义、图像 base64、tool calls 与 tool results。
- Anthropic -> Q：`Utils/MapAnthropicToAmazonQ`
  - 处理 system 注入、消息交替、工具定义（超长 description 特殊处理）、复杂 content block/tool_use。
- Q -> OpenAI：`Utils/ProcessQStreamToOpenAI`
  - 解析 eventstream，聚合 content 与 tool call 参数，保证 arguments 为合法 JSON。
- （从文件清单看）应存在 Q -> Anthropic/调试方向转换能力：`Utils/Anthropic2Q.go`、`API/DebugAnthropic2Q.go`。

### 3) 聊天与流式
- `API/Messages.go`：
  - 入参绑定 + `ValidateAnthropicRequest`。
  - 检测 `web_search` 工具后走 MCP 专门路径（stream/non-stream）。
  - 普通路径转发 Amazon Q，支持流式和非流式。
- `API/ChatCompletions.go`（未展开）推断承担 OpenAI 入口同类逻辑。

### 4) 模型与计费相关能力
- `/v1/models`：
  - 实际向 Q 发起 `ListAvailableModels`。
  - 根据请求头判定返回 OpenAI 风格或 Anthropic 风格模型列表。
  - 每个模型额外扩展 `-thinking` 变体。
- `/v1/messages/count_tokens`：
  - 用 `tiktoken cl100k` 估算输入 token。
  - 对 thinking 标签做简单剥离，支持 system/messages/tools 汇总估算。

### 5) Token 账户池与自动刷新
- `Utils/GetBearer.go`：
  - 支持 `csv` 或 `api` 两种账户来源（`.env.example`）。
  - 管理 `RefreshTokens`、`ActiveTokens`、并发锁、轮转索引。
  - 支持 API 账户缓存到 `resources/api_accounts.json`，异常账户可封禁（调用账户 API）。
- `main.go` 启动时先尝试获取 bearer，再启动后台刷新协程。

### 6) 可观测性
- `Utils/Logger.go`：
  - `resources/error.log` 与 `resources/normal.log`（lumberjack 滚动切割）。
  - Gin 默认输出接入 `NormalLogger`。

---

## 关键代码逻辑与调用链

### 调用链 A：服务启动
1. `main.main`
2. `Utils.InitLoggers`
3. `godotenv.Load`
4. `Utils.GetBearer`（初始化可用访问 token）
5. `Utils.StartTokenRefresher`（后台维护）
6. `setupRouter`
7. `gin.Run`

### 调用链 B：Anthropic 请求（/v1/messages）
1. `router -> API.Messages`
2. `ShouldBindJSON(AnthropicRequest)`
3. `Utils.ValidateAnthropicRequest`
4. 分支：
   - 若包含 `web_search`：`handleMCPStreamingRequest / handleMCPNonStreamingRequest`
   - 否则：`handleAnthropicStreamingRequest / handleAnthropicNonStreamingRequest`
5. 非流式核心：
   - `Utils.MapAnthropicToAmazonQ`
   - 构造 Q HTTP 请求（含 Amazon Q 目标头）
   - `Utils.GetBearer` 注入内部鉴权
   - 请求 Q，解析回包并回写 Anthropic 风格响应
6. 错误统一走 `anthropicError`（含 `request-id`）

### 调用链 C：模型列表（/v1/models）
1. `router -> API.ListModels`
2. `fetchQModels` 请求 Q 的 `ListAvailableModels`
3. 依据 `Authorization/x-api-key` 判断输出格式
4. `handleOpenAIModels` 或 `handleAnthropicModels` 生成兼容响应

### 调用链 D：Token 估算（/v1/messages/count_tokens）
1. `router -> API.CountTokens`
2. 解析 `AnthropicTokenCountRequest`
3. `estimateInputTokens` 汇总 system/messages/tools
4. `countTokens`（tiktoken 编码）返回估算值

### 调用链 E：OpenAI/Anthropic 与 Q 的核心桥接逻辑
- 入站协议对象（OpenAI/Anthropic） -> `Utils/*2Q` 映射 -> Q 请求结构 `Models.QAPIRequest`
- Q eventstream -> `Utils.Q2Openai` 解析与聚合 -> OpenAI SSE/普通响应对象
- 工具调用链路重点：
  - assistant tool_use -> QToolUse
  - tool_result -> QToolResultItem
  - SSE 分片参数 -> 按 `toolUseId` 累积并最终组装 JSON arguments

---

## 不确定性与边界

1. 多个关键文件内容被截断（如 `API/Messages.go`、`Utils/GetBearer.go`、`Utils/Openai2Q.go`、`Models/*.go`），以下细节无法完全确认：
- `ChatCompletions` 的完整分支策略与返回格式细节。
- MCP 路由实现细节与失败重试策略。
- token 刷新调度算法（刷新频率、失效剔除、降级策略）全貌。
- 流式响应中 finish_reason、usage、tool-call 增量拼装的全部边界处理。

2. 从上下文可见 `for i := range len(req.Messages)` 这一写法（`Utils/Anthropic2Q.go`片段）在标准 Go 中可疑，可能是截断/转录问题；是否真实存在编译问题 **不确定**。

3. 未提供测试、CI 具体脚本与运行结果，故无法确认当前实现与声明行为在所有边界条件下都已被验证。

---
生成日期：2026-04-09
