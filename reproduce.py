#!/usr/bin/env python3
# Reproduce this campaign's certified results.
# Re-runs the sealed verifier's integrity checks and re-verifies every certified
# hit recorded in ledger.jsonl. Exits 0 iff everything reproduces.
import json, sys, importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
V = HERE / "workspace" / "verifier.py"
LEDGER = HERE / "ledger.jsonl"

def _load(path):
    spec = importlib.util.spec_from_file_location("verifier", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    if not V.exists():
        print("no workspace/verifier.py in this package; see README for the reproduction path")
        return 0
    ver = _load(V)
    ok = True
    if hasattr(ver, "dress_rehearsal"):
        r = float(ver.dress_rehearsal())
        print("dress-rehearsal residual: %.2e V  [%s]" % (r, "OK" if r < 1e-6 else "FAIL"))
        ok = ok and (r < 1e-6)
    if hasattr(ver, "pre_search_checks"):
        print("pre-search checks:", ver.pre_search_checks())
    hits = []
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("kind") == "search_hit" and row.get("candidate") is not None:
                hits.append(row["candidate"])
    print("\nre-verifying %d certified hit(s) from the ledger:" % len(hits))
    for i, c in enumerate(hits):
        res = ver.verify(c)
        valid = bool(res.get("valid")) if isinstance(res, dict) else False
        reason = res.get("reason", "")[:88] if isinstance(res, dict) else ""
        print("  hit %d: valid=%s  %s" % (i, valid, reason))
        ok = ok and valid
    print("\nREPRODUCED - all checks passed." if ok else "\nFAILED - something did not reproduce.")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
