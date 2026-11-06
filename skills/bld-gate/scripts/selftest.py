#!/usr/bin/env python3
"""selftest.py — run after editing bld_gate.py or the templates the gates parse.

fixtures/ok  : every gate must exit 0.
fixtures/bad : every gate must exit 1, and the expected checks must all appear as FAIL.
Prints OK or the first mismatch; exit 0 / 1.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE.parent / "assets" / "fixtures"
GATE = HERE / "bld_gate.py"
EXPECT_BAD = {
    "to-pr": {"approvals", "open-items", "decisions"},
    "to-prd": {"approvals", "placeholders", "proposed-tags"},
    "to-comms": {"review"},
    "to-hu": {"tracker", "review"},
    "hu-catalog": {"hu-fields", "hu-trace", "hu-deps"},
}


def run(folder, gate):
    p = subprocess.run([sys.executable, str(GATE), "gate", str(folder), gate], capture_output=True, text=True)
    return p.returncode, {ln.split()[1].rstrip(":") for ln in p.stdout.splitlines() if ln.startswith("FAIL ")}


def main():
    for gate, expected in EXPECT_BAD.items():
        code, fails = run(FIX / "ok", gate)
        if code != 0:
            return print(f"MISMATCH ok/{gate}: exit {code}, fails {sorted(fails)}") or 1
        code, fails = run(FIX / "bad", gate)
        if code != 1 or not expected <= fails:
            return print(f"MISMATCH bad/{gate}: exit {code}, expected {sorted(expected)}, got {sorted(fails)}") or 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
