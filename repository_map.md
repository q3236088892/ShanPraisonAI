# Repository Structure Overview

## Directory Map (functional view)

```text
.
├─ .github/
│  ├─ workflows/
│  │  ├─ test-*.yml                    # layered CI validation suites
│  │  ├─ benchmark.yml                 # performance pipeline
│  │  ├─ build-image.yml               # image build pipeline
│  │  ├─ python-package.yml            # package build
│  │  ├─ python-publish.yml            # Python publish
│  │  ├─ docker-publish.yml            # container publish
│  │  ├─ release.yml                   # release orchestration
│  │  ├─ claude*.yml / gemini*.yml     # provider-integrated automations
│  │  └─ auto-*.yml                    # repo automation workflows
│  └─ actions/
│     ├─ claude-code-action/
│     │  └─ action.yml
│     ├─ claude-issue-triage-action/
│     │  └─ action.yml
│     └─ gemini/
│        └─ action.yml
├─ docker/
│  ├─ bots/                            # bot-worker runtime image path
│  └─ call/                            # call/service runtime image path
├─ examples/
│  ├─ cli/                             # CLI usage
│  ├─ async_runs/                      # async execution patterns
│  ├─ background/                      # background/job patterns
│  ├─ benchmark/                       # performance usage demos
│  ├─ capabilities/                    # feature demos
│  ├─ checkpoints/                     # checkpoint/approval flows
│  └─ ...                              # additional scenario examples
├─ .flowpilot/
│  ├─ config.json                      # automation config
│  └─ update-cache.json                # cached metadata/state
└─ .workflow/                          # inferred workflow/tool metadata
```

---

## Key Entry Points

### 1) Primary Entry Points (repo runtime triggers)
- **`.github/workflows/*.yml`** are the top-level event handlers.
- Typical trigger domains:
  - **Validation:** `test-*`, `benchmark.yml`
  - **Build/Release:** `build-image.yml`, `python-package.yml`, `python-publish.yml`, `docker-publish.yml`, `release.yml`
  - **Automation:** `claude*`, `gemini*`, `auto-*`

### 2) Secondary Entry Points (reusable execution units)
- **`.github/actions/*/action.yml`** modules:
  - `claude-code-action`
  - `claude-issue-triage-action`
  - `gemini`
- These are called by workflows to encapsulate provider-specific or repeated logic.

### 3) Developer/Runtime Entry Points
- **`examples/*`**: user-facing execution starts for CLI, async/background, benchmark, capabilities, checkpoints.
- **`docker/bots`, `docker/call`**: containerized launch paths for reproducible runtime services.

---

## Module Relationship Summary

### Control-plane to execution-plane flow
1. GitHub event triggers a workflow (`.github/workflows`).
2. Workflow orchestrates CI/CD steps and invokes local reusable actions (`.github/actions`).
3. Outputs flow to status checks, comments/triage, artifacts, and publish targets.

### Core relationship graph (conceptual)
- **Workflows** → orchestrate **Custom Actions** + **Test/Build/Publish jobs**
- **Custom Actions** → integrate automation/provider logic (Claude/Gemini paths)
- **Docker modules** → define runtime packaging/deployment boundaries
- **Examples** → consume framework APIs and demonstrate runtime behavior patterns
- **Config metadata (`.flowpilot`, `.workflow`)** → influence automation determinism and tooling behavior

### Boundary model
- **Inside repo boundary:** workflows, custom actions, examples, Docker definitions, automation configs.
- **Outside repo boundary:** GitHub platform APIs/events, LLM providers, package indexes, container registries.

### Practical interpretation
This structure is optimized for:
- **Event-driven repository operations** (CI, release, issue/PR automation)
- **Modular automation reuse** (custom action layer)
- **Runtime demonstration and adoption** (examples)
- **Reproducible deployment paths** (container modules)

It also implies tight coupling between workflow governance and delivery quality, making CI policy, action hardening, and release consistency central to repository health.