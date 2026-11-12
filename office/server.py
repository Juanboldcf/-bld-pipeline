#!/usr/bin/env python3
"""Oficina BLD — dashboard local de los agentes BLD. Python 3 stdlib only.

  python3 ~/.claude/office/server.py [--port 8765] [--root <carpeta BLD>]

LOCAL ONLY: no escribe en Bold Brain ni en ningún servicio externo; escucha solo en 127.0.0.1.
Vistas: / (profesional) y /pixel (16 bits). Ambas usan core.js + core.css (misma lógica).

Lee: ~/.claude/agents/*.md, Documents/Claude/BLD/<proyecto>/ (entregables, open items, events.jsonl).
Escribe: solo si el PM lo pide en la interfaz: abrir una carpeta (`open`) o crear un proyecto nuevo (bld_init.py). El chat lanza `claude -p` en MODO SOLO LECTURA
(herramientas Read/Glob/Grep, sin MCP, sin persistir sesión).
"""
import argparse, datetime, json, math, os, pathlib, re, secrets, shutil, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HOME = pathlib.Path.home()
AGENTS_DIR = HOME / ".claude" / "agents"
BLD_ROOT = HOME / "Documents" / "Claude" / "BLD"
GATE = HOME / ".claude" / "skills" / "bld-gate" / "scripts" / "bld_gate.py"
INIT = HOME / ".claude" / "skills" / "bld-init" / "scripts" / "bld_init.py"
HERE = pathlib.Path(__file__).parent
TOKEN = secrets.token_urlsafe(24)
PORT = 8765
CLAUDE = shutil.which("claude") or str(HOME / ".local" / "bin" / "claude")
CHAT_MODEL = "sonnet"
CHAT_SLOTS = threading.Semaphore(2)
NEW_LOCK = threading.Lock()
RUN_SLOT = threading.Semaphore(1)  # una ejecución a la vez
RUNS = {}  # id -> estado de cada ejecución (en memoria)
RUN_MODEL = "sonnet"
LIVE = {"until": 0.0}  # LIVE: mientras esté encendido, los agentes lanzados con «Ejecutar» pueden buscar en internet
LIVE_MAX_MIN = 120
SEC_DIR = HERE / ".security"
RUN_TIMEOUT = 900

FRONT = ["bld-pm-orchestrator", "bld-discovery-synthesis", "bld-pr-agent", "bld-prd-agent",
         "bld-hu-agent", "bld-ux-ui-agent", "bld-stakeholder-comms-agent"]
