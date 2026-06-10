# BLD PM Agents Pipeline

> AI-powered product management pipeline for BLD — strategic planning, roadmap governance, KR tracking, and execution orchestration via Claude Code agents.

---

## Architecture Overview

```mermaid
graph TB
    subgraph DISCOVERY["🔭 Discovery Layer"]
        MT["bld-market-trends\nMarket Intelligence"]
        CX["bld-cx-insights\nCX & Survey Analysis"]
        IT["bld-idea-tank\nIdeation & Proposals"]
        DS["bld-discovery-synthesis\nOpportunity Brief → C-level Approval"]
    end

    subgraph DEFINITION["📋 Product Definition Layer"]
        PR["bld-pr-agent\nPress Release & FAQ"]
        PRD["bld-prd-agent\nPRD — Area Reviews & Approval"]
        HU["bld-hu-agent\nUser Stories → ADO"]
    end

    subgraph STRATEGIC["🧭 Strategic Layer"]
        KRC["bld-kr-compass\nQuarterly KR Guardian"]
        RG["bld-roadmap-guardian\nRoadmap & Backlog Governor"]
        DR["bld-dependency-radar\nWeekly Dependency Scanner"]
    end

    subgraph EXECUTION["⚙️ Execution Pipeline"]
        PMO["bld-pm-orchestrator\nSprint planning & delegation"]
        DEV["bld-dev-agent\nFeature implementation"]
        QA["bld-qa-agent\nValidation & testing"]
        DOC["bld-docs-agent\nDocumentation & changelogs"]
    end

    subgraph INTEGRATIONS["🔗 Integrations"]
        CU["ClickUp\nBacklog & sprints"]
        ADO["Azure DevOps\nCI/CD & work items"]
        SLIDES["Roadmap Slides\nC-level alignment"]
        LOVIFY["Lovify\nKR data feed (future)"]
    end

    MT -->|Market signals| DS
    CX -->|CX evidence| DS
    IT -->|Idea catalog| DS
    DS -->|Approved opportunity| PR
    PR -->|Approved PR| PRD
    PRD -->|Fully approved PRD| HU
    HU -->|HU set| PMO

    KRC -->|KR status every sprint| RG
    DR -->|Weekly dependency report| PMO
    RG -->|Priority & parallelization signals| PMO
    PMO -->|Tasks| DEV
    PMO -->|Tasks| QA
    PMO -->|Tasks| DOC

    RG <-->|Read backlog / Request permission to update| CU
    RG <-->|Request permission to update| ADO
    RG <-->|Request permission to update| SLIDES
    DR <-->|Read backlog weekly| CU
    HU -->|Create work items| ADO
    KRC <-->|Manual feed / future integration| LOVIFY

    style DISCOVERY fill:#2d1b4e,color:#fff,stroke:#9b59b6
    style DEFINITION fill:#1a3a4a,color:#fff,stroke:#3498db
    style STRATEGIC fill:#1e3a5f,color:#fff,stroke:#4a90d9
    style EXECUTION fill:#1a4a2e,color:#fff,stroke:#4caf50
    style INTEGRATIONS fill:#3a1e1e,color:#fff,stroke:#e57373
```

---

## Agent Descriptions

### 🔭 Discovery Layer

#### `bld-market-trends`
> Scans industry trends, competitor moves, and emerging opportunities.

#### `bld-cx-insights`
> Analyzes customer surveys, NPS, support tickets, and CX channel feedback.

#### `bld-idea-tank`
> Collects and evaluates internal proposals and ideation sessions.

#### `bld-discovery-synthesis`
> Weighs market + CX + ideas into a ranked Opportunity Brief. **C-level approval required** before moving to PR stage.

---

### 📋 Product Definition Layer

#### `bld-pr-agent`
> Amazon-style Press Release and FAQ. Customer-first narrative before any technical work begins. Requires C-level + PM approval to unlock PRD.

#### `bld-prd-agent`
> Full PRD with structured review cycles across all BLD areas: UX/UI, Legal, Finance, Core, FinOps, Backend, Mobile, Web, Operations, Platform, Auth/ID, Lifecycle. **All area heads + C-level must approve** before HU generation is unlocked.

#### `bld-hu-agent`
> Breaks the approved PRD into ADO-format User Stories (Como/Quiero/Para), grouped by epic and area. Hands HU set to bld-pm-orchestrator.

---

### 🧭 Strategic Layer

#### `bld-roadmap-guardian`
> Permanent strategic governor of the BLD product roadmap.

- Reads the BLD roadmap from ClickUp and roadmap slides
- Evaluates every feature for **strategic fit**, **priority**, and **parallelization opportunity**
- Monitors backlog health and flags drift
- **Requires explicit PM permission** before writing to ClickUp, Azure DevOps, or roadmap slides
- Receives KR status from `bld-kr-compass` every sprint and uses it as a primary prioritization factor

#### `bld-dependency-radar`
> Weekly watchdog for blocked tasks and cross-team dependencies.

- Scans the full ClickUp sprint backlog every Monday
- Detects blockers, stalled tasks (>5 days in progress), and unmet DOR
- Produces a structured Dependency Report for PM review
- Drafts stakeholder communication messages for PM to send
- Future: posts directly to a designated Slack channel

---

#### `bld-kr-compass`
> Quarterly KR north star — keeps the team and C-level aligned.

