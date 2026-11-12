#!/usr/bin/env python3
"""Agrega a ~/.claude/settings.json los hooks de seguridad (SessionStart y SessionEnd -> security_check.py).
Solo toca esos dos eventos y no quita nada. Sin argumentos solo muestra qué agregaría; con --aplicar hace copia de
seguridad (settings.json.bak-AAAAMMDD-HHMMSS) y escribe el cambio. Lo ejecuta el usuario: Claude Code no edita su propio settings.json."""
import json, pathlib, shutil, sys, time

SETTINGS = pathlib.Path.home() / ".claude" / "settings.json"
CHECK = pathlib.Path.home() / ".claude" / "office" / "security_check.py"
WANT = {"SessionStart": "--start", "SessionEnd": "--end"}

data = json.loads(SETTINGS.read_text(encoding="utf-8"))
hooks = data.setdefault("hooks", {})
added = 0
for event, flag in WANT.items():
    cmd = f"python3 {CHECK} {flag}"
    entries = hooks.setdefault(event, [])
    if any(h.get("command") == cmd for e in entries for h in e.get("hooks", [])):
        print(f"{event}: ya existe")
        continue
    entries.append({"hooks": [{"type": "command", "command": cmd, "timeout": 20}]})
    added += 1
    print(f"{event}: se agregaría -> {cmd}")
if "--aplicar" not in sys.argv:
    print("Solo vista previa. Para aplicar: python3 " + sys.argv[0] + " --aplicar")
    sys.exit(0)
if not added:
    print("Nada que agregar.")
    sys.exit(0)
backup = SETTINGS.with_name(f"settings.json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
shutil.copy2(SETTINGS, backup)
SETTINGS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
json.loads(SETTINGS.read_text(encoding="utf-8"))
print(f"Listo. Copia de seguridad: {backup}. Nueva sesión para que se carguen los hooks.")
