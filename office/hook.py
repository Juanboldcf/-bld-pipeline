#!/usr/bin/env python3
"""Hook de la Oficina BLD: anota qué agente trabaja en qué proyecto. LOCAL ONLY.

Lo invoca Claude Code (PreToolUse/PostToolUse/SubagentStart/SubagentStop) con el evento en stdin.
Escribe una línea JSON en Documents/Claude/BLD/<proyecto>/events.jsonl (o BLD/_events.jsonl si el
proyecto no se pudo deducir). Nunca bloquea ni falla: siempre sale con código 0. No toca Bold Brain.
"""
import json, pathlib, re, sys, time

BLD = pathlib.Path.home() / "Documents" / "Claude" / "BLD"
PENDING = BLD / ".office-pending.json"
FOLDER_RE = re.compile(r"/Documents/Claude/BLD/([A-Za-z0-9][A-Za-z0-9._-]*)")


def project_in(text):
    for m in FOLDER_RE.finditer(text or ""):
        name = m.group(1)
        while name:  # quita puntuación final pegada a la ruta ("...-debito.")
            if (BLD / name).is_dir():
                return name
            name = name.rstrip(".,;:)]'\"") if name[-1] in ".,;:)]'\"" else ""
    return ""


def load_pending():
    try:
        return json.loads(PENDING.read_text())
    except Exception:  # noqa: BLE001
        return {}


def save_pending(p):
    try:
        PENDING.write_text(json.dumps(p))
    except Exception:  # noqa: BLE001
        pass


def emit(project, rec):
    rec["ts"] = time.time()
    rec["project"] = project
    target = (BLD / project / "events.jsonl") if project else (BLD / "_events.jsonl")
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main():
    if not BLD.is_dir():
        return
    d = json.load(sys.stdin)
    if (pathlib.Path(__file__).parent / ".debug").exists():  # volcado temporal para diagnóstico
        with (pathlib.Path(__file__).parent / "hook-debug.jsonl").open("a") as f:
            f.write(json.dumps({k: (v if k != "tool_input" else {kk: str(vv)[:200] for kk, vv in (v or {}).items()}) for k, v in d.items() if k in ("hook_event_name", "tool_name", "tool_input", "agent_type", "agent_id", "cwd")}, ensure_ascii=False) + "\n")
    ev, tool, ti = d.get("hook_event_name"), d.get("tool_name", ""), d.get("tool_input") or {}
    if ev == "PreToolUse" and tool in ("Agent", "Task"):
        agent = ti.get("subagent_type") or ""
        project = project_in((ti.get("prompt") or "") + " " + (ti.get("description") or ""))
        if agent and project:
            p = load_pending()
            p[agent] = {"project": project, "note": (ti.get("description") or "")[:120], "ts": time.time()}
            save_pending(p)
    elif ev in ("SubagentStart", "SubagentStop"):
        agent = d.get("agent_type") or ""
        if not agent:
            return
        hint = {}
        for _ in range(6):  # los hooks son asíncronos: espera un momento a que el de PreToolUse deje la pista
            hint = load_pending().get(agent) or {}
            if hint and time.time() - hint.get("ts", 0) < 7200:
                break
            hint = {}
            time.sleep(0.15)
        emit(hint.get("project", ""), {"agent": agent, "event": "start" if ev == "SubagentStart" else "stop",
                                       "note": hint.get("note", "")})
    elif ev == "PostToolUse" and tool in ("Write", "Edit", "MultiEdit"):
        agent = d.get("agent_type") or ""
        fp = ti.get("file_path") or ""
        project = project_in(fp)
        if agent and project:
            emit(project, {"agent": agent, "event": "write", "note": pathlib.Path(fp).name})


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        pass
    sys.exit(0)
