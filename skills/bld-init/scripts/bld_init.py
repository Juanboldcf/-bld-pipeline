#!/usr/bin/env python3
"""bld_init.py — creates the run folder of a BLD initiative. Python 3 stdlib only.

  bld_init.py <slug> [--type FEA|DIS|INV|MET|CAM|OTR] [--ado <ADO feature id>] [--id <id>] [--title "<name>"] [--root <BLD root>]

Folder: <root>/<TYPE>-<NNN>-<slug>/ when --type is given (NNN = next consecutive number for that type);
else <root>/<id>-<slug>/ when a legacy numeric --id is given, else <root>/<slug>/.
Flat pipeline files (01-..09-) live at the top level (bld_gate.py reads them there);
everything else (storm, praxis, designs, iterations, definitions) goes in subfolders.
Never overwrites: if the folder exists it only reports it. Exit 0 ok / 1 exists / 2 usage.
"""
import argparse, datetime, pathlib, re, sys

ROOT = pathlib.Path("/Users/juan.alvarez/Documents/Claude/BLD")
SUBDIRS = {
    "definiciones": "Definiciones de negocio, respuestas del PM, reglas confirmadas",
    "storm": "Event storming (eventstorm.yaml / .html)",
    "praxis": "Artefactos Praxis (survey, proposal, spec, design, tasks)",
    "disenos": "Diseños, wireframes y prototipos (Figma, HTML, PDF)",
    "iteraciones": "Iteraciones de diseño y feedback de UX/UI",
    "referencias": "Documentos fuente (PRD de origen, actas, correos)",
}

TYPES = {"FEA": "Feature", "DIS": "Diseño", "INV": "Investigación", "MET": "Seguimiento de métricas", "CAM": "Campaña", "OTR": "Otro"}


def next_id(root: pathlib.Path, typ: str) -> str:
    top = 0
    if root.exists():
        for p in root.iterdir():
            m = re.match(rf"{typ}-(\d+)(-|$)", p.name)
            if m and p.is_dir():
                top = max(top, int(m.group(1)))
    return f"{typ}-{top + 1:03d}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--id", default="")
    ap.add_argument("--type", default="", choices=[""] + list(TYPES))
    ap.add_argument("--ado", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args()
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.slug):
        print("error: slug must be lowercase letters/digits separated by single hyphens", file=sys.stderr)
        return 2
    if a.id and not re.fullmatch(r"\d+", a.id):
        print("error: --id must be the numeric ADO work item id", file=sys.stderr)
        return 2
    if a.ado and not re.fullmatch(r"\d+", a.ado):
        print("error: --ado must be the numeric ADO work item id", file=sys.stderr)
        return 2
    if a.type:
        a.id = next_id(pathlib.Path(a.root), a.type)
    name = f"{a.id}-{a.slug}" if a.id else a.slug
    folder = pathlib.Path(a.root) / name
    if folder.exists():
        print(f"EXISTS {folder}")
        return 1
    folder.mkdir(parents=True)
    for d in SUBDIRS:
        (folder / d).mkdir()
    (folder / "events.jsonl").touch()
    today = datetime.date.today().isoformat()
    rows = "\n".join(f"| `{d}/` | {desc} |" for d, desc in SUBDIRS.items())
    (folder / "00-init.md").write_text(
        f"# {a.title or a.slug}\n\n"
        "| Campo | Valor |\n|---|---|\n"
        f"| Carpeta | `{name}` |\n"
        f"| ID | {a.id or 'sin id'} |\n"
        f"| Tipo | {a.type or 'FEA'} · {TYPES.get(a.type or 'FEA')} |\n"
        f"| Feature ADO | {a.ado or (a.id if a.id.isdigit() else '') or 'sin id todavía'} |\n"
        "| ClickUp | |\n| PM | |\n"
        f"| Creada | {today} |\n"
        f"| Bold Brain | proyecto `bld-agentes`, claves `bld/{name}/…` |\n\n"
        "## Estructura\n\n"
        "Archivos del pipeline en la raíz (`01-` a `09-`, versiones `vN`, nunca se sobrescriben). "
        "Todo lo demás en subcarpetas:\n\n"
        f"| Carpeta | Contenido |\n|---|---|\n{rows}\n\n"
        "`events.jsonl`: una línea JSON por evento de agente (lo lee la Oficina BLD).\n",
        encoding="utf-8",
    )
    print(f"CREATED {folder}")
    print(f"BRAIN project=bld-agentes key_prefix=bld/{name}/")
    return 0

if __name__ == "__main__":
    sys.exit(main())