ROOMS = [
    {"id": "discovery", "name": "Sala Discovery", "agents": ["bld-market-trends", "bld-cx-insights", "bld-idea-tank"]},
    {"id": "estrategia", "name": "Sala Estrategia", "agents": ["bld-roadmap-guardian", "bld-kr-compass", "bld-dependency-radar"]},
    {"id": "revision", "name": "Sala Revisión", "agents": ["bld-prd-reviewer", "bld-hu-reviewer"]},
    {"id": "taller", "name": "Taller Dev", "agents": ["bld-dev-agent", "bld-qa-agent", "bld-docs-agent"]},
    {"id": "estudio", "name": "Estudio de Diseño", "agents": ["ux-ui-prototipos-issuing-bold", "qa-prototipo-ux-regresion"]},
    {"id": "storm-research", "name": "Sala STORM · Investigación", "agents": ["storm-researcher", "storm-expert", "storm-writer"]},
    {"id": "event-storming", "name": "Taller Event Storming", "agents": ["storm-start", "storm-big-picture", "storm-process", "storm-design", "storm-verify", "storm-render"]},
    {"id": "pm-toolkit", "name": "Sala PM Toolkit", "agents": ["pm-discovery-lead", "pm-data-analyst", "pm-gtm-strategist", "pm-comms-writer", "pm-ops-facilitator"]},
    {"id": "utilidades", "name": "Utilidades", "agents": ["generador-pr-faq", "prep-campanas-marketing-prod", "reporte-mastercard-sofia"]},
]
# agente -> (rol legible, jefe). Jefe None = responde directamente al PM.
META = {
    "bld-pm-orchestrator": ("Orquestador del sprint", None),
    "bld-discovery-synthesis": ("Síntesis de discovery", "bld-pm-orchestrator"),
    "bld-pr-agent": ("Press Release y FAQ", "bld-pm-orchestrator"),
    "bld-prd-agent": ("Requisitos (PRD)", "bld-pm-orchestrator"),
    "bld-hu-agent": ("Historias de usuario", "bld-pm-orchestrator"),
    "bld-ux-ui-agent": ("Diseño UX/UI", "bld-pm-orchestrator"),
    "bld-stakeholder-comms-agent": ("Comunicación con áreas", "bld-pm-orchestrator"),
    "bld-market-trends": ("Tendencias de mercado", "bld-discovery-synthesis"),
    "bld-cx-insights": ("Voz del cliente", "bld-discovery-synthesis"),
    "bld-idea-tank": ("Ideas y propuestas", "bld-discovery-synthesis"),
    "bld-roadmap-guardian": ("Guardián del roadmap", "bld-pm-orchestrator"),
    "bld-kr-compass": ("Brújula de KRs", "bld-roadmap-guardian"),
    "bld-dependency-radar": ("Radar de dependencias", "bld-pm-orchestrator"),
    "bld-prd-reviewer": ("Revisor de PRD", "bld-prd-agent"),
    "bld-hu-reviewer": ("Revisor de HU", "bld-hu-agent"),
    "bld-dev-agent": ("Desarrollo", "bld-pm-orchestrator"),
    "bld-qa-agent": ("QA", "bld-pm-orchestrator"),
    "bld-docs-agent": ("Documentación", "bld-pm-orchestrator"),
    "ux-ui-prototipos-issuing-bold": ("Prototipos Issuing", "bld-ux-ui-agent"),
    "qa-prototipo-ux-regresion": ("QA de prototipos", "bld-ux-ui-agent"),
    "generador-pr-faq": ("PR/FAQ genérico", None),
    "prep-campanas-marketing-prod": ("Campañas y ROI", None),
    "reporte-mastercard-sofia": ("Reporte Mastercard", None),
    "pm-discovery-lead": ("Discovery de producto", None),
    "pm-data-analyst": ("Análisis de datos y métricas", None),
    "pm-gtm-strategist": ("Go-to-market y ventas", None),
    "pm-comms-writer": ("Comunicación ejecutiva", None),
    "pm-ops-facilitator": ("Rituales y operación", None),
    "storm-researcher": ("Investigación multi-perspectiva", None),
    "storm-expert": ("Responde con fuentes verificadas", None),
    "storm-writer": ("Redacta secciones con citas", None),
    "storm-start": ("Facilitador de Event Storming", None),
    "storm-big-picture": ("Event Storming · Big Picture", "storm-start"),
    "storm-process": ("Event Storming · Proceso", "storm-start"),
    "storm-design": ("Event Storming · Diseño", "storm-start"),
    "storm-verify": ("Verifica el modelo", "storm-start"),
    "storm-render": ("Genera eventstorm.html", "storm-start"),
}
PERSONA = {  # rasgo + frase característica (se muestra en la vista pixel)
    "bld-pm-orchestrator": ("Calmada y organizada", "Un sprint a la vez."),
    "bld-discovery-synthesis": ("Curiosa y analítica", "Conecto los puntos."),
    "bld-pr-agent": ("Narradora con gancho", "Si no cabe en un titular, no está claro."),
    "bld-prd-agent": ("Meticuloso", "El detalle es el producto."),
    "bld-hu-agent": ("Enérgico", "Cada historia, una prueba."),
    "bld-ux-ui-agent": ("Sensible y estética", "Primero la persona, luego el píxel."),
    "bld-stakeholder-comms-agent": ("Diplomático", "¿Ya lo hablaste con el área?"),
    "bld-market-trends": ("Visionario", "Lo que viene ya pasó en otro mercado."),
    "bld-cx-insights": ("Empática", "El cliente ya lo dijo."),
    "bld-idea-tank": ("Chispa creativa", "¿Y si probamos…?"),
    "bld-roadmap-guardian": ("Estratega serio", "¿Esto mueve un KR?"),
    "bld-kr-compass": ("Enfocada", "Medir para no desviarnos."),
    "bld-dependency-radar": ("Vigilante", "Hay un bloqueo en el horizonte."),
    "bld-prd-reviewer": ("Escéptico justo", "Muéstrame la evidencia."),
    "bld-hu-reviewer": ("Riguroso", "¿Esto se puede probar?"),
    "bld-dev-agent": ("Práctico", "Compila primero, conversamos después."),
    "bld-qa-agent": ("Cazadora de bugs", "Lo rompo para que no se rompa."),
    "bld-docs-agent": ("Ordenada", "Si no está escrito, no existió."),
    "ux-ui-prototipos-issuing-bold": ("Perfeccionista creativa", "Un píxel a la vez."),
    "qa-prototipo-ux-regresion": ("Ojo de águila", "Esto antes funcionaba…"),
    "generador-pr-faq": ("Narrador", "Trabajo hacia atrás desde el cliente."),
    "prep-campanas-marketing-prod": ("Comercial", "Cada peso con retorno."),
    "reporte-mastercard-sofia": ("Puntual", "Llegó correo. Resumen listo."),
    "pm-discovery-lead": ("Exploradora", "Primero entender el problema."),
    "pm-data-analyst": ("Cuantitativo", "Los números no mienten."),
    "pm-gtm-strategist": ("Lanzadora", "¿Cómo se lo cuenta ventas?"),
    "pm-comms-writer": ("Clara y directa", "Una idea por párrafo."),
    "pm-ops-facilitator": ("Ritmo de equipo", "Retro corta, acciones claras."),
    "storm-researcher": ("Investigador incansable", "Una fuente más."),
    "storm-expert": ("Rigor de citas", "Sin fuente no hay respuesta."),
    "storm-writer": ("Pluma precisa", "Solo escribo lo que está respaldado."),
    "storm-start": ("Facilitadora", "Empecemos por los eventos."),
    "storm-big-picture": ("Visión de conjunto", "Primero el mapa completo."),
    "storm-process": ("Detallista de procesos", "¿Y qué pasa después?"),
    "storm-design": ("Arquitecto", "Cada comando tiene dueño."),
    "storm-verify": ("Verificador", "Cierro los cabos sueltos."),
    "storm-render": ("Visual", "Que el modelo se vea."),
}
INVOKE = {"storm-researcher": "/storm:research <tema>  (lo lanza el director; no se invoca directo)",
          "storm-writer": "/storm:research <tema>  (lo lanza el director; no se invoca directo)",
          "storm-expert": "/storm:discuss <tema>  (lo lanza el director; no se invoca directo)"}
