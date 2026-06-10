
---

## Strategic Layer Agents

Two agents run above the execution pipeline as permanent strategic guardians:

### bld-roadmap-guardian
Reads BLD roadmap from ClickUp and slides. Evaluates every feature for
strategic fit, priority and parallelization opportunity. Monitors backlog
health. Requests explicit PM permission before updating ClickUp, Azure
DevOps or roadmap slides.

### bld-kr-compass
Holds BLD's quarterly KRs as the strategic north star. Tracks KR progress
sprint by sprint. Detects drift. Generates next-quarter KR proposals.
Keeps PM and C-level aligned. KRs fed manually per quarter or via
Lovify when integration is available.

### How they connect
kr-compass feeds current KR status to roadmap-guardian every sprint.
roadmap-guardian uses KR alignment as a primary factor in feature
prioritization and parallelization decisions.
