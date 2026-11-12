#!/usr/bin/env python3
"""Verificación de seguridad local (solo lectura sobre el sistema). LOCAL ONLY: no envía nada a ningún servicio.

Uso:
  python3 security_check.py --init    guarda la línea base (el estado ACTUAL se considera limpio: revísalo antes)
  python3 security_check.py --start   chequeo de inicio de sesión
  python3 security_check.py --end     chequeo de fin de sesión
  python3 security_check.py           chequeo manual
Escribe el informe en ~/.claude/office/.security/ (last-report.json/.md, history.log) y sale con 0 sin alertas, 1 con alertas.
Con --start/--end imprime un resumen corto (el de SessionStart entra al contexto de Claude); con alertas avisa con una
notificación local de macOS. No modifica settings.json, agentes, procesos ni red; solo escribe dentro de .security/.
"""
import hashlib, json, os, pathlib, re, subprocess, sys, time

HOME = pathlib.Path.home()
OFFICE = HOME / ".claude" / "office"
SEC = OFFICE / ".security"
BASE = SEC / "baseline.json"
PORT = 8765
KNOWN_HOOK = f"python3 {OFFICE}/hook.py"
WATCH_FILES = [HOME / ".claude" / "settings.json", HOME / ".claude" / "settings.local.json", HOME / ".zshrc", HOME / ".zprofile",
               HOME / ".bash_profile", HOME / ".bashrc", HOME / ".ssh" / "authorized_keys", HOME / ".claude" / "CLAUDE.md"]
OFFICE_EXT = {".py", ".js", ".css", ".html", ".json"}


def sha(p):
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except OSError:
        return None


def run(cmd, timeout=10):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def snapshot():
    s = {"files": {str(p): sha(p) for p in WATCH_FILES if p.exists()}}
    s["agents"] = {p.name: sha(p) for p in sorted((HOME / ".claude" / "agents").rglob("*")) if p.is_file()}
    s["office"] = {p.name: sha(p) for p in sorted(OFFICE.iterdir()) if p.is_file() and p.suffix in OFFICE_EXT}
    s["launch"] = sorted(p.name for p in (HOME / "Library" / "LaunchAgents").glob("*")) if (HOME / "Library" / "LaunchAgents").is_dir() else []
    s["cron"] = run(["crontab", "-l"]).strip().splitlines()
    try:
        cfg = json.loads((HOME / ".claude" / "settings.json").read_text())
    except (OSError, ValueError):
        cfg = {}
    cmds = sorted({h.get("command", "") for es in (cfg.get("hooks") or {}).values() for e in es for h in e.get("hooks", [])})
    s["hook_cmds"] = cmds
    s["mcp"] = sorted((cfg.get("mcpServers") or {}).keys())
    s["perm_allow"] = sorted(((cfg.get("permissions") or {}).get("allow")) or [])
    return s


def listeners():
    """[(proceso, pid, dirección)] de sockets TCP en escucha."""
    out, rows = run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"]), []
    for ln in out.splitlines()[1:]:
        f = ln.split()
        if len(f) >= 9:
            rows.append((f[0], f[1], f[8]))
    return rows