EMOJI = {"bld-pm-orchestrator": "🧭", "bld-discovery-synthesis": "🔭", "bld-pr-agent": "📰", "bld-prd-agent": "📋",
         "bld-hu-agent": "🧩", "bld-ux-ui-agent": "🎨", "bld-stakeholder-comms-agent": "💬", "bld-market-trends": "📈",
         "bld-cx-insights": "🎧", "bld-idea-tank": "💡", "bld-roadmap-guardian": "🗺️", "bld-kr-compass": "🎯",
         "bld-dependency-radar": "🔗", "bld-prd-reviewer": "🔍", "bld-hu-reviewer": "🔎", "bld-dev-agent": "💻",
         "bld-qa-agent": "🧪", "bld-docs-agent": "📚", "ux-ui-prototipos-issuing-bold": "🖌️",
         "qa-prototipo-ux-regresion": "🧐", "generador-pr-faq": "✍️", "prep-campanas-marketing-prod": "📣",
         "reporte-mastercard-sofia": "💳", "storm-researcher": "🌐", "storm-expert": "🎓", "storm-writer": "✒️",
         "storm-start": "🗒️", "storm-big-picture": "🗺️", "storm-process": "⚙️", "storm-design": "🧱",
         "storm-verify": "✅", "storm-render": "🖼️", "pm-discovery-lead": "🧭", "pm-data-analyst": "📊",
         "pm-gtm-strategist": "📢", "pm-comms-writer": "📝", "pm-ops-facilitator": "🛠️"}
FILE_AGENT = [(r"01-market.*\.md", "bld-market-trends"), (r"02-cx.*\.md", "bld-cx-insights"),
              (r"03-ideas.*\.md", "bld-idea-tank"), (r"04-opportunity-brief.*\.md", "bld-discovery-synthesis"),
              (r"05-pr_v\d+\.md", "bld-pr-agent"), (r"06-prd_v\d+\.md", "bld-prd-agent"),
              (r"06b-prd-review_v\d+\.md", "bld-prd-reviewer"), (r"07-feedback_v\d+\.md", "bld-stakeholder-comms-agent"),
              (r"08-hu-catalog.*\.md", "bld-hu-agent"), (r"09-hu-review.*\.md", "bld-hu-reviewer"),
              (r"storm/eventstorm\.yaml", "storm-start"), (r"storm/eventstorm\.html", "storm-render")]
STAGES = [("Brief", r"04-opportunity-brief.*\.md"), ("PR", r"05-pr_v\d+\.md"), ("PRD", r"06-prd_v\d+\.md"),
          ("Revisión PRD", r"06b-prd-review_v\d+\.md"), ("Comms", r"07-feedback_v\d+\.md"),
          ("HU", r"08-hu-catalog.*\.md"), ("Revisión HU", r"09-hu-review.*\.md")]
TYPES = {"FEA": "Feature", "DIS": "Diseño", "INV": "Investigación", "MET": "Seguimiento de métricas", "CAM": "Campaña", "OTR": "Otro"}
# hitos por tipo: (nombre, patrón de archivo en la raíz | "dir:<subcarpeta>" = la subcarpeta tiene archivos)
STAGE_SETS = {
    "FEA": STAGES,
    "INV": [("Mercado", r"01-market.*\.md"), ("Voz del cliente", r"02-cx.*\.md"), ("Ideas", r"03-ideas.*\.md"), ("Brief", r"04-opportunity-brief.*\.md")],
    "DIS": [("Definición", "dir:definiciones"), ("Diseños", "dir:disenos"), ("Iteraciones", "dir:iteraciones"), ("Revisión", r"09-hu-review.*\.md|.*-review.*\.md")],
    "MET": [("Definición", "dir:definiciones"), ("Datos", "dir:referencias"), ("Análisis", r".*(analisis|análisis|evidencia).*\.md"), ("Reporte", r".*(reporte|report|seguimiento).*\.md")],
    "CAM": [("Definición", "dir:definiciones"), ("Insumos", "dir:referencias"), ("Modelo ROI", r".*(roi|costos).*\.(md|xlsx)"), ("Lanzamiento", r".*(lanzamiento|launch).*\.md")],
    "OTR": [("Definición", "dir:definiciones"), ("Insumos", "dir:referencias"), ("Entregable", r"\d\d-.*\.md")],
}
PROJECT_ID_RE = re.compile(r"^(?:([A-Z]{3})-(\d+)|(\d+))-")
RECENT_S, WORKING_S, DONE_S = 15 * 60, 45 * 60, 24 * 3600
PRIORITY = ["working", "question", "done", "recent", "delivered", "idle"]


def parse_agent(path):
    txt = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"---\n(.*?)\n---\n?(.*)", txt, re.S)
    meta, body = {}, txt
    if m:
        body = m.group(2)
        lines, i = m.group(1).splitlines(), 0
        while i < len(lines):
            line = lines[i]
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if v in (">", "|", ">-", "|-") and not line.startswith(" "):
                block = []
                while i + 1 < len(lines) and (lines[i + 1].startswith(" ") or not lines[i + 1].strip()):
                    i += 1
                    block.append(lines[i].strip())
                v = " ".join(b for b in block if b)
            if k in ("name", "description", "model", "tools", "allowed-tools") and not line.startswith(" "):
                meta["tools" if k == "allowed-tools" else k] = v
            i += 1
    name = meta.get("name", path.stem)
    role, boss = META.get(name, ("Agente", None))
    return {"name": name, "description": meta.get("description", "").strip('"'), "model": meta.get("model", ""),
            "tools": [t.strip() for t in meta.get("tools", "").split(",") if t.strip()],
            "emoji": EMOJI.get(name, "🤖"), "role": role, "boss": boss, "kind": "agent", "invoke_cmd": "", "invoke_name": name, "_body": body}


PLUGINS = ("storm", "pm-toolkit")


def storm_sources():
    """Agentes de plugins (STORM, pm-toolkit) y skills storm-* (Event Storming), fuera de ~/.claude/agents."""
    found = []
    for manifest in (HOME / ".claude" / "plugins" / "synced").glob("*/*/.claude-plugin/plugin.json"):
        try:
            plugin = json.loads(manifest.read_text()).get("name")
        except (ValueError, OSError):
            continue
        if plugin in PLUGINS:
            found += [(p, "plugin:" + plugin) for p in sorted((manifest.parent.parent / "agents").glob("*.md"))]
    found += [(p, "skill") for p in sorted((HOME / ".claude" / "skills").glob("storm-*/SKILL.md"))]
    return found


def load_agents():
    out = {}
    for p in sorted(AGENTS_DIR.glob("*.md")):
        if p.name.startswith("CONEXIONES"):
            continue
        a = parse_agent(p)
        out[a["name"]] = a
    for p, kind in storm_sources():
        a = parse_agent(p)
        a["kind"] = "skill" if kind == "skill" else "plugin"
        if kind.startswith("plugin:"):
            a["invoke_name"] = f"{kind[7:]}:{a['name']}"
        a["invoke_cmd"] = INVOKE.get(a["name"], f"/{a['name']} <slug-del-dominio>" if kind == "skill" else "")
        out[a["name"]] = a
    return out


def public(a):
    out = {k: v for k, v in a.items() if not k.startswith("_")}
    out["trait"], out["quote"] = PERSONA.get(a["name"], ("", ""))
    return out


def open_items(folder):
    items = []
    for p in sorted(folder.glob("*.md")):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        header = None
        for line in text.splitlines():
            if not line.startswith("|"):
                header = None
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells[:4] == ["ID", "Item", "Type", "Blocks"]:
                header = cells
                continue
            if header and len(cells) >= len(header) and not set(line) <= set("|-: "):
                row = dict(zip(header, cells))
                if row.get("Status", "").lower() == "open":
                    items.append({"id": row.get("ID"), "item": row.get("Item"), "type": row.get("Type"),
                                  "blocks": row.get("Blocks"), "raised_by": row.get("Raised by"), "file": p.name})
    return items


TRANSCRIPTS = HOME / ".claude" / "projects"
FOLDER_RE = re.compile(r"/Documents/Claude/BLD/([A-Za-z0-9][A-Za-z0-9._-]*)")


ACTIVITY = {"Read": "leyendo", "Glob": "buscando archivos", "Grep": "buscando en archivos", "Write": "escribiendo", "Edit": "editando", "MultiEdit": "editando",
            "NotebookEdit": "editando", "Bash": "ejecutando comandos", "WebSearch": "investigando en la web", "WebFetch": "leyendo una página web",
            "Agent": "delegando", "Task": "delegando", "TodoWrite": "planificando", "SubagentHandback": "entregando el resultado"}


def last_activity(log):
    """Qué está haciendo un sub-agente ahora: nombre de la última herramienta en la cola de su transcripción (solo lectura).
    Idea tomada de Pixel Agents (MIT): los personajes teclean, leen o esperan según la herramienta en uso."""
    try:
        with log.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 65536))
            tail = fh.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    for line in reversed(tail):
        try:
            content = json.loads(line).get("message", {}).get("content", [])
        except (ValueError, AttributeError):
            continue
        for c in reversed(content if isinstance(content, list) else []):
            if isinstance(c, dict) and c.get("type") == "tool_use":
                name = str(c.get("name", ""))
                if name.startswith("mcp__"):
                    return "consultando " + name.split("__")[1].replace("claude_ai_", "").replace("_", " ")
                return ACTIVITY.get(name, "trabajando")
    return ""


def transcript_events(names, known):
    """Estado en vivo sin hooks: lee los sub-agentes que Claude Code guarda en <proyecto>/<sesión>/subagents/agent-*.meta.json
    (tipo, 'finished', prompt con la carpeta BLD). Idea tomada de Pixel Agents (MIT), que también lee las transcripciones. Solo lectura."""
    evs, now = [], time.time()
    try:
        metas = list(TRANSCRIPTS.glob("*/*/subagents/agent-*.meta.json"))
    except OSError:
        return evs
    for meta in metas:
        try:
            log = meta.with_suffix("").with_suffix(".jsonl")
            mt = log.stat().st_mtime
            if now - mt > DONE_S:
                continue
            m = json.loads(meta.read_text())
            agent = str(m.get("agentType", "")).split(":")[-1]
            if agent not in known:
                continue
            with log.open(encoding="utf-8", errors="replace") as fh:
                first = json.loads(fh.readline())
            text = json.dumps(first.get("message", {}).get("content", ""))
            proj = next((g for g in (x.group(1).rstrip(".,;:)]'\"\\") for x in FOLDER_RE.finditer(text)) if g in names), "")
            if not proj:
                continue
            t0 = datetime.datetime.fromisoformat(first["timestamp"].replace("Z", "+00:00")).timestamp()
            note = str(m.get("description", ""))[:120]
            act = "" if m.get("finished") or now - mt > 90 else last_activity(log)
            evs.append({"agent": agent, "event": "start", "note": note + (" · " + act if act else ""), "ts": t0, "project": proj})
            if m.get("finished") or now - mt > 90:  # sin escribir en 90 s ≈ terminó o quedó esperando
                evs.append({"agent": agent, "event": "stop", "note": note, "ts": max(mt, t0 + 1), "project": proj})
        except (OSError, ValueError, KeyError, AttributeError, TypeError):
            continue
    return evs


def read_events(names, agents=()):
    evs = []
    sources = [(BLD_ROOT / n / "events.jsonl", n) for n in names] + [(BLD_ROOT / "_events.jsonl", "")]
    for path, proj in sources:
        try:
            if not path.is_file():
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:  # incluye PermissionError
            continue
        for line in lines:
            try:
                e = json.loads(line)
                e["agent"] = str(e["agent"]).split(":")[-1]
                e["ts"] = float(e["ts"])
                if not isinstance(e["event"], str) or not math.isfinite(e["ts"]):
                    continue
            except (ValueError, KeyError, TypeError):
                continue
            e["project"] = e.get("project") or proj
            evs.append(e)
    evs += transcript_events(set(names), set(agents))
    evs.sort(key=lambda e: e["ts"])
    return evs


