# Oficina BLD · construcción de píxeles

Vista pixel art (16 bits) de la Oficina BLD. Contiene **solo** la parte de píxeles:

| Archivo | Para qué |
|---|---|
| `pixel.html` | Vista pixel de la Oficina (`/pixel`) |
| `live.html` | Incrusta Pixel Agents si corre en local (`/live`) |
| `make_assets.py` | Genera los PNG originales con Pillow (`python3 make_assets.py [--preview]`) |
| `assets/` | 47 PNG + `manifest.json` ya generados |

Los gráficos son originales, sin licencias externas. `live.html` enlaza a la extensión Pixel Agents (MIT, https://github.com/pixel-agents-hq/pixel-agents).

**No incluye** el servidor ni la lógica (`server.py`, `core.js`, `core.css`) ni la vista profesional: viven en el repo privado de la Oficina. Para ver estas vistas hay que copiarlas junto a esos archivos en `~/.claude/office/`.

Agregado el 2026-11-12.
