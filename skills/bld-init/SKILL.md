---
name: bld-init
description: >
  Starts a BLD initiative: creates its run folder under /Users/juan.alvarez/Documents/Claude/BLD/
  (named <ADO id>-<slug> when the feature has an id) with the standard subfolders, and registers it
  in Bold Brain project `bld-agentes`. Invoke explicitly: /bld-init <slug> [ado-id] ["title"].
argument-hint: "<slug> [ado-feature-id] [\"title\"]"
disable-model-invocation: true
allowed-tools: Read, Bash(python3 *bld-init/scripts/*), mcp__bold-brain__capture, mcp__bold-brain__summon
---

# bld-init

1. Run (id and title optional):
   ```bash
   python3 /Users/juan.alvarez/.claude/skills/bld-init/scripts/bld_init.py <slug> [--id <id>] [--title "<title>"]
   ```
   Exit 1 (`EXISTS`) → tell the PM the folder is already there and stop; never recreate it.
   Exit 2 → quote the error and ask for a valid slug / numeric id.
2. Check Bold Brain first: `summon` in project `bld-agentes` for the key prefix `bld/<folder>/`. If
   nothing exists, `capture` once in project `bld-agentes` (hint `bld/<folder>/init`) with the
   folder path, ADO id, title and date. One Brain project (`bld-agentes`) for all initiatives;
   each initiative is a key prefix, not a project.
3. Reply in Spanish, max 4 lines: folder path, Brain key prefix, and the next step
   (the first agent for this initiative, or "importar fuentes a `referencias/`").

Rules: never fill ADO id, ClickUp, PM or any approval yourself; those cells are for the PM.
