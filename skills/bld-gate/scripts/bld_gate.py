#!/usr/bin/env python3
"""bld_gate.py — deterministic gates for the BLD product pipeline (run folder of markdown files).

Audit only: reads the run folder, writes nothing. Python 3 standard library only.

  bld_gate.py gate   <run-folder> <to-pr|to-prd|to-comms|to-hu|hu-catalog>
  bld_gate.py status <run-folder>
  bld_gate.py trace  <run-folder> --eventstorm <eventstorm.yaml>
  bld_gate.py --list

Exit 0 = every check passed · 1 = at least one FAIL · 2 = usage / missing file.
A PASS is structural only: it never says the content is right.
"""
import re
import sys
from pathlib import Path

DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
AREAS = ["UX/UI", "Legal", "Finance", "Core", "FinOps", "Backend", "Mobile", "Web",
         "Operations", "Platform", "Auth/ID", "Lifecycle", "PM", "C-level"]
C_LEVEL = re.compile(r"c-level|ceo|cfo|cto|coo|cpo|chief|founder", re.I)
RESIDUE_INLINE = re.compile(
    r"\[(?:Name|Nombre|YYYY-MM-DD|Product/Feature Name|Headline|Subheadline|City, Date|"
    r"Rol/Usuario|Acción/Funcionalidad|Beneficio/Valor de negocio)\b[^\]]*\]|\[N\]")
RESIDUE_LINE = re.compile(r"^\s*\[[^\]\[]+\]\s*$")
PROPOSED = re.compile(r"\[PROPUESTO[^\]]*\]")
OI_TYPES = {"unknown", "conflict", "assumption", "missing-input"}

CHECKS = {
    "artifact": ("the artifact the gate needs exists", "a file is missing", "the agent that writes it"),
    "approvals": ("approval rows are all ✅ with a date (latest round per approver)", "a row is not ✅ or has no date, or PM / C-level is absent", "the PM, in the approval table"),
    "tracker": ("PRD tracker has the 14 rows, each Final ✅ with owner and date", "a row is missing, pending or incomplete", "bld-prd-agent with the PM"),
    "review": ("PRD review file for the same version exists and is not FAIL", "no 06b file for that version, or verdict FAIL", "the caller saves bld-prd-reviewer's reply; bld-prd-agent fixes"),
    "placeholders": ("no template residue left ([Name], [YYYY-MM-DD], a line that is only [instructions])", "residue found", "the agent that wrote the artifact"),
    "proposed-tags": ("no [PROPUESTO] tag left (a number, quote or name nobody gave)", "a tag remains", "the PM adopts or replaces it"),
    "open-items": ("Open items table: types valid, conflict is always 'frena', nothing 'frena' left open, resolved rows name who resolved", "a rule is broken or a blocking item is open", "the PM"),
    "decisions": ("Decisions table rows have author, why and alternatives; the author is a person", "a cell is empty or the author is an agent", "the PM, who decides"),
    "hu-fields": ("every HU has one Area, a PRD ref, Depends on, and a DoR", "a field is missing", "bld-hu-agent"),
    "hu-trace": ("every Must requirement of the PRD is covered by an HU; every ref exists in the PRD", "a Must has no HU, or an HU cites an unknown id", "bld-hu-agent"),
    "hu-deps": ("Depends on points to existing HUs and has no cycle; HU ids are unique", "dangling, duplicate or circular", "bld-hu-agent"),
}


class Report:
    def __init__(self):
        self.fails, self.warns, self.passed = [], [], []

    def fail(self, check, msg):
        self.fails.append((check, msg))

    def warn(self, check, msg):
        self.warns.append((check, msg))

    def ok(self, check):
        if check not in {c for c, _ in self.fails}:
            self.passed.append(check)

    def render(self, title):
        n = len(self.passed) + len({c for c, _ in self.fails})
        head = "PASS" if not self.fails else "FAIL"
        out = [f"{title}", f"Structure: {head} ({n} checks, {len(self.fails)} problems)"]
        for c, m in self.fails:
            out.append(f"FAIL {c}: {m} → fixed in: {CHECKS[c][2]}")
        for c, m in self.warns:
            out.append(f"WARN {c}: {m}")
        if not self.fails:
            out.append("A PASS is structural only: it says nothing about whether the content is right.")
        return "\n".join(out)


