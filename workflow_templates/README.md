# Workflow Templates

This folder contains reusable YAML workflow templates for PraisonAI.

## Templates

1. `codebase_analysis.yaml`
   - Use case: repository architecture/module/dependency/risk analysis
   - Auto output files:
     - `project_analysis.md`
     - `repository_map.md`

2. `bugfix_autofix.yaml`
   - Use case: bug triage -> fix -> verify -> report
   - Key variable:
     - `test_command` (default: `pytest -q`)
   - Auto output file:
     - `bugfix_report.md`

3. `doc_generation.yaml`
   - Use case: generate project documentation from repository context
   - Auto output file:
     - `project_documentation.md`

## How To Run

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

## Customization Checklist

1. Update `variables` first (paths, output file names, test command).
2. Keep each `agent` focused on one responsibility.
3. Use `parallel` only for independent subtasks.
4. Always end with a synthesizer/reviewer step for final output quality.
5. For third-party OpenAI-compatible gateways, make the final synthesizer call at least one tool before writing the final output.