def project_type(name):
    """Tipo e ID visible: FEA-001-… → FEA/FEA-001; 170290-… (ADO) → FEA/170290; sin prefijo → OTR."""
    m = PROJECT_ID_RE.match(name)
    if not m:
        return "OTR", ""
    return (m.group(1), f"{m.group(1)}-{m.group(2)}") if m.group(1) else ("FEA", m.group(3))


def stage_status(folder, typ):
    """Hitos del proyecto según su tipo, con el archivo y la fecha que lo cumplió."""
    files = {p.name: p for p in folder.iterdir() if p.is_file()}
    out = []
    for n, pat in STAGE_SETS.get(typ, STAGES):
        if pat.startswith("dir:"):
            d = folder / pat[4:]
            hits = [p for p in d.iterdir() if p.is_file()] if d.is_dir() else []
        else:
            hits = [p for f, p in files.items() if re.fullmatch(pat, f)]
        newest = max(hits, key=lambda p: p.stat().st_mtime) if hits else None
        out.append({"name": n, "done": bool(hits), "file": newest.relative_to(folder).as_posix() if newest else "",
                    "at": newest.stat().st_mtime if newest else 0})
    return out


def project_summary(name):
    folder = BLD_ROOT / name
    files = [p.name for p in folder.iterdir() if p.is_file()]
    oi = open_items(folder)
    typ, pid = project_type(name)
    stages = stage_status(folder, typ)
    done = sum(1 for s in stages if s["done"])
    mt = max([(folder / f).stat().st_mtime for f in files] or [0])
    return {"name": name, "type": typ, "type_name": TYPES[typ], "pid": pid, "title": name[len(pid) + 1:] if pid and name.startswith(pid + "-") else name,
            "stages_done": done, "stages_total": len(stages), "open_items": len(oi),
            "frena": sum(1 for i in oi if i["blocks"].replace(" ", "") == "frena"), "last_activity": mt,
            "files": sorted(files), "open_list": oi[:6]}


def agent_project_states(name, agents, events):
    """Estado de cada agente en cada proyecto, a partir de archivos y de events.jsonl."""
    folder = BLD_ROOT / name
    now = time.time()
    files = {p.name: p for p in folder.iterdir() if p.is_file()}
    if (folder / "storm").is_dir():
        files.update({"storm/" + p.name: p for p in (folder / "storm").iterdir() if p.is_file()})
    deliveries = {}
    for fname, p in files.items():
        for pat, agent in FILE_AGENT:
            if re.fullmatch(pat, fname):
                d = deliveries.setdefault(agent, {"files": [], "mtime": 0})
                d["files"].append(fname)
                d["mtime"] = max(d["mtime"], p.stat().st_mtime)
    by_agent = {}
    for it in open_items(folder):
        for pat, agent in FILE_AGENT:
            if re.fullmatch(pat, it["file"]):
                by_agent.setdefault(agent, []).append(it)
    last = {}
    for e in events:
        if e["project"] == name:
            slot = last.setdefault(e["agent"], {})
            slot[e["event"]] = e
    states = {}
    for a in agents:
        d, ev = deliveries.get(a), last.get(a, {})
        st, note, done_at = "idle", "Sin actividad en este proyecto", 0
        if d:
            st, note = "delivered", "Entregó " + ", ".join(sorted(d["files"])[-2:])
            if now - d["mtime"] < RECENT_S and not ev:
                st, note = "recent", "Actividad reciente: " + sorted(d["files"])[-1]
        start, stop, write = ev.get("start"), ev.get("stop"), ev.get("write")
        if start and (not stop or start["ts"] > stop["ts"]) and now - start["ts"] < WORKING_S:
            st, note = "working", start.get("note") or "Trabajando"
            if write and write["ts"] >= start["ts"]:
                note = f"Escribiendo {write.get('note', '')}"
        elif stop and now - stop["ts"] < DONE_S:
            st, note, done_at = "done", "Terminó: " + (stop.get("note") or "tarea lista"), stop["ts"]
        elif ev.get("question") and now - ev["question"]["ts"] < DONE_S:
            st, note = "question", ev["question"].get("note") or "Tiene una pregunta"
        items = by_agent.get(a, [])
        if items and st not in ("working",):
            if any(i["blocks"].replace(" ", "") == "frena" for i in items):
                st = "question"
        if st != "idle" or items:
            states[a] = {"project": name, "state": st, "note": note, "done_at": done_at,
                         "open_items": len(items), "files": sorted(d["files"]) if d else [],
                         "updated": max([x["ts"] for x in ev.values()] + [d["mtime"] if d else 0])}
    return states


def focus_state(name, agents):
    folder = BLD_ROOT / name
    files = {p.name for p in folder.iterdir() if p.is_file()}
    typ, pid = project_type(name)
    stages = stage_status(folder, typ)
    try:
        gate = subprocess.run([sys.executable, str(GATE), "status", str(folder)], capture_output=True,
                              text=True, timeout=15).stdout.strip()
    except Exception as exc:  # noqa: BLE001
        gate = f"(no se pudo leer el estado de los gates: {exc})"
    return {"name": name, "type": typ, "type_name": TYPES[typ], "pid": pid, "path": str(folder), "stages": stages, "open_items": open_items(folder), "gate": gate,
            "subdirs": {p.name: len(list(p.iterdir())) for p in folder.iterdir() if p.is_dir()},
            "root_files": sorted(files)}


def safe_projects():
    """Carpetas de proyecto reales: sin ocultas, sin '_' y sin enlaces que salgan de BLD_ROOT."""
    root = BLD_ROOT.resolve()
    try:
        entries = list(BLD_ROOT.iterdir())
    except OSError:
        return []
    out = []
    for p in entries:
        try:
            if p.is_dir() and not p.name.startswith((".", "_")) and (p.resolve() == root / p.name) and os.access(p, os.R_OK | os.X_OK):
                out.append(p)
        except OSError:
            continue
    return out


