---
name: bld-gate
description: >
  Audits a BLD pipeline run folder (/Users/juan.alvarez/Documents/Claude/BLD/<slug>/) with a
  deterministic script: which artifacts exist, whether each gate (brief → PR → PRD → HU) passes,
  and what blocks the next one. Writes nothing. Invoke explicitly: /bld-gate [slug] [gate].
argument-hint: "[initiative-slug] [to-pr|to-prd|to-comms|to-hu|hu-catalog|trace]"
disable-model-invocation: true
allowed-tools: Read, Glob, Bash(python3 *bld-gate/scripts/*)
---

# bld-gate

Thin wrapper over `bld_gate.py`, the only list of checks (`bld_gate.py --list` prints each one:
when it passes, when it fails, who fixes it). It is an audit: it writes nothing and gives no verdict
of its own. Subagents have no Bash by design, so the gates are run here, by the PM's session.

## Procedure

1. **Locate the run folder.** `/Users/juan.alvarez/Documents/Claude/BLD/<slug>/`. No slug → list the
   folders there and ask which one.
2. **No gate given → position.**
   ```bash
   python3 /Users/juan.alvarez/.claude/skills/bld-gate/scripts/bld_gate.py status <folder>
   ```
3. **A gate given → run it.** Gates are named for what they unlock:
   | Gate | Unlocks | Reads |
   |------|---------|-------|
   | `to-pr` | bld-pr-agent | `04-opportunity-brief.md` |
   | `to-prd` | bld-prd-agent | latest `05-pr_vN.md` |
   | `to-comms` | bld-stakeholder-comms-agent on a PRD | latest `06-prd_vN.md` + `06b-prd-review_vN.md` |
   | `to-hu` | bld-hu-agent | latest `06-prd_vN.md` + its review |
   | `hu-catalog` | PM review / ADO creation | `08-hu-catalog.md` against the PRD |
   ```bash
   python3 /Users/juan.alvarez/.claude/skills/bld-gate/scripts/bld_gate.py gate <folder> <gate>
   ```
4. **`trace` given** (with the path of an `eventstorm.yaml`) → lists the business rules the PRD/HU
   cite nowhere:
   ```bash
   python3 /Users/juan.alvarez/.claude/skills/bld-gate/scripts/bld_gate.py trace <folder> --eventstorm <path>
   ```
5. **Exit 2** → quote the error line and stop. **Exit 1** → report every `FAIL` line with its ids and
   who fixes it, in Spanish. **Exit 0** → PASS.

## Output format

```markdown
Estructura: PASS | FAIL (<n> checks, <m> problemas)
- <check>: <problema con ids> → lo corrige <quién>
Siguiente: <lo que desbloquea>
```

## CRITICAL REMINDERS

- NEVER edit a run-folder file to make a gate pass. Fixing happens with the agent that wrote it and
  the PM who decides.
- A PASS is structural only. Say so; never present it as a judgment on the content.
- A gate failing on `approvals`, `tracker` or `decisions` is never "fixed" by writing ✅ or an author
  yourself: those cells record what a person said.
- After editing `bld_gate.py` or the templates it parses, run `python3 scripts/selftest.py`.
