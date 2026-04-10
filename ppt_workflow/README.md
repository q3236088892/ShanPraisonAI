# PPT 自动生成工作流

## 两种方案

| 方案 | 输出格式 | 特点 | Token 消耗 |
|---|---|---|---|
| **python-pptx** (`ppt_pipeline.yaml`) | `.pptx` 文件 | 原生 PPT，可用 Office 编辑 | ~3000-5000 |
| **HTML 演示** (`html_generator/pipeline.yaml`) | `.html` 文件 | 乔布斯风格，浏览器直接放映，自带动画 | ~2000-4000 |

---

## 方案一：python-pptx（生成 .pptx）

### 前置条件

```powershell
conda activate praisonai
pip install python-pptx
```

### 运行

```powershell
$env:PRAISONAI_MODEL = "custom_openai/gpt-4o-mini"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run `
  .\ppt_workflow\ppt_pipeline.yaml `
  -m $env:PRAISONAI_MODEL `
  --max-tokens 3000 `
  --var requirement="做一个关于AI Agent技术趋势的演讲PPT" `
  --var output_file="AI_Trends.pptx" `
  --var style="dark"
```

参数：`style` = `dark`（深色商务风）/ `light`（浅色简约风）

---

## 方案二：HTML 演示（乔布斯风格，推荐）

### 优势

- **零依赖**：不需要 python-pptx，纯 HTML/CSS/JS
- **更省 Token**：LLM 只写内容 HTML，不写代码
- **即时预览**：浏览器打开就能放映
- **自带交互**：键盘←→翻页、触屏滑动、进度条、页码
- **设计质量高**：预制乔布斯风格（深色背景、渐变文字、极简排版）

### 运行

```powershell
$env:PRAISONAI_MODEL = "custom_openai/gpt-4o-mini"

D:\conda\envs\praisonai\python.exe -m praisonai workflow run `
  .\ppt_workflow\html_generator\pipeline.yaml `
  -m $env:PRAISONAI_MODEL `
  --max-tokens 4000 `
  --var requirement="做一个关于AI Agent技术趋势的演讲" `
  --var output_file="presentation.html"
```

### 放映

直接用浏览器打开生成的 `.html` 文件：
- **→ / Space / Click右半屏**：下一页
- **← / Backspace / Click左半屏**：上一页
- **Home / End**：首页 / 末页
- 支持手机触屏滑动

### 幻灯片类型

| 类型 | 用途 | 效果 |
|---|---|---|
| `slide--title` | 封面页 | 大标题 + 渐变文字 + 径向背景 |
| `slide--content` | 内容页 | 标题 + 发光圆点要点列表 |
| `slide--two-col` | 对比页 | 双栏对比（before/after、pros/cons） |
| `slide--quote` | 金句页 | 大引号 + 居中引文 |
| `slide--end` | 结尾页 | 渐变大字 + 行动号召 |

---

## 文件结构

```
ppt_workflow/
├── README.md                       # 本文件
├── ppt_pipeline.yaml               # 方案一：python-pptx 工作流
├── tools.py                        # 方案一：本地工具
└── html_generator/                 # 方案二：HTML 演示
    ├── pipeline.yaml               # 工作流定义
    ├── tools.py                    # 本地工具（模板读取/文件写入/验证）
    ├── template.html               # 乔布斯风格 HTML 模板
    └── skill.md                    # Skill 描述文档
```

## 省 Token 核心设计

| 技巧 | 原理 |
|---|---|
| 预制 HTML 模板 | 所有 CSS/JS/动画已写好，LLM 只填内容 |
| 单 Agent 生成 | 只用 1 个 creator + 1 个 verifier，减少 system prompt 开销 |
| 本地验证工具 | 文件检查在本地执行，不消耗 token |
| 关闭 planning/reasoning | 每项额外消耗 500-2000 token |
| 限制 max_tokens | 防止模型输出冗余 |