def office(initiative):
    agents = load_agents()
    names = sorted(p.name for p in safe_projects()) if BLD_ROOT.exists() else []
    events = read_events(names, agents)
    summaries = []
    for n in names:
        try:
            summaries.append(project_summary(n))
        except Exception:  # un proyecto con datos raros no debe tumbar el panel
            continue
    focus = initiative if initiative in names else (
        max(summaries, key=lambda s: s["last_activity"])["name"] if summaries else None)
    per_agent = {a: [] for a in agents}
    for n in names:
        for a, st in agent_project_states(n, agents, events).items():
            per_agent[a].append(st)
    feed = [{"ts": e["ts"], "agent": e["agent"], "project": e["project"], "event": e["event"], "note": e.get("note", "")}
            for e in events[-80:]]
    return {"token": TOKEN, "initiatives": summaries, "current": initiative if initiative in names else "",
            "focus": focus, "front": [public(agents[n]) for n in FRONT if n in agents],
            "rooms": [{"id": r["id"], "name": r["name"], "agents": [public(agents[n]) for n in r["agents"] if n in agents]}
                      for r in ROOMS],
            "projects": per_agent, "state": focus_state(focus, agents) if focus else None, "feed": feed,
            "live": live_state(), "security": security_state(),
            "bld_root": str(BLD_ROOT), "now": time.time(), "types": TYPES, "next_ids": next_ids()}


def new_project(payload):
    """Crea la carpeta de una iniciativa con bld_init.py; el ID (TIPO-NNN) lo asigna el tipo. No escribe en Bold Brain."""
    slug, typ, ado, title = (str(payload.get(k, "")).strip() for k in ("slug", "type", "ado", "title"))
    title = " ".join(title.split())[:120]  # una sola línea: no inyecta markdown en 00-init.md
    if typ not in TYPES:
        return 400, {"error": "Elige un tipo de proyecto"}
    if len(slug) > 60 or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        return 400, {"error": "El nombre debe ir en minúsculas, números y guiones (ej. limites-tarjeta)"}
    if ado and not re.fullmatch(r"\d{1,9}", ado):
        return 400, {"error": "El ID de ADO debe ser numérico"}
    cmd = [sys.executable, str(INIT), slug, "--type", typ, "--root", str(BLD_ROOT)] + (["--ado", ado] if ado else []) + (["--title", title] if title else [])
    with NEW_LOCK:  # dos creaciones simultáneas no deben repetir número
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    if r.returncode == 1:
        return 409, {"error": "Ya existe un proyecto con ese nombre"}
    if r.returncode != 0:
        return 500, {"error": (r.stderr or r.stdout)[:300]}
    name = pathlib.Path(r.stdout.splitlines()[0].split(" ", 1)[1]).name
    return 200, {"name": name, "output": r.stdout.strip()}


def next_ids():
    """Próximo ID por tipo, para mostrarlo en el formulario antes de crear."""
    out = {}
    for t in TYPES:
        top = 0
        for p in (BLD_ROOT.iterdir() if BLD_ROOT.exists() else []):
            m = re.match(rf"{t}-(\d+)(-|$)", p.name)
            if m and p.is_dir():
                top = max(top, int(m.group(1)))
        out[t] = f"{t}-{top + 1:03d}"
    return out


# ------------------------------------------------------------------ chat (solo lectura)
def chat(payload):
    agents = load_agents()
    agent = payload.get("agent", "")
    if not isinstance(agent, str) or agent not in agents:
        return 400, {"error": "agente desconocido"}
    mode = "boss" if payload.get("mode") == "boss" and agents[agent]["boss"] else "agent"
    target = agents[agents[agent]["boss"]] if mode == "boss" else agents[agent]
    project = payload.get("project", "")
    project = project if isinstance(project, str) else ""
    folder = BLD_ROOT / project if project and re.fullmatch(r"[A-Za-z0-9._-]+", project) and (BLD_ROOT / project).is_dir() \
        else BLD_ROOT
    message = str(payload.get("message", "")).strip()[:4000]
    if not message:
        return 400, {"error": "mensaje vacío"}
    history = payload.get("history")
    hist = [h for h in (history if isinstance(history, list) else [])[-8:] if isinstance(h, dict)]
    convo = "\n".join(f"{'PM' if h.get('role') == 'user' else target['name']}: {str(h.get('text', ''))[:1500]}" for h in hist)
    files = sorted(p.name for p in folder.iterdir() if p.is_file()) if folder != BLD_ROOT else []
    who = (f"El PM te consulta como jefe de `{agent}` ({agents[agent]['role']}) y quiere saber cómo va su trabajo."
           if mode == "boss" else f"Eres `{agent}`.")
    system = (target["_body"].strip() + "\n\n---\nMODO CONVERSACIÓN (Oficina BLD)\n"
              f"{who} Estás hablando con el PM en una terminal. Solo lectura: tienes Read, Glob y Grep; no puedes "
              "escribir archivos, crear tareas, enviar mensajes ni invocar otros agentes. Si el PM pide un cambio, "
              "dile qué agente debe hacerlo y que use el botón «Copiar invocación».\n"
              f"Carpeta del proyecto: {folder}\nArchivos en la raíz: {', '.join(files) or '(ninguno)'}\n"
              "Lee los archivos del proyecto antes de afirmar algo sobre su contenido. No inventes cifras, citas ni "
              "aprobaciones; si no lo sabes, dilo. Responde en español, breve y directo.")
    prompt = (f"Conversación previa:\n{convo}\n\n" if convo else "") + f"Mensaje del PM: {message}"
    if not CHAT_SLOTS.acquire(blocking=False):
        return 429, {"error": "hay 2 conversaciones en curso; espera a que termine una"}
    try:
        r = subprocess.run([CLAUDE, "-p", "--append-system-prompt", system, "--tools", "Read,Glob,Grep",
                            "--strict-mcp-config", "--no-session-persistence", "--add-dir", str(BLD_ROOT),
                            "--model", CHAT_MODEL],
                           input=prompt, cwd=str(folder), capture_output=True, text=True, timeout=170)
    except subprocess.TimeoutExpired:
        return 504, {"error": "el agente tardó más de 170 s"}
    except OSError as exc:
        return 500, {"error": f"no se pudo lanzar claude: {exc}"}
    finally:
        CHAT_SLOTS.release()
    if r.returncode != 0:
        return 500, {"error": (r.stderr or r.stdout or "error de claude")[:600]}
    return 200, {"reply": r.stdout.strip(), "speaker": target["name"], "mode": mode}


