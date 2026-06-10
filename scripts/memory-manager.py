#!/usr/bin/env python3
"""
BLD PM Agents Pipeline — Memory Manager
Manages agent memory files to prevent hallucination and context bloat.

Commands:
  python3 memory-manager.py status        — show all agent memories + sizes
  python3 memory-manager.py clean         — prune entries older than MAX_AGE_DAYS
  python3 memory-manager.py reset <agent> — wipe a single agent's memory
  python3 memory-manager.py reset --all   — wipe all agent memories (asks for confirmation)
"""

import os, sys, re, glob
from datetime import datetime, timedelta
from pathlib import Path

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[38;5;71m"
BLUE   = "\033[38;5;75m"
YELLOW = "\033[38;5;220m"
RED    = "\033[38;5;203m"
PURPLE = "\033[38;5;135m"
GREY   = "\033[38;5;245m"

MEMORY_DIR   = Path.home() / ".claude" / "agent-memory"
MAX_AGE_DAYS = 90      # entries older than this get pruned on clean
WARN_TOKENS  = 1500    # warn if estimated tokens in a file exceed this
MAX_TOKENS   = 3000    # hard limit — force summarization above this

AGENTS = [
    # Discovery
    "bld-market-trends", "bld-cx-insights", "bld-idea-tank", "bld-discovery-synthesis",
    # Product Definition
    "bld-pr-agent", "bld-prd-agent", "bld-hu-agent",
    # Strategic
    "bld-kr-compass", "bld-roadmap-guardian", "bld-dependency-radar",
    # Execution
    "bld-pm-orchestrator", "bld-dev-agent", "bld-qa-agent", "bld-docs-agent",
    # Support
    "bld-ux-ui-agent", "bld-stakeholder-comms-agent",
]

MEMORY_TEMPLATE = """\
# {agent} — Agent Memory
# Best practices:
#   - Keep total size under ~3000 tokens (~12KB)
#   - Date-stamp every entry: [YYYY-MM-DD]
#   - Use sections: FACTS | DECISIONS | LEARNINGS | ACTIVE_CONTEXT
#   - Clean entries older than 90 days (run: python3 memory-manager.py clean)

## FACTS
# Permanent truths about this agent's domain. Update in place, don't append.
# Example: [2026-06-10] ClickUp workspace ID = XXXXX

## DECISIONS
# Key decisions made that affect this agent's behavior. Date-stamped, never delete.
# Example: [2026-06-10] Audit trail required on all ClickUp comments — PM approval needed

## LEARNINGS
# Patterns, mistakes, and insights discovered during operation. Prune after 90 days.
# Example: [2026-06-10] Stakeholder X prefers Slack DM over email for feedback requests

## ACTIVE_CONTEXT
# Current sprint/quarter state. Overwrite each sprint — do NOT accumulate.
# Max 10 lines. Everything here is assumed current.
# Example: Current quarter: Q3-2026 | Sprint: Sprint 12 | KR focus: Revenue +20%
"""


def estimate_tokens(text):
    # rough estimate: ~4 chars per token
    return len(text) // 4


def health_color(tokens):
    if tokens > MAX_TOKENS:
        return RED
    if tokens > WARN_TOKENS:
        return YELLOW
    return GREEN


def health_label(tokens):
    if tokens > MAX_TOKENS:
        return "OVER LIMIT — must clean"
    if tokens > WARN_TOKENS:
        return "WARNING — approaching limit"
    return "OK"


def ensure_memory_dir():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def get_memory_path(agent):
    return MEMORY_DIR / f"{agent}.md"


def init_agent_memory(agent):
    path = get_memory_path(agent)
    if not path.exists():
        path.write_text(MEMORY_TEMPLATE.format(agent=agent))
        return True
    return False


def cmd_status():
    ensure_memory_dir()
    print()
    print(f"{BOLD}{'═' * 72}{RESET}")
    print(f"{BOLD}   BLD Agent Memory Status{RESET}")
    print(f"{GREY}   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  MAX: {MAX_TOKENS} tokens  |  WARN: {WARN_TOKENS} tokens{RESET}")
    print(f"{BOLD}{'═' * 72}{RESET}")

    layers = {
        "🔭 Discovery":          AGENTS[:4],
        "📋 Product Definition": AGENTS[4:7],
        "🧭 Strategic":          AGENTS[7:10],
        "⚙️  Execution":          AGENTS[10:14],
        "🤝 Support":            AGENTS[14:],
    }

    total_tokens = 0
    missing = []

    for layer_name, agents in layers.items():
        print()
        print(f"  {BOLD}{layer_name}{RESET}")
        print(f"  {'─' * 68}")
        for agent in agents:
            path = get_memory_path(agent)
            if not path.exists():
                print(f"  {GREY}{agent:<40} {'— not initialized':>20}{RESET}")
                missing.append(agent)
                continue
            content = path.read_text()
            tokens = estimate_tokens(content)
            size_kb = path.stat().st_size / 1024
            total_tokens += tokens
            color = health_color(tokens)
            label = health_label(tokens)
            bar_filled = min(int(tokens / MAX_TOKENS * 20), 20)
            b = f"{color}{'█' * bar_filled}{GREY}{'░' * (20 - bar_filled)}{RESET}"
            print(f"  {agent:<40} {b} {color}{tokens:>5} tok{RESET}  {DIM}{size_kb:.1f}KB{RESET}  {DIM}{label}{RESET}")

    print()
    print(f"  {BOLD}Total estimated tokens in memory:{RESET} {health_color(total_tokens)}{total_tokens}{RESET}")
    if missing:
        print(f"  {YELLOW}{len(missing)} agents have no memory file yet — run: python3 memory-manager.py init{RESET}")
    print()
    print(f"{BOLD}{'═' * 72}{RESET}")

    # Best practice tips
    print()
    print(f"{BOLD}  Memory Management Best Practices{RESET}")
    print(f"  {'─' * 68}")
    tips = [
        ("FACTS section",      "Permanent truths. Update in-place. Never grows unbounded."),
        ("DECISIONS section",  "Key behavioral decisions. Keep forever. Date-stamped."),
        ("LEARNINGS section",  "Observations from operation. Prune entries > 90 days old."),
        ("ACTIVE_CONTEXT",     "Current sprint/quarter state. Overwrite each sprint (max 10 lines)."),
        ("Clean regularly",    f"Run `clean` command to prune entries older than {MAX_AGE_DAYS} days."),
        ("No conversation log","Memory ≠ chat history. Only facts, decisions, learnings."),
        ("Structured entries", "Always prefix with [YYYY-MM-DD] for date-based pruning."),
    ]
    for label, tip in tips:
        print(f"  {BLUE}{label:<22}{RESET} {tip}")
    print()


def cmd_init():
    ensure_memory_dir()
    created = 0
    for agent in AGENTS:
        if init_agent_memory(agent):
            print(f"  {GREEN}✓{RESET} Created memory file for {agent}")
            created += 1
        else:
            print(f"  {GREY}─{RESET} {agent} already has a memory file")
    print()
    if created:
        print(f"  {GREEN}Initialized {created} new agent memory files in {MEMORY_DIR}{RESET}")
    else:
        print(f"  {GREY}All agent memory files already exist.{RESET}")
    print()


def cmd_clean():
    ensure_memory_dir()
    cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)
    cutoff_str = cutoff.strftime("%Y-%m-%d")
    date_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2})\]')

    print()
    print(f"  {BOLD}Pruning entries older than {MAX_AGE_DAYS} days (before {cutoff_str}){RESET}")
    print()

    total_removed = 0
    for agent in AGENTS:
        path = get_memory_path(agent)
        if not path.exists():
            continue

        lines = path.read_text().splitlines()
        new_lines = []
        removed = 0
        for line in lines:
            m = date_pattern.search(line)
            if m:
                entry_date = datetime.strptime(m.group(1), "%Y-%m-%d")
                if entry_date < cutoff:
                    # only prune from LEARNINGS section (not FACTS or DECISIONS)
                    # simple heuristic: if line starts with # or is in a section header, keep it
                    if not line.strip().startswith("#") and "LEARNINGS" not in line:
                        removed += 1
                        total_removed += 1
                        continue
            new_lines.append(line)

        if removed > 0:
            path.write_text("\n".join(new_lines) + "\n")
            print(f"  {YELLOW}{agent:<40}{RESET} removed {removed} old entries")
        else:
            print(f"  {GREY}{agent:<40}{RESET} nothing to prune")

    print()
    if total_removed:
        print(f"  {GREEN}Done. Removed {total_removed} entries older than {cutoff_str}.{RESET}")
    else:
        print(f"  {GREEN}All memory files are clean.{RESET}")
    print()