def check():
    alerts, notes = [], []
    cur = snapshot()
    base = json.loads(BASE.read_text()) if BASE.exists() else None
    if base is None:
        notes.append("Sin línea base: ejecuta `security_check.py --init` tras revisar este informe (no se pueden detectar cambios).")

    # 1) El servidor de la Oficina solo debe escuchar en loopback
    own = [r for r in listeners() if r[2].endswith(f":{PORT}")]
    for proc, pid, addr in own:
        if not addr.startswith(("127.0.0.1:", "[::1]:", "localhost:")):
            alerts.append(f"La Oficina (pid {pid}) escucha en {addr}: debe ser solo 127.0.0.1")
    if not own:
        notes.append(f"La Oficina no está corriendo en el puerto {PORT} (normal si está apagada).")

    # 2) Conexiones entrantes de otras máquinas al puerto de la Oficina
    for ln in run(["lsof", "-nP", f"-iTCP:{PORT}", "-sTCP:ESTABLISHED"]).splitlines()[1:]:
        m = re.search(r"->([^\s:]+(?::\d+)?)", ln)
        peer = ln.split("->")[-1].split(" ")[0] if "->" in ln else ""
        if peer and not peer.startswith(("127.0.0.1:", "[::1]:", "localhost:")) and f":{PORT}->" in ln.replace(" ", ""):
            alerts.append(f"Conexión no local al puerto {PORT}: {ln.split()[0]} -> {peer}")

    # 3) Sockets en escucha expuestos a la red (no loopback)
    expo = sorted({(p, a) for p, _, a in listeners() if not a.startswith(("127.0.0.1:", "[::1]:", "localhost:"))})
    prev = set(map(tuple, (base or {}).get("exposed", [])))
    for p, a in expo:
        if base is not None and (p, a) not in prev:
            alerts.append(f"Nuevo socket expuesto a la red: {p} en {a}")
    cur["exposed"] = [list(x) for x in expo]
    if base is None and expo:
        notes.append("Sockets expuestos a la red hoy: " + ", ".join(f"{p} {a}" for p, a in expo[:8]))

    # 4) Hooks y configuración de Claude Code
    hooks_ok = {KNOWN_HOOK}
    for c in cur["hook_cmds"]:
        if c not in hooks_ok and (base is None or c not in base["hook_cmds"]):
            (alerts if base is not None else notes).append(f"Hook no reconocido en settings.json: {c[:120]}")
    if base:
        for k in ("mcp", "perm_allow"):
            add = sorted(set(cur[k]) - set(base[k]))
            if add:
                alerts.append(f"settings.json: nuevo(s) en {k}: {', '.join(add)[:200]}")

    # 5) Archivos vigilados, agentes y código de la Oficina
    if base:
        def diff(label, a, b):
            for name in sorted(set(a) | set(b)):
                if a.get(name) != b.get(name):
                    kind = "nuevo" if name not in b else "eliminado" if name not in a else "modificado"
                    alerts.append(f"{label} {kind}: {name}")
        diff("Archivo vigilado", cur["files"], base["files"])
        diff("Agente", cur["agents"], base["agents"])
        diff("Código de la Oficina", cur["office"], base["office"])
        for k, lab in (("launch", "LaunchAgent"), ("cron", "cron")):
            for x in sorted(set(cur[k]) ^ set(base[k])):
                alerts.append(f"{lab} cambió: {x[:120]}")

    # 6) Procesos sospechosos conocidos
    ps = run(["ps", "-axo", "pid=,command="])
    for ln in ps.splitlines():
        if re.search(r"pixel-agents|ngrok|cloudflared|frpc|\bnc -l|socat .*LISTEN", ln) and "security_check" not in ln:
            alerts.append("Proceso a revisar: " + ln.strip()[:140])

    # 7) Rechazos registrados por el servidor (POST con token/host inválido)
    log = OFFICE / ".security" / "audit.log"
    if log.exists():
        cutoff, rej = time.time() - 24 * 3600, 0
        for ln in log.read_text(errors="replace").splitlines()[-2000:]:
            try:
                e = json.loads(ln)
            except ValueError:
                continue
            if e.get("event") == "rejected" and e.get("ts", 0) > cutoff:
                rej += 1
        if rej >= 5:
            alerts.append(f"El servidor rechazó {rej} peticiones POST inválidas en 24 h (token/host/origen)")
        elif rej:
            notes.append(f"{rej} petición(es) POST rechazadas en 24 h")
    cur["_has_base"] = base is not None
    return alerts, notes, cur


def main():
    SEC.mkdir(mode=0o700, exist_ok=True)
    mode = next((a for a in sys.argv[1:] if a in ("--init", "--start", "--end")), "--manual")
    alerts, notes, cur = check()
    has_base = cur.pop("_has_base", False)
    cur["_has_base"] = has_base
    if mode == "--init":
        cur.pop("_has_base", None)
        BASE.write_text(json.dumps(cur, indent=1, ensure_ascii=False))
        print(f"Línea base guardada en {BASE}. Se consideró limpio el estado actual: revisa antes los avisos de abajo.")
        for a in alerts + notes:
            print(" -", a)
        return 0
    rep = {"mode": mode.strip("-"), "ts": time.time(), "when": time.strftime("%Y-%m-%d %H:%M:%S"), "ok": (not alerts) if cur.get("_has_base") else None, "alerts": alerts, "notes": notes}
    (SEC / "last-report.json").write_text(json.dumps(rep, ensure_ascii=False))
    (SEC / "last-report.md").write_text(f"# Seguridad {rep['when']} ({rep['mode']})\n\n" + (("Sin alertas.\n" if has_base else "Sin línea base: no se pueden detectar cambios.\n") if not alerts else "".join(f"- ALERTA: {a}\n" for a in alerts)) + "".join(f"- nota: {n}\n" for n in notes))
    with (SEC / "history.log").open("a") as f:
        f.write(f"{rep['when']} {rep['mode']} {'OK' if not alerts else str(len(alerts)) + ' alertas'}\n")
    if mode in ("--start", "--end"):
        print(f"[seguridad {rep['mode']}] " + ("sin alertas" if not alerts else f"{len(alerts)} ALERTA(S): " + " | ".join(alerts[:5])))
    else:
        print((SEC / "last-report.md").read_text())
    if alerts and mode in ("--start", "--end"):
        msg = f"{len(alerts)} alerta(s): {alerts[0][:90]}".replace('"', "'")
        run(["osascript", "-e", f'display notification "{msg}" with title "Seguridad Oficina BLD"'])
    return 1 if alerts else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001  (un hook nunca debe romper la sesión)
        print(f"[seguridad] error del verificador: {exc}")
        sys.exit(0 if any(a in sys.argv for a in ("--start", "--end")) else 2)
