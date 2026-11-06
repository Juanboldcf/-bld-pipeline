# PRD — Custom limits
**Version:** v1

## 5. Functional Requirements
| ID | Requirement | Priority (MoSCoW) | Area owner |
|----|-------------|------------------|-----------|
| F1 | The client can set a monthly limit | Must | Mobile |
| F2 | The client can deactivate the limit and keep amount and period (inv-desactivar-conserva-monto-y-periodo) | Should | Backend |
| NF1 | Limit check answers in under 300 ms | Must | Backend |

## Decisions
| ID | Decision | Decided by | Why | Alternatives rejected |
|----|----------|-----------|-----|----------------------|
| D-1 | Mobile and Backend disagree on rounding: round down | Juan David Alvarez | "Never charge over the limit" | Round half up (rejected: could exceed the limit) |

## Open items
| ID | Item | Type | Blocks | Raised by | Status | Resolved by |
|----|------|------|--------|-----------|--------|-------------|
| OI-1 | Area heads disagree on rounding | conflict | frena | bld-prd-agent | resolved | D-1 (Juan David Alvarez) |
| OI-2 | SMS provider cost unknown | unknown | no frena | bld-prd-agent | open | |

## Area Approval Tracker

| Area | Owner | v1 | v2 | v3 | Final | Date | Notes |
|------|-------|----|----|----|----|------|-------|
| UX/UI | Owner UX | ✅ | | | ✅ | 2026-10-12 | |
| Legal | Owner Legal | ✅ | | | ✅ | 2026-10-12 | |
| Finance | Owner Finance | ✅ | | | ✅ | 2026-10-12 | |
| Core | Owner Core | ✅ | | | ✅ | 2026-10-12 | |
| FinOps | Owner FinOps | ✅ | | | ✅ | 2026-10-12 | |
| Backend | Owner Backend | ✅ | | | ✅ | 2026-10-12 | |
| Mobile | Owner Mobile | ✅ | | | ✅ | 2026-10-12 | |
| Web | Owner Web | ✅ | | | ✅ | 2026-10-12 | |
| Operations | Owner Operations | ✅ | | | ✅ | 2026-10-12 | |
| Platform | Owner Platform | ✅ | | | ✅ | 2026-10-12 | |
| Auth/ID | Owner Auth | ✅ | | | ✅ | 2026-10-12 | |
| Lifecycle | Owner Lifecycle | ✅ | | | ✅ | 2026-10-12 | |
| PM Juan David | Owner PM Juan David | ✅ | | | ✅ | 2026-10-12 | |
| C-level | Owner C-level | ✅ | | | ✅ | 2026-10-12 | |
