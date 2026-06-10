#!/usr/bin/env python3
"""
BLD PM Agents Pipeline — Token & Cost Console
Reads real usage from Claude Code session files.
Usage: python3 ~/.claude/scripts/costs.py [--all]
"""

import json, os, sys, glob
from datetime import datetime, timezone
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

# ── Pricing per 1M tokens (Sonnet 4.6) ──────────────────────────────────────
PRICING = {
    "claude-sonnet-4-6": {
        "input":          3.00,
        "output":        15.00,
        "cache_create":   3.75,   # 25% more than input
        "cache_read":     0.30,   # 90% less than input
    },
    "claude-opus-4-8": {
        "input":          5.00,
        "output":        25.00,
        "cache_create":   6.25,
        "cache_read":     0.50,
    },
    "claude-haiku-4-5": {
        "input":          1.00,
        "output":         5.00,
        "cache_create":   1.25,
        "cache_read":     0.10,
    },
}
DEFAULT_PRICE = PRICING["claude-sonnet-4-6"]

CLAUDE_DIR = Path.home() / ".claude"
BLD_PROJECT_DIR = CLAUDE_DIR / "projects" / "-Users-juandavid-Documents-Claude-PM--agents-work-pipeline"


def calc_cost(usage, model):
    p = PRICING.get(model, DEFAULT_PRICE)
    cost = (
        usage.get("input_tokens", 0)                * p["input"]        / 1_000_000 +
        usage.get("output_tokens", 0)               * p["output"]       / 1_000_000 +
        usage.get("cache_creation_input_tokens", 0) * p["cache_create"] / 1_000_000 +
        usage.get("cache_read_input_tokens", 0)     * p["cache_read"]   / 1_000_000
    )
    return cost


def parse_session(path):
    totals = {
        "input": 0, "output": 0,
        "cache_create": 0, "cache_read": 0,
        "cost": 0.0, "messages": 0,
        "model": "unknown", "session_id": Path(path).stem,
        "first_ts": None, "last_ts": None,
    }
    seen_ids = set()
    try:
        with open(path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # track timestamps
                ts = entry.get("timestamp")
                if ts:
                    if totals["first_ts"] is None or ts < totals["first_ts"]:
                        totals["first_ts"] = ts
                    if totals["last_ts"] is None or ts > totals["last_ts"]:
                        totals["last_ts"] = ts

                msg = entry.get("message", {})
                msg_id = msg.get("id")
                if not msg_id or msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)

                usage = msg.get("usage")
                if not usage:
                    continue

                model = msg.get("model", "claude-sonnet-4-6")
                totals["model"] = model
                totals["input"]        += usage.get("input_tokens", 0)
                totals["output"]       += usage.get("output_tokens", 0)
                totals["cache_create"] += usage.get("cache_creation_input_tokens", 0)
                totals["cache_read"]   += usage.get("cache_read_input_tokens", 0)
                totals["cost"]         += calc_cost(usage, model)
                totals["messages"]     += 1
    except Exception:
        pass
    return totals


def fmt_ts(ms):
    if not ms:
        return "—"
    try:
        return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "—"


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def bar(value, max_value, width=20, color=GREEN):
    filled = int((value / max_value) * width) if max_value else 0
    return f"{color}{'█' * filled}{GREY}{'░' * (width - filled)}{RESET}"


def print_section(title, color):
    print()
    print(f"{color}{BOLD}{'━' * 78}{RESET}")
    print(f"{color}{BOLD}  {title}{RESET}")
    print(f"{color}{'━' * 78}{RESET}")


