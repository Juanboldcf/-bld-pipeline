# bld-stakeholder-comms-agent — Agent Memory
# Best practices:
#   - Keep total size under ~3000 tokens (~12KB)
#   - Date-stamp every entry: [YYYY-MM-DD]
#   - Use sections: FACTS | DECISIONS | LEARNINGS | ACTIVE_CONTEXT
#   - Clean entries older than 90 days (run: python3 memory-manager.py clean)

## FACTS
# Permanent truths about this agent's domain. Update in place, don't append.
# Example: [2026-06-10] ClickUp workspace ID = XXXXX

## DECISIONS
# Key decisions made that affect this agent's behavior. Date-stamped, never delete.
# Example: [2026-06-10] Audit trail required on all ClickUp comments — PM approval needed

## LEARNINGS
# Patterns, mistakes, and insights discovered during operation. Prune after 90 days.
# Example: [2026-06-10] Stakeholder X prefers Slack DM over email for feedback requests

## ACTIVE_CONTEXT
# Current sprint/quarter state. Overwrite each sprint — do NOT accumulate.
# Max 10 lines. Everything here is assumed current.
# Example: Current quarter: Q3-2026 | Sprint: Sprint 12 | KR focus: Revenue +20%