def latest(folder, pattern):
    best, best_n = None, -1
    for p in folder.iterdir():
        m = re.fullmatch(pattern, p.name)
        if m:
            n = int(m.group(1)) if m.groups() and m.group(1) else 0
            if n > best_n:
                best, best_n = p, n
    return best, best_n


def read(path):
    return path.read_text(encoding="utf-8")


def section(text, heading_re):
    """Lines under the first heading whose text matches, up to the next heading of equal or higher level."""
    lines, out, level = text.splitlines(), [], None
    for ln in lines:
        m = re.match(r"^(#+)\s+(.*)", ln)
        if m and level is None and re.search(heading_re, m.group(2), re.I):
            level = len(m.group(1))
            continue
        if level is not None:
            if m and len(m.group(1)) <= level:
                break
            out.append(ln)
    return out if level is not None else None


def table(lines):
    """Markdown table -> (header, rows); cells stripped of ** and whitespace."""
    rows = []
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip().strip("*").strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    if not rows:
        return [], []
    return [h.lower() for h in rows[0]], rows[1:]


def col(header, *names):
    for i, h in enumerate(header):
        if any(n in h for n in names):
            return i
    return None


def approvals(text, heading_re, rep, label, need_pm=True, need_clevel=True):
    sec = section(text, heading_re)
    if sec is None:
        rep.fail("approvals", f"{label}: no approval section found")
        return
    header, rows = table(sec)
    i_name, i_role, i_dec, i_date = col(header, "name", "nombre"), col(header, "role", "rol"), col(header, "decision"), col(header, "date", "fecha")
    if None in (i_name, i_dec, i_date):
        rep.fail("approvals", f"{label}: approval table needs Name, Decision and Date columns")
        return
    latest_by = {}
    for r in rows:
        if len(r) <= max(i_name, i_dec, i_date) or not r[i_name] or r[i_name] in ("...", "…"):
            continue
        latest_by[r[i_name].lower()] = r
    if len(latest_by) < 2:
        rep.fail("approvals", f"{label}: fewer than 2 approvers recorded")
    bad = []
    for name, r in latest_by.items():
        dec, date = r[i_dec], r[i_date]
        if "✅" not in dec or "❌" in dec or "🔄" in dec:
            bad.append(f"{r[i_name]} is not ✅ ({dec or 'empty'})")
        elif not DATE.search(date):
            bad.append(f"{r[i_name]} has ✅ without a date")
    for b in bad:
        rep.fail("approvals", f"{label}: {b}")
    blob = " ".join(" ".join(r) for r in latest_by.values())
    if need_pm and not re.search(r"\bPM\b|Juan David", blob):
        rep.fail("approvals", f"{label}: no PM row")
    if need_clevel and not C_LEVEL.search(blob):
        rep.fail("approvals", f"{label}: no C-level row")
    rep.ok("approvals")


def tracker(text, rep):
    sec = section(text, r"approval tracker")
    if sec is None:
        rep.fail("tracker", "no 'Area Approval Tracker' section")
        return
    header, rows = table(sec)
    i_area, i_owner, i_final, i_date = col(header, "area", "área"), col(header, "owner"), col(header, "final"), col(header, "date")
    if None in (i_area, i_owner, i_final, i_date):
        rep.fail("tracker", "tracker needs Area, Owner, Final and Date columns")
        return
    by = {r[i_area].lower(): r for r in rows if len(r) > max(i_area, i_owner, i_final, i_date)}
    for a in AREAS:
        r = next((v for k, v in by.items() if a.lower() in k), None)
        if r is None:
            rep.fail("tracker", f"row missing: {a}")
        elif "✅" not in r[i_final]:
            rep.fail("tracker", f"{a} Final is not ✅ ({r[i_final] or 'empty'})")
        elif not r[i_owner] or r[i_owner] in ("...", "…"):
            rep.fail("tracker", f"{a} has no owner")
        elif not DATE.search(r[i_date]):
            rep.fail("tracker", f"{a} has ✅ without a date")
    rep.ok("tracker")


