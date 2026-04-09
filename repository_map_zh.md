## 目录结构地图

```text
/
├─ .github/
│  ├─ workflows/                  # 控制平面：CI/CD、测试、发布、AI协作编排
│  │  ├─ test-*.yml
│  │  ├─ benchmark.yml
│  │  ├─ python-package.yml
│  │  ├─ python-publish.yml
│  │  ├─ docker-publish.yml
│  │  ├─ release.yml
│  │  ├─ claude*.yml
│  │  └─ gemini*.yml
│  └─ actions/                    # 执行平面：本地可复用 Action
│     ├─ claude-code-action/action.yml
│     ├─ claude-issue-triage-action/action.yml
│     └─ gemini/action.yml
├─ docker/                        # 运行平面：容器化封装与隔离
│  ├─ bots/
│  └─ call/
├─ examples/                      # 消费平面：用户侧示例入口
│  ├─ basic/
│  ├─ cli/
│  ├─ capabilities/
│  ├─ checkpoints/
│  ├─ benchmark/
│  ├─ caching/
│  └─ ...（多场景专题目录）
├─ .flowpilot/                    # 工具配置（本地/自动化）
├─ .workflow/                     # 辅助流程配置
└─ （未显式看到 src/lib 等主业务源码目录）
```

---

## 关键入口点

1. **GitHub 工作流入口（主入口）**  
   `/.github/workflows/*.yml`  
   由 `push/pull_request/issue/workflow_dispatch` 等事件触发，负责全局调度。

2. **本地 Action 入口（二级执行入口）**  
   `/.github/actions/*/action.yml`  
   承接 workflow 参数并落地执行逻辑（脚本/容器/composite）。

3. **容器运行入口（运行时边界）**  
   `/docker/bots`、`/docker/call`  
   提供环境一致性与隔离能力，通常被 workflow 或命令调用。

4. **示例调用入口（开发者入口）**  
   `/examples/*`  
   提供场景化使用路径，帮助快速验证能力与接口行为。

---

## 模块关系摘要

- **关系主链**：`GitHub Event → workflows → actions → (docker) → 输出结果/发布物`
- **分层职责**：  
  - `workflows`：编排与门禁（控制平面）  
  - `actions`：执行封装（执行平面）  
  - `docker`：运行时隔离（运行平面）  
  - `examples`：能力消费与演示（消费平面）
- **外部边界**：  
  - GitHub 平台（Runner、Checks、Artifacts、Comments）  
  - 模型服务（Claude/Gemini API）  
  - 制品仓库（Python 包与容器镜像）
- **术语提示**：  
  - **控制平面**：只做触发与编排，不直接承载业务逻辑。  
  - **执行平面**：实际运行命令、脚本、Action 的层。  

---

## 建议优先阅读路径

1. **先看全局编排**：`/.github/workflows/`  
   重点读：`test-*.yml`、`release.yml`、`python-publish.yml`、`docker-publish.yml`、`claude*/gemini*`。  
   目标：建立“触发条件-职责-输出”的流程图。

2. **再看执行实现**：`/.github/actions/*/action.yml`  
   目标：确认 workflow 如何把输入传给执行层，识别权限与依赖点。

3. **再看运行时边界**：`/docker/bots`、`/docker/call`  
   目标：理解哪些任务在容器内执行、镜像如何参与流水线。

4. **最后看用户面**：`/examples/basic → cli → capabilities/checkpoints → benchmark`  
   目标：从最小可运行示例到复杂场景，反推对外能力模型。

> 结论边界：该阅读路径适用于“外围工程架构”理解；若要确认应用内核实现，需补充主源码目录与核心模块代码审阅。