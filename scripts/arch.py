#!/usr/bin/env python3
"""
BLD PM Agents Pipeline — Architecture Console
Usage: python3 ~/.claude/scripts/arch.py
"""

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

# Layer colors
C_DISC = "\033[38;5;135m"   # purple  — Discovery
C_DEFN = "\033[38;5;39m"    # blue    — Product Definition
C_STRAT= "\033[38;5;75m"    # sky     — Strategic
C_EXEC = "\033[38;5;71m"    # green   — Execution
C_INTG = "\033[38;5;203m"   # red     — Integrations
C_GATE = "\033[38;5;220m"   # yellow  — Gates
C_FLOW = "\033[38;5;245m"   # grey    — Arrows/lines

def box(label, agent, color, width=38):
    pad = width - len(agent) - 2
    left = pad // 2
    right = pad - left
    top    = f"{color}┌{'─' * (width)}┐{RESET}"
    mid    = f"{color}│{' ' * left}{BOLD}{agent}{RESET}{color}{' ' * right}│{RESET}"
    bottom = f"{color}└{'─' * (width)}┘{RESET}"
    lbl    = f"{DIM}{label.center(width + 2)}{RESET}"
    return [top, mid, bottom, lbl]

def gate(text):
    return f"{C_GATE}{'─' * 12} {BOLD}{text}{RESET}{C_GATE} {'─' * 12}{RESET}"

def arrow(text=""):
    prefix = f"          {C_FLOW}│{RESET}"
    label  = f"          {C_FLOW}▼{RESET}  {DIM}{text}{RESET}" if text else f"          {C_FLOW}▼{RESET}"
    return [prefix, label]

def hline(agents_row, color):
    return f"{color}{'  '.join(['─' * 40] * len(agents_row))}{RESET}"

def print_layer_header(name, color):
    width = 80
    print()
    print(f"{color}{BOLD}{'━' * width}{RESET}")
    print(f"{color}{BOLD}  {name}{RESET}")
    print(f"{color}{'━' * width}{RESET}")

def print_row(boxes_lines):
    max_h = max(len(b) for b in boxes_lines)
    for i in range(max_h):
        row = ""
        for b in boxes_lines:
            line = b[i] if i < len(b) else ""
            row += line + "   "
        print(row)