def review(folder, n, rep):
    p = folder / f"06b-prd-review_v{n}.md"
    if not p.exists():
        rep.fail("review", f"06b-prd-review_v{n}.md missing: the caller must save the reviewer's reply there")
        return
    m = re.search(r"^Verdict:\s*(PASS WITH FIXES|PASS|FAIL)\b", read(p), re.M)
    if not m:
        rep.fail("review", f"{p.name} has no 'Verdict:' line")
    elif m.group(1) == "FAIL":
        rep.fail("review", f"{p.name} verdict is FAIL")
    rep.ok("review")


def lint(text, name, rep, tags):
    fenced = False
    for i, ln in enumerate(text.splitlines(), 1):
        if ln.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced or ln.lstrip().startswith("|---"):
            continue
        if RESIDUE_INLINE.search(ln) or RESIDUE_LINE.match(ln):
            rep.fail("placeholders", f"{name}:{i} template residue: {ln.strip()[:70]}")
        if tags and PROPOSED.search(ln):
            rep.fail("proposed-tags", f"{name}:{i} {ln.strip()[:70]}")
    rep.ok("placeholders")
    rep.ok("proposed-tags")


def open_items(text, name, rep, blocking_fails=True):
    sec = section(text, r"open items")
    if sec is None:
        return
    header, rows = table(sec)
    i = {k: col(header, *v) for k, v in {"id": ("id",), "type": ("type",), "blocks": ("block",), "status": ("status",), "by": ("resolved",)}.items()}
    if None in (i["id"], i["type"], i["blocks"], i["status"]):
        rep.fail("open-items", f"{name}: Open items table needs ID, Type, Blocks, Status columns")
        return
    for r in rows:
        if len(r) <= max(v for v in i.values() if v is not None) or not r[i["id"]] or r[i["id"]] in ("...", "…"):
            continue
        t, b, s = r[i["type"]].lower(), r[i["blocks"]].lower(), r[i["status"]].lower()
        if t not in OI_TYPES:
            rep.fail("open-items", f"{name}: {r[i['id']]} has type '{t}' (use {sorted(OI_TYPES)})")
        if t == "conflict" and "no" in b:
            rep.fail("open-items", f"{name}: {r[i['id']]} is a conflict and must be 'frena'")
        if s.startswith("open") and b.startswith("frena") and blocking_fails:
            rep.fail("open-items", f"{name}: {r[i['id']]} frena and is still open")
        if s.startswith("resolved") and (i["by"] is None or not r[i["by"]]):
            rep.fail("open-items", f"{name}: {r[i['id']]} is resolved without saying who resolved it")
    rep.ok("open-items")


def decisions(text, name, rep):
    sec = section(text, r"decisions")
    if sec is None:
        return
    header, rows = table(sec)
    i = {k: col(header, *v) for k, v in {"id": ("id",), "by": ("decided",), "why": ("why",), "alt": ("alternativ",)}.items()}
    if None in i.values():
        rep.fail("decisions", f"{name}: Decisions table needs ID, Decided by, Why, Alternatives columns")
        return
    for r in rows:
        if len(r) <= max(i.values()) or not r[i["id"]] or r[i["id"]] in ("...", "…"):
            continue
        for k in ("by", "why", "alt"):
            if not r[i[k]] or r[i[k]] in ("...", "…"):
                rep.fail("decisions", f"{name}: {r[i['id']]} has an empty '{k}'")
        if re.search(r"\bbld-|\bagent\b", r[i["by"]], re.I):
            rep.fail("decisions", f"{name}: {r[i['id']]} is authored by an agent; a person decides")
    rep.ok("decisions")


def need(folder, pattern, label, rep):
    p, n = latest(folder, pattern)
    if p is None:
        rep.fail("artifact", f"{label} not found in {folder}")
    return p, n