# ------------------------------------------------------------------ ejecutar (modo escritura, acotado al proyecto)
def audit(event, **kw):
    """Registro local de eventos sensibles (LIVE, ejecuciones, rechazos). Nunca guarda el token."""
    try:
        SEC_DIR.mkdir(mode=0o700, exist_ok=True)
        with (SEC_DIR / "audit.log").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "event": event, **kw}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def live_state():
    left = LIVE["until"] - time.time()
    return {"on": left > 0, "seconds_left": max(0, int(left))}


def set_live(payload):
    on = payload.get("on")
    if not isinstance(on, bool):
        return 400, {"error": "falta on: true|false"}
    if on:
        m = payload.get("minutes", 60)
        m = m if isinstance(m, int) and not isinstance(m, bool) else 60
        LIVE["until"] = time.time() + max(5, min(m, LIVE_MAX_MIN)) * 60
    else:
        LIVE["until"] = 0.0
    audit("live", on=on, minutes=(max(5, min(payload.get("minutes", 60) if isinstance(payload.get("minutes", 60), int) else 60, LIVE_MAX_MIN)) if on else 0))
    return 200, live_state()


def security_state():
    try:
        r = json.loads((SEC_DIR / "last-report.json").read_text(encoding="utf-8"))
        return {"ok": (bool(r["ok"]) if r.get("ok") is not None else None), "when": r.get("when", ""), "mode": r.get("mode", ""), "alerts": [str(a)[:200] for a in r.get("alerts", [])][:5]}
    except (OSError, ValueError):
        return {"ok": None, "when": "", "mode": "", "alerts": []}


def _emit(project, agent, event, note=""):
    try:
        with (BLD_ROOT / project / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"agent": agent, "event": event, "note": note[:120], "ts": time.time(), "project": project}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _run_job(rid, agent, a, folder, project, task, web):
    job = RUNS[rid]
    system = (a["_body"].strip() + "\n\n---\nMODO EJECUCIÓN (Oficina BLD)\n"
              f"Eres `{agent}`. El PM te pidió ejecutar una tarea desde la Oficina y confirmó. Puedes leer"
              + (", buscar en la web (LIVE está encendido)" if web else " (LIVE está APAGADO: no tienes acceso a internet; trabaja solo con los archivos del proyecto y di qué te faltó)")
              + f" y escribir/editar archivos SOLO dentro de {folder}. No tienes shell, no puedes invocar otros agentes ni usar "
              "servicios externos (Slack, correo, ClickUp, Bold Brain, etc.). Lee 00-init.md primero. Cita fuente y fecha de "
              "cada dato, marca supuestos y lo no verificado, y no inventes cifras. Cuando termines, responde en español con "
              "un resumen corto: qué archivos escribiste y qué quedó sin verificar.")
    abs_ = str(folder)
    cmd = [CLAUDE, "-p", "--append-system-prompt", system, "--tools", "Read,Glob,Grep,Write,Edit" + (",WebSearch,WebFetch" if web else ""),
           "--allowedTools", "Read", "Glob", "Grep", *(["WebSearch", "WebFetch"] if web else []), f"Edit(/{abs_}/**)",  # las reglas Edit cubren también Write
           "--strict-mcp-config", "--no-session-persistence", "--add-dir", abs_, "--model", RUN_MODEL]
    _emit(project, agent, "start", "Ejecución desde la Oficina: " + task)
    audit("run_start", agent=agent, project=project, web=web)
    try:
        r = subprocess.run(cmd, input=f"Tarea del PM: {task}", cwd=abs_, capture_output=True, text=True, timeout=RUN_TIMEOUT)
        if r.returncode == 0:
            job.update(status="done", reply=r.stdout.strip())
        else:
            job.update(status="error", error=(r.stderr or r.stdout or "error de claude")[:600])
    except subprocess.TimeoutExpired:
        job.update(status="error", error=f"tardó más de {RUN_TIMEOUT // 60} min")
    except OSError as exc:
        job.update(status="error", error=f"no se pudo lanzar claude: {exc}")
    finally:
        _emit(project, agent, "stop", "Ejecución desde la Oficina")
        audit("run_end", agent=agent, project=project, status=job.get("status"))
        RUN_SLOT.release()