def main():
    print()
    print(f"{BOLD}{'═' * 82}{RESET}")
    print(f"{BOLD}   BLD PM AGENTS PIPELINE  —  Architecture Overview{RESET}")
    print(f"{BOLD}{'═' * 82}{RESET}")

    # ── DISCOVERY LAYER ──────────────────────────────────────────────────────
    print_layer_header("🔭  DISCOVERY LAYER", C_DISC)
    row1 = [
        box("1. Market Intel",    "bld-market-trends",      C_DISC),
        box("2. CX & Surveys",    "bld-cx-insights",        C_DISC),
        box("3. Ideas & Proposals","bld-idea-tank",          C_DISC),
    ]
    print_row(row1)
    print(f"\n                    {C_FLOW}└──────────┬──────────┘{RESET}")
    print(f"                               {C_FLOW}▼{RESET}")
    print(f"          {box('4. Synthesis & Opportunity Brief', 'bld-discovery-synthesis', C_DISC)[0]}")
    print(f"          {box('4. Synthesis & Opportunity Brief', 'bld-discovery-synthesis', C_DISC)[1]}")
    print(f"          {box('4. Synthesis & Opportunity Brief', 'bld-discovery-synthesis', C_DISC)[2]}")
    print()
    print(f"               {gate('🔐 GATE: C-level approves Opportunity Brief')}")

    # ── PRODUCT DEFINITION LAYER ─────────────────────────────────────────────
    print_layer_header("📋  PRODUCT DEFINITION LAYER", C_DEFN)
    for a, label, extra in [
        ("bld-pr-agent",  "5. Press Release & FAQ",          f"  {C_GATE}▶ Gate: C-level + PM ✅{RESET}"),
        ("bld-prd-agent", "6. PRD (12-area review cycles)",  f"  {C_GATE}▶ Gate: All areas + C-level ✅{RESET}"),
        ("bld-hu-agent",  "7. User Stories → ADO",           f"  {DIM}UX/UI section included{RESET}"),
    ]:
        b = box(label, a, C_DEFN)
        print(f"  {b[0]}{extra}")
        print(f"  {b[1]}")
        print(f"  {b[2]}")
        print(f"  {b[3]}")
        if a != "bld-hu-agent":
            print(f"            {C_FLOW}▼{RESET}")
    print()
    print(f"               {gate('🔐 GATE: Full PRD approval unlocks HU generation')}")

    # ── STRATEGIC LAYER ───────────────────────────────────────────────────────
    print_layer_header("🧭  STRATEGIC LAYER", C_STRAT)
    row2 = [
        box("KR Guardian",        "bld-kr-compass",          C_STRAT),
        box("Roadmap Governor",   "bld-roadmap-guardian",    C_STRAT),
        box("Weekly Dep. Scanner","bld-dependency-radar",    C_STRAT),
    ]
    print_row(row2)
    print(f"\n  {DIM}kr-compass feeds KR status → roadmap-guardian every sprint{RESET}")
    print(f"  {DIM}dependency-radar reports blockers every Monday{RESET}")

    # ── EXECUTION PIPELINE ───────────────────────────────────────────────────
    print_layer_header("⚙️   EXECUTION PIPELINE", C_EXEC)
    print(f"  {box('Sprint Planning & Delegation', 'bld-pm-orchestrator', C_EXEC)[0]}")
    print(f"  {box('Sprint Planning & Delegation', 'bld-pm-orchestrator', C_EXEC)[1]}")
    print(f"  {box('Sprint Planning & Delegation', 'bld-pm-orchestrator', C_EXEC)[2]}")
    print(f"            {C_FLOW}┌──────────┼──────────┐{RESET}")
    print(f"            {C_FLOW}▼          ▼          ▼{RESET}")
    row3 = [
        box("Feature impl.",  "bld-dev-agent",   C_EXEC),
        box("Validation",     "bld-qa-agent",    C_EXEC),
        box("Docs & Changelog","bld-docs-agent", C_EXEC),
    ]
    print_row(row3)

    # ── SUPPORT AGENTS ───────────────────────────────────────────────────────
    print_layer_header("🤝  SUPPORT AGENTS", C_INTG)
    row4 = [
        box("UX/UI Review & Figma", "bld-ux-ui-agent",           C_INTG),
        box("Stakeholder Comms",    "bld-stakeholder-comms-agent",C_INTG),
    ]
    print_row(row4)
    print(f"\n  {DIM}ux-ui-agent: signs off PRD UX/UI section, iterates wireframes{RESET}")
    print(f"  {DIM}stakeholder-comms: Gmail + Slack → collects feedback → Coda sub-sheets{RESET}")

    # ── INTEGRATIONS ─────────────────────────────────────────────────────────
    print_layer_header("🔗  INTEGRATIONS", C_INTG)
    integrations = [
        ("ClickUp",      "Backlog & Sprints",         "Read + Write (PM-gated)"),
        ("Azure DevOps", "CI/CD & Work Items",        "Read + Write (PM-gated)"),
        ("Google Drive", "Meeting Transcripts",       "Read"),
        ("Gmail",        "Stakeholder Comms",         "Read + Send (PM-gated)"),
        ("Slack",        "Notifications & Comms",     "Read + Send (PM-gated)"),
        ("Coda",         "Feedback Sub-sheets",       "Read + Write (PM-gated)"),
        ("Figma",        "UX/UI Designs",             "Read"),
        ("Lovify",       "KR Data Feed",              "Read (future)"),
    ]
    print(f"  {BOLD}{'System':<16} {'Purpose':<28} {'Access'}{RESET}")
    print(f"  {'─' * 68}")
    for name, purpose, access in integrations:
        print(f"  {C_INTG}{name:<16}{RESET} {purpose:<28} {DIM}{access}{RESET}")

    print()
    print(f"{BOLD}{'═' * 82}{RESET}")
    print(f"  {DIM}16 agents  |  4 layers  |  2 approval gates  |  8 integrations{RESET}")
    print(f"{BOLD}{'═' * 82}{RESET}")
    print()

if __name__ == "__main__":
    main()