def prd_requirements(text):
    """{id: priority} from the PRD's functional-requirements table (rows whose first cell is F<n>)."""
    out = {}
    for ln in text.splitlines():
        cells = [c.strip().strip("*") for c in ln.strip().strip("|").split("|")]
        if ln.strip().startswith("|") and cells and re.fullmatch(r"F\d+", cells[0]):
            out[cells[0]] = next((c for c in cells[1:] if re.fullmatch(r"Must|Should|Could|Won'?t", c, re.I)), "?").capitalize()
        elif ln.strip().startswith("|") and cells and re.fullmatch(r"NF\d+", cells[0]):
            out[cells[0]] = "NF"
    return out


def catalog(folder, rep):
    p, _ = need(folder, r"08-hu-catalog(?:_v(\d+))?\.md", "08-hu-catalog.md", rep)
    prd, n = need(folder, r"06-prd_v(\d+)\.md", "06-prd_vN.md", rep)
    if p is None or prd is None:
        return
    text = read(p)
    blocks = re.split(r"^###\s+\[?(HU-\d+)\]?[^\n]*$", text, flags=re.M)
    hus, seen, blocks_list = {}, [], []
    for k in range(1, len(blocks), 2):
        hid, body = blocks[k], blocks[k + 1]
        seen.append(hid)
        hus[hid] = body
        blocks_list.append((hid, body))
    for dup in {h for h in seen if seen.count(h) > 1}:
        rep.fail("hu-deps", f"{dup} appears more than once")
    reqs = prd_requirements(read(prd))
    covered, deps = set(), {}
    for hid, body in blocks_list:
        area = re.search(r"\*\*Area:\*\*\s*(.+)", body)
        ref = re.search(r"\*\*PRD ref:\*\*\s*(.+)", body)
        dep = re.search(r"\*\*Depends on:\*\*\s*(.+)", body)
        if not area or not area.group(1).strip() or RESIDUE_INLINE.search(area.group(1)) or re.search(r"\s/\s", area.group(1)):
            rep.fail("hu-fields", f"{hid}: needs exactly one Area")
        if not ref or not re.search(r"N?F\d+", ref.group(1)):
            rep.fail("hu-fields", f"{hid}: PRD ref missing")
        else:
            for rid in re.findall(r"\bN?F\d+\b", ref.group(1)):
                covered.add(rid)
                if reqs and rid not in reqs:
                    rep.fail("hu-trace", f"{hid} cites {rid}, which is not in {prd.name}")
        if not dep:
            rep.fail("hu-fields", f"{hid}: 'Depends on' missing (write None if none)")
        else:
            deps.setdefault(hid, []).extend(re.findall(r"HU-\d+", dep.group(1)))
        if "Definición de Ready" not in body or not re.search(r"✓\s*R\d", body):
            rep.fail("hu-fields", f"{hid}: DoR missing or empty")
    for rid, pr in reqs.items():
        if pr == "Must" and rid not in covered:
            rep.fail("hu-trace", f"{rid} (Must) has no HU")
        elif pr in ("Should", "Could", "NF", "?") and rid not in covered:
            rep.warn("hu-trace", f"{rid} ({pr}) has no HU")
    for hid, ds in deps.items():
        for d in ds:
            if d not in hus:
                rep.fail("hu-deps", f"{hid} depends on {d}, which does not exist")
    state = {}

    def visit(h, path):
        if state.get(h) == 2:
            return
        if state.get(h) == 1:
            rep.fail("hu-deps", "circular dependency: " + " → ".join(path + [h]))
            return
        state[h] = 1
        for d in deps.get(h, []):
            if d in hus:
                visit(d, path + [h])
        state[h] = 2

    for h in hus:
        visit(h, [])
    lint(text, p.name, rep, tags=True)
    open_items(text, p.name, rep)
    if not hus:
        rep.fail("hu-fields", f"{p.name} contains no '### [HU-nnn]' blocks")
    for c in ("hu-fields", "hu-trace", "hu-deps"):
        rep.ok(c)