def run_agent(payload):
    agents = load_agents()
    agent = payload.get("agent", "")
    project = payload.get("project", "")
    task = str(payload.get("task", "")).strip()[:4000]
    if payload.get("confirm") is not True:
        return 400, {"error": "falta la confirmación del PM"}
    if not isinstance(agent, str) or agent not in agents or not agents[agent].get("_body"):
        return 400, {"error": "agente desconocido"}
    if not isinstance(project, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", project) or not (BLD_ROOT / project).is_dir():
        return 400, {"error": "elige un proyecto concreto"}
    if not task:
        return 400, {"error": "falta la tarea"}
    folder = (BLD_ROOT / project).resolve()
    if BLD_ROOT.resolve() not in folder.parents:
        return 400, {"error": "proyecto fuera de la carpeta BLD"}
    if not RUN_SLOT.acquire(blocking=False):
        return 429, {"error": "ya hay una ejecución en curso; espera a que termine"}
    rid = secrets.token_hex(6)
    RUNS[rid] = {"status": "running", "agent": agent, "project": project, "started": time.time()}
    for k in sorted(RUNS, key=lambda k: RUNS[k]["started"])[:-20]:
        RUNS.pop(k, None)
    threading.Thread(target=_run_job, args=(rid, agent, agents[agent], folder, project, task, live_state()["on"]), daemon=True).start()
    return 200, {"id": rid, "web": live_state()["on"]}


# ------------------------------------------------------------------ http
class Handler(BaseHTTPRequestHandler):
    timeout = 15  # un cliente que no envía todo el cuerpo no retiene el hilo
    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _host_ok(self):
        return (self.headers.get("Host") or "") in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _page(self, name):
        html = (HERE / name).read_text(encoding="utf-8")
        return self._send(200, html, "text/html; charset=utf-8")

    def _json_body(self, limit):
        """Cuerpo JSON como dict, o None si es inválido, no es objeto o excede el límite."""
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n < 0 or n > limit:
                return None
            payload = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, TypeError):
            return None
        return payload if isinstance(payload, dict) else None

    def do_GET(self):  # noqa: N802
        if not self._host_ok():
            return self._send(403, "host no permitido")
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/":
            return self._page("index.html")
        if u.path == "/pixel":
            return self._page("pixel.html")
        if u.path == "/live":
            return self._page("live.html")
        if u.path.startswith("/assets/") and re.fullmatch(r"/assets/[a-z0-9_.-]+\.(png|json)", u.path):
            f = HERE / u.path[1:]
            if f.is_file():
                return self._send(200, f.read_bytes(), "image/png" if f.suffix == ".png" else "application/json")
        if u.path in ("/core.js", "/core.css"):
            ctype = "application/javascript" if u.path.endswith(".js") else "text/css"
            return self._send(200, (HERE / u.path[1:]).read_text(encoding="utf-8"), ctype + "; charset=utf-8")
        if u.path == "/api/office":
            return self._send(200, json.dumps(office(q.get("i", [""])[0]), allow_nan=False), "application/json")
        if u.path == "/api/file":
            try:
                folder = (BLD_ROOT / q.get("i", [""])[0]).resolve()
                target = (folder / q.get("f", [""])[0]).resolve()
                if BLD_ROOT.resolve() not in folder.parents or folder not in target.parents \
                        or target.suffix not in (".md", ".yaml", ".json", ".jsonl", ".txt") or not target.is_file():
                    return self._send(404, "not found")
                return self._send(200, target.read_text(encoding="utf-8", errors="replace")[:300_000])
            except (ValueError, OSError):
                return self._send(404, "not found")
        if u.path == "/api/run-status":
            j = RUNS.get(q.get("id", [""])[0])
            if not j:
                return self._send(404, "not found")
            return self._send(200, json.dumps({k: v for k, v in j.items() if k != "started"}, ensure_ascii=False), "application/json; charset=utf-8")
        if u.path == "/api/agent":
            name = q.get("n", [""])[0]
            target = AGENTS_DIR / f"{name}.md"
            if re.fullmatch(r"[a-z0-9-]+", name) and target.is_file():
                return self._send(200, target.read_text(encoding="utf-8", errors="replace"))
            a = load_agents().get(name) if re.fullmatch(r"[a-z0-9-]+", name) else None
            if a and a.get("_body"):
                return self._send(200, a["_body"])
        return self._send(404, "not found")

    def do_POST(self):  # noqa: N802
        # Protección contra páginas externas: Host válido, token (solo lo conoce nuestra página) y mismo origen.
        origin = self.headers.get("Origin")
        if not self._host_ok() or self.headers.get("X-Office-Token") != TOKEN \
                or (origin and urlparse(origin).netloc != self.headers.get("Host")):
            audit("rejected", path=urlparse(self.path).path[:60], origin=(origin or "")[:60])
            return self._send(403, "forbidden")
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/api/open-folder":
            folder = (BLD_ROOT / q.get("i", [""])[0]).resolve()
            if BLD_ROOT.resolve() in folder.parents and folder.is_dir():
                subprocess.Popen(["open", str(folder)])
                return self._send(200, "ok")
        if u.path == "/api/new-project":
            payload = self._json_body(5000)
            if payload is None:
                return self._send(400, json.dumps({"error": "json inválido"}), "application/json")
            code, body = new_project(payload)
            return self._send(code, json.dumps(body, ensure_ascii=False), "application/json; charset=utf-8")
        if u.path == "/api/live":
            payload = self._json_body(1000)
            if payload is None:
                return self._send(400, json.dumps({"error": "json inválido"}), "application/json")
            code, body = set_live(payload)
            return self._send(code, json.dumps(body), "application/json")
        if u.path == "/api/run":
            payload = self._json_body(10_000)
            if payload is None:
                return self._send(400, json.dumps({"error": "json inválido"}), "application/json")
            code, body = run_agent(payload)
            return self._send(code, json.dumps(body, ensure_ascii=False), "application/json; charset=utf-8")
        if u.path == "/api/chat":
            payload = self._json_body(60_000)
            if payload is None:
                return self._send(400, json.dumps({"error": "json inválido"}), "application/json")
            code, body = chat(payload)
            return self._send(code, json.dumps(body, ensure_ascii=False), "application/json; charset=utf-8")
        return self._send(404, "not found")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--root", default="", help="carpeta BLD alternativa (demos)")
    args = ap.parse_args()
    PORT = args.port
    if args.root:
        BLD_ROOT = pathlib.Path(args.root)
    print(f"Oficina BLD en http://127.0.0.1:{PORT}  (pixel: /pixel)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