def main():
    show_all = "--all" in sys.argv

    print()
    print(f"{BOLD}{'═' * 78}{RESET}")
    print(f"{BOLD}   BLD PM AGENTS PIPELINE  —  Token & Cost Console{RESET}")
    print(f"{GREY}   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BOLD}{'═' * 78}{RESET}")

    # ── BLD Project Sessions ─────────────────────────────────────────────────
    print_section("📁  BLD PROJECT SESSIONS", BLUE)

    session_files = sorted(glob.glob(str(BLD_PROJECT_DIR / "*.jsonl")))
    if not session_files:
        print(f"  {RED}No session files found in BLD project directory.{RESET}")
    else:
        project_total = {"input": 0, "output": 0, "cache_create": 0, "cache_read": 0, "cost": 0.0, "messages": 0}
        sessions_data = []

        for path in session_files:
            s = parse_session(path)
            sessions_data.append(s)
            for k in ["input", "output", "cache_create", "cache_read", "messages"]:
                project_total[k] += s[k]
            project_total["cost"] += s["cost"]

        # table header
        print(f"  {BOLD}{'Session':<38} {'Start':<17} {'Msgs':>4} {'Tokens':>10} {'Cost':>9}{RESET}")
        print(f"  {'─' * 75}")

        for s in sessions_data:
            total_tokens = s["input"] + s["output"] + s["cache_create"] + s["cache_read"]
            sid = s["session_id"][:36]
            print(f"  {GREY}{sid:<38}{RESET} {fmt_ts(s['first_ts']):<17} "
                  f"{s['messages']:>4} {fmt_tokens(total_tokens):>10} "
                  f"{YELLOW}${s['cost']:>7.4f}{RESET}")

        print(f"  {'─' * 75}")
        total_t = project_total["input"] + project_total["output"] + project_total["cache_create"] + project_total["cache_read"]
        print(f"  {BOLD}{'TOTAL':<38} {'':17} {project_total['messages']:>4} {fmt_tokens(total_t):>10} "
              f"{GREEN}${project_total['cost']:>7.4f}{RESET}")

    # ── Token Breakdown ───────────────────────────────────────────────────────
    if session_files:
        print_section("🔢  TOKEN BREAKDOWN (BLD PROJECT)", PURPLE)

        pt = project_total
        grand = pt["input"] + pt["output"] + pt["cache_create"] + pt["cache_read"]
        if grand == 0:
            grand = 1  # avoid div/0

        rows = [
            ("Input tokens",        pt["input"],        DEFAULT_PRICE["input"],        BLUE),
            ("Output tokens",       pt["output"],       DEFAULT_PRICE["output"],       GREEN),
            ("Cache create tokens", pt["cache_create"], DEFAULT_PRICE["cache_create"], YELLOW),
            ("Cache read tokens",   pt["cache_read"],   DEFAULT_PRICE["cache_read"],   GREY),
        ]

        for label, count, price, color in rows:
            cost = count * price / 1_000_000
            pct = count / grand * 100
            b = bar(count, grand, 24, color)
            print(f"  {label:<22} {b} {fmt_tokens(count):>8}  {DIM}(${price:.2f}/1M){RESET}  {YELLOW}${cost:.4f}{RESET}")

        print()
        print(f"  {BOLD}Cache efficiency:{RESET}  "
              f"{GREEN}{pt['cache_read'] / max(pt['input'] + pt['cache_read'], 1) * 100:.1f}% tokens served from cache{RESET}  "
              f"{GREY}(saves ~90% on read vs input price){RESET}")

    # ── All Projects Summary ──────────────────────────────────────────────────
    if show_all:
        print_section("🌐  ALL PROJECTS SUMMARY", GREY)
        all_projects = sorted(glob.glob(str(CLAUDE_DIR / "projects" / "*" / "*.jsonl")))
        proj_map = {}
        for path in all_projects:
            proj = Path(path).parent.name
            s = parse_session(path)
            if proj not in proj_map:
                proj_map[proj] = {"cost": 0.0, "input": 0, "output": 0, "sessions": 0}
            proj_map[proj]["cost"]    += s["cost"]
            proj_map[proj]["input"]   += s["input"]
            proj_map[proj]["output"]  += s["output"]
            proj_map[proj]["sessions"] += 1

        sorted_proj = sorted(proj_map.items(), key=lambda x: x[1]["cost"], reverse=True)
        max_cost = sorted_proj[0][1]["cost"] if sorted_proj else 1

        print(f"  {BOLD}{'Project':<52} {'Sessions':>8} {'Cost':>9}{RESET}")
        print(f"  {'─' * 75}")
        grand_total = 0
        for proj, data in sorted_proj:
            display = proj.replace("-Users-juandavid-", "~/").replace("-", "/")[:50]
            b = bar(data["cost"], max_cost, 12, YELLOW)
            print(f"  {display:<52} {data['sessions']:>8} {YELLOW}${data['cost']:>7.4f}{RESET}")
            grand_total += data["cost"]
        print(f"  {'─' * 75}")
        print(f"  {BOLD}{'ALL PROJECTS TOTAL':<52} {len(all_projects):>8} {GREEN}${grand_total:>7.4f}{RESET}")

    # ── Pricing Reference ─────────────────────────────────────────────────────
    print_section("💰  PRICING REFERENCE", YELLOW)
    print(f"  {BOLD}{'Model':<22} {'Input':>10} {'Output':>10} {'Cache Create':>14} {'Cache Read':>11}{RESET}")
    print(f"  {'─' * 72}")
    for model, p in PRICING.items():
        print(f"  {model:<22} ${p['input']:>8.2f}/M  ${p['output']:>8.2f}/M  "
              f"${p['cache_create']:>12.2f}/M  ${p['cache_read']:>9.2f}/M")

    print()
    print(f"  {DIM}Tip: run with --all to see cost breakdown across all Claude Code projects{RESET}")
    print()
    print(f"{BOLD}{'═' * 78}{RESET}")
    print()


if __name__ == "__main__":
    main()