def gate(folder, to):
    rep = Report()
    if to == "to-pr":
        p, _ = need(folder, r"04-opportunity-brief\.md", "04-opportunity-brief.md", rep)
        if p:
            t = read(p)
            approvals(t, r"approval", rep, p.name)
            lint(t, p.name, rep, tags=True)
            open_items(t, p.name, rep)
            decisions(t, p.name, rep)
    elif to == "to-prd":
        p, _ = need(folder, r"05-pr_v(\d+)\.md", "05-pr_vN.md", rep)
        if p:
            t = read(p)
            approvals(t, r"^approval", rep, p.name)
            lint(t, p.name, rep, tags=True)
            open_items(t, p.name, rep)
            decisions(t, p.name, rep)
    elif to == "to-comms":
        p, n = need(folder, r"06-prd_v(\d+)\.md", "06-prd_vN.md", rep)
        if p:
            review(folder, n, rep)
            lint(read(p), p.name, rep, tags=False)
            open_items(read(p), p.name, rep, blocking_fails=False)
            decisions(read(p), p.name, rep)
    elif to == "to-hu":
        p, n = need(folder, r"06-prd_v(\d+)\.md", "06-prd_vN.md", rep)
        if p:
            t = read(p)
            tracker(t, rep)
            review(folder, n, rep)
            lint(t, p.name, rep, tags=True)
            open_items(t, p.name, rep)
            decisions(t, p.name, rep)
    elif to == "hu-catalog":
        catalog(folder, rep)
    else:
        return None
    return rep


def status(folder):
    files = {
        "brief": latest(folder, r"04-opportunity-brief\.md")[0],
        "pr": latest(folder, r"05-pr_v(\d+)\.md")[0],
        "prd": latest(folder, r"06-prd_v(\d+)\.md")[0],
        "hu": latest(folder, r"08-hu-catalog(?:_v(\d+))?\.md")[0],
    }
    out = [f"BLD pipeline — {folder.name}"]
    for k, v in files.items():
        out.append(f"  {k:<6}{v.name if v else '—'}")
    nxt = None
    for to, label in (("to-pr", "PR"), ("to-prd", "PRD"), ("to-hu", "HU")):
        r = gate(folder, to)
        state = "PASS" if not r.fails else f"FAIL ({len(r.fails)})"
        out.append(f"  gate {to:<8}{state}")
        if r.fails and nxt is None:
            nxt = f"unlock {label}: {r.fails[0][1]}"
    out.append(f"Next: {nxt or 'gates to HU all pass; run `gate <folder> hu-catalog` on the catalog'}")
    return "\n".join(out)


def trace(folder, es_path):
    es = read(Path(es_path))
    ids = re.findall(r"^\s*-\s+id:\s+(inv-[a-z0-9-]+)", es, re.M)
    docs = "\n".join(read(p) for p in folder.iterdir() if re.match(r"0[68]", p.name) and p.suffix == ".md")
    missing = [i for i in ids if i not in docs]
    out = [f"EventStorm trace — {len(ids)} rules, {len(ids) - len(missing)} cited in PRD/HU"]
    out += [f"WARN rule {i} is cited nowhere (cite it in a requirement, or in Out of Scope with the reason)" for i in missing]
    return "\n".join(out)


def main(argv):
    if argv[1:] == ["--list"]:
        for k, (when, fails, fixed) in CHECKS.items():
            print(f"{k}\n  passes when: {when}\n  fails when:  {fails}\n  fixed in:    {fixed}")
        return 0
    try:
        cmd, folder = argv[1], Path(argv[2])
        if not folder.is_dir():
            raise FileNotFoundError(folder)
        if cmd == "gate":
            rep = gate(folder, argv[3])
            if rep is None:
                raise ValueError(f"unknown gate {argv[3]}")
            print(rep.render(f"Gate {argv[3]} — {folder.name}"))
            return 1 if rep.fails else 0
        if cmd == "status":
            print(status(folder))
            return 0
        if cmd == "trace" and argv[3] == "--eventstorm":
            print(trace(folder, argv[4]))
            return 0
        raise ValueError("usage")
    except (IndexError, ValueError, FileNotFoundError, OSError) as e:
        print(f"error: {e}\n" + __doc__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