- Holds BLD's quarterly Key Results as the strategic truth
- Tracks KR progress sprint by sprint
- Detects drift early and raises alerts
- Generates next-quarter KR proposals
- KRs fed manually each quarter, or via Lovify when integration is available

---

## Agent Interaction Flow

```mermaid
sequenceDiagram
    participant PM as PM (Human)
    participant KRC as bld-kr-compass
    participant RG as bld-roadmap-guardian
    participant EX as Execution Agents
    participant CU as ClickUp / ADO

    Note over KRC,RG: Every Sprint
    KRC->>RG: KR progress report + drift alerts

    Note over RG,CU: Backlog Review
    RG->>CU: Read backlog & roadmap
    RG->>PM: Prioritization proposal + parallelization plan

    PM->>RG: Approve / modify priorities
    RG->>CU: Update backlog (with PM permission)

    Note over PM,EX: Sprint Execution
    PM->>EX: Delegate tasks
    EX->>PM: Progress updates

    Note over KRC: End of Quarter
    KRC->>PM: Next-quarter KR proposals
    PM->>KRC: Approve new KRs
```

---

## KR Progress Tracking

```mermaid
graph LR
    subgraph Q["Quarterly KR Cycle"]
        direction TB
        SET["KRs Set\n(Manual / Lovify)"]
        TRACK["Sprint-by-Sprint\nTracking"]
        DRIFT["Drift Detection\n& Alerts"]
        PROP["Next-Quarter\nProposals"]
    end

    SET --> TRACK --> DRIFT --> PROP --> SET

    style Q fill:#1e3a5f,color:#fff,stroke:#4a90d9
```

---

## Directory Structure

```
~/.claude/
├── agents/              # Agent definition files (.md)
│   │
│   ├── # Discovery Layer
│   ├── bld-market-trends.md
│   ├── bld-cx-insights.md
│   ├── bld-idea-tank.md
│   ├── bld-discovery-synthesis.md
│   │
│   ├── # Product Definition Layer
│   ├── bld-pr-agent.md
│   ├── bld-prd-agent.md
│   ├── bld-hu-agent.md
│   │
│   ├── # Strategic Layer
│   ├── bld-kr-compass.md
│   ├── bld-roadmap-guardian.md
│   ├── bld-dependency-radar.md
│   │
│   ├── # Execution Pipeline
│   ├── bld-pm-orchestrator.md
│   ├── bld-dev-agent.md
│   ├── bld-qa-agent.md
│   └── bld-docs-agent.md
├── agent-memory/        # Persistent memory across sessions
├── cost-logs/           # Token usage & cost tracking
├── scripts/             # Utility scripts
├── settings.json        # Claude Code configuration
├── .gitignore
└── README.md
```

---

## Permission Model

```mermaid
graph TD
    ACTION["Agent wants to write\nto external system"]
    CHECK{"Requires\nPM approval?"}
    READ["Read-only operations\n✅ Always allowed"]
    REQ["Request sent to PM"]
    APPROVE{"PM approves?"}
    EXEC["Execute action"]
    BLOCK["Action blocked\nLog reason"]

    ACTION --> CHECK
    CHECK -->|Write to ClickUp / ADO / Slides| REQ
    CHECK -->|Read from any source| READ
    REQ --> APPROVE
    APPROVE -->|Yes| EXEC
    APPROVE -->|No| BLOCK

    style EXEC fill:#1a4a2e,color:#fff,stroke:#4caf50
    style BLOCK fill:#3a1e1e,color:#fff,stroke:#e57373
    style READ fill:#1a4a2e,color:#fff,stroke:#4caf50
```

---

## Setup

```bash
# 1. Clone
git clone git@github.com:juandavidcowboy88/-bld-pipeline.git ~/.claude

# 2. Authenticate GitHub CLI
gh auth login

# 3. Agents are loaded automatically by Claude Code
# Place agent .md files in ~/.claude/agents/
```

---

## Integrations

| System | Access | Auth Method |
|---|---|---|
| ClickUp | Read + Write (PM-gated) | API Token |
| Azure DevOps | Read + Write (PM-gated) | PAT |
| Roadmap Slides | Read + Write (PM-gated) | Google Drive / SharePoint |
| Lovify | Read (future) | API (TBD) |
| GitHub | Read + Write | SSH Key |

---

## Roadmap

- [x] Discovery layer: `bld-market-trends`, `bld-cx-insights`, `bld-idea-tank`, `bld-discovery-synthesis`
- [x] Product definition layer: `bld-pr-agent`, `bld-prd-agent`, `bld-hu-agent`
- [x] Strategic layer: `bld-roadmap-guardian`, `bld-kr-compass`, `bld-dependency-radar`
- [x] Execution pipeline: `bld-pm-orchestrator`, `bld-dev-agent`, `bld-qa-agent`, `bld-docs-agent`
- [x] ClickUp task template (Context / Process / DOR / DOD / KR Alignment)
- [x] ADO user story template (Como/Quiero/Para + Reglas + DoR + Técnico + DoD)
- [x] Update audit trail (date, approver, meeting + Google Drive transcript link)
- [ ] ClickUp MCP integration
- [ ] Azure DevOps MCP integration
- [ ] Slack integration for dependency reports
- [ ] Cost tracking dashboard
- [ ] Lovify KR feed integration

---

*Maintained by Juan David Alvarez · BLD Product Team*
