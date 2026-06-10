# BLD PM Agents Pipeline

> AI-powered product management pipeline for BLD — strategic planning, roadmap governance, KR tracking, and execution orchestration via Claude Code agents.

---

## Architecture Overview

```mermaid
graph TB
    subgraph STRATEGIC["🧭 Strategic Layer"]
        KRC["bld-kr-compass\nQuarterly KR Guardian"]
        RG["bld-roadmap-guardian\nRoadmap & Backlog Governor"]
    end

    subgraph EXECUTION["⚙️ Execution Pipeline"]
        PM["PM Orchestrator\nSprint planning & delegation"]
        DEV["Dev Agents\nFeature implementation"]
        QA["QA Agents\nValidation & testing"]
        DOC["Docs Agents\nDocumentation & changelogs"]
    end

    subgraph INTEGRATIONS["🔗 Integrations"]
        CU["ClickUp\nBacklog & sprints"]
        ADO["Azure DevOps\nCI/CD & work items"]
        SLIDES["Roadmap Slides\nC-level alignment"]
        LOVIFY["Lovify\nKR data feed (future)"]
    end

    KRC -->|KR status every sprint| RG
    RG -->|Priority & parallelization signals| PM
    PM -->|Tasks| DEV
    PM -->|Tasks| QA
    PM -->|Tasks| DOC

    RG <-->|Read backlog / Request permission to update| CU
    RG <-->|Request permission to update| ADO
    RG <-->|Request permission to update| SLIDES
    KRC <-->|Manual feed / future integration| LOVIFY

    style STRATEGIC fill:#1e3a5f,color:#fff,stroke:#4a90d9
    style EXECUTION fill:#1a4a2e,color:#fff,stroke:#4caf50
    style INTEGRATIONS fill:#3a1e1e,color:#fff,stroke:#e57373
```

---

## Agent Descriptions

### 🧭 Strategic Layer

#### `bld-roadmap-guardian`
> Permanent strategic governor of the BLD product roadmap.

- Reads the BLD roadmap from ClickUp and roadmap slides
- Evaluates every feature for **strategic fit**, **priority**, and **parallelization opportunity**
- Monitors backlog health and flags drift
- **Requires explicit PM permission** before writing to ClickUp, Azure DevOps, or roadmap slides
- Receives KR status from `bld-kr-compass` every sprint and uses it as a primary prioritization factor

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
│   ├── bld-roadmap-guardian.md
│   └── bld-kr-compass.md
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

- [x] Strategic layer: `bld-roadmap-guardian` + `bld-kr-compass`
- [ ] Execution pipeline agents
- [ ] ClickUp MCP integration
- [ ] Azure DevOps MCP integration
- [ ] Cost tracking dashboard
- [ ] Lovify KR feed integration

---

*Maintained by Juan David Alvarez · BLD Product Team*