def cmd_reset(target):
    ensure_memory_dir()
    if target == "--all":
        confirm = input(f"  {RED}Reset ALL agent memories? This cannot be undone. Type 'yes' to confirm: {RESET}")
        if confirm.strip().lower() != "yes":
            print("  Aborted.")
            return
        for agent in AGENTS:
            path = get_memory_path(agent)
            path.write_text(MEMORY_TEMPLATE.format(agent=agent))
            print(f"  {YELLOW}Reset{RESET} {agent}")
        print(f"\n  {GREEN}All agent memories reset.{RESET}\n")
    else:
        if target not in AGENTS:
            print(f"  {RED}Unknown agent: {target}{RESET}")
            print(f"  Available: {', '.join(AGENTS)}")
            return
        path = get_memory_path(target)
        confirm = input(f"  {YELLOW}Reset memory for {target}? Type 'yes' to confirm: {RESET}")
        if confirm.strip().lower() != "yes":
            print("  Aborted.")
            return
        path.write_text(MEMORY_TEMPLATE.format(agent=target))
        print(f"  {GREEN}Memory reset for {target}.{RESET}\n")


def usage():
    print(f"""
  {BOLD}BLD Memory Manager — Commands{RESET}

  {BLUE}python3 memory-manager.py status{RESET}         Show all agent memory sizes and health
  {BLUE}python3 memory-manager.py init{RESET}           Create memory files for all agents
  {BLUE}python3 memory-manager.py clean{RESET}          Prune LEARNINGS entries older than {MAX_AGE_DAYS} days
  {BLUE}python3 memory-manager.py reset <agent>{RESET}  Wipe one agent's memory
  {BLUE}python3 memory-manager.py reset --all{RESET}    Wipe all agent memories (asks confirmation)
""")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "status":
        cmd_status()
    elif args[0] == "init":
        cmd_init()
    elif args[0] == "clean":
        cmd_clean()
    elif args[0] == "reset" and len(args) >= 2:
        cmd_reset(args[1])
    else:
        usage()
