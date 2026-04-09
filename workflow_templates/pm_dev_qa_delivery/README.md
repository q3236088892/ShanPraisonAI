# PM-DEV-QA Delivery Workflow (ZH)

## 用途

这是一个“需求驱动交付”模板，流程为：

1. `pm_agent`：拆解需求、给出技术方案与验收标准  
2. `dev_agent`：按方案实现代码并根据 QA 反馈修复  
3. `qa_agent`：执行真实测试（可含浏览器/E2E），输出 `APPROVED` 或 `NEEDS_REWORK`  
4. 循环多轮后由 `release_agent` 执行部署或阻断发布  
5. `report_agent` 生成最终交付报告

> 注意：当前模板采用“固定轮次循环（delivery_rounds）+ 早停语义（APPROVED_EARLY_EXIT）”策略。  
> 浏览器/E2E 测试通过内置 `execute_command` 执行（例如 `npx playwright test`）。

## 关键文件

- `pm_dev_qa_delivery_zh.yaml`：workflow 主模板  
- （无）本模板不依赖自定义 `tools.py`，仅使用项目内置 tools（如 `read_file`、`write_file`、`list_files`、`execute_command`）

## 关键变量

- `project_root`：项目根目录（可用绝对路径）  
- `requirement`：你的需求描述  
- `tech_stack`：技术栈要求  
- `deploy_target`：部署目标环境  
- `acceptance_criteria`：验收标准  
- `unit_test_command`：单元/集成测试命令（默认 `pytest -q`）  
- `browser_test_command`：浏览器/E2E 测试命令（可空）  
- `deploy_command`：部署命令（可空）  
- `delivery_rounds`：迭代轮次（默认 1~5）

## 运行示例（Windows + Conda）

```powershell
conda activate praisonai
chcp 65001 > $null
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8 = "1"

$env:OPENAI_API_KEY = "<YOUR_KEY>"
$env:CUSTOM_OPENAI_API_KEY = $env:OPENAI_API_KEY
$env:OPENAI_BASE_URL = "https://ice.v.ua/v1"
$env:OPENAI_API_BASE = "https://ice.v.ua/v1"
$env:PRAISONAI_MODEL = "custom_openai/gpt-5.3-codex"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run .\workflow_templates\pm_dev_qa_delivery\pm_dev_qa_delivery_zh.yaml `
  -m $env:PRAISONAI_MODEL --max-tokens 12000 -v `
  --var project_root="E:\your_project" `
  --var requirement="实现一个XX信息管理系统，包含用户管理、权限控制、审计日志、导入导出" `
  --var tech_stack="FastAPI + Vue3 + PostgreSQL + Redis" `
  --var deploy_target="Ubuntu 22.04 + Docker Compose" `
  --var acceptance_criteria="核心接口通过自动化测试；关键页面可用；具备基础权限校验与错误处理" `
  --var unit_test_command="pytest -q" `
  --var browser_test_command="npx playwright test" `
  --var deploy_command="docker compose up -d --build"
```

## 输出文件

- `项目实施计划.md`
- `项目交付总结.md`
