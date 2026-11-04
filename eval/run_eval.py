"""Score the prompt against a hand-made answer key, and measure run-to-run stability.

    python3 eval/run_eval.py                 # score every notice in the key, one run each
    python3 eval/run_eval.py --runs 3        # also report stability across 3 runs
    python3 eval/run_eval.py --file 21_04939_FUL--3474437.pdf

Correctness answers "is it right?". Stability answers "does it say the same thing twice?".
Both matter: a prompt change that raises the score by luck shows up as instability here.
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from ct import extract, logic  # noqa: E402
from ct.config import cost_usd  # noqa: E402

KEY_PATH = os.path.join(ROOT, "eval", "answer_key.json")
CLIENT = extract.get_client()


def analyse(path):
    """Exactly the pipeline the app uses (ct.extract.extract): text, or vision for scans,
    with the same retry-on-truncation-or-bad-JSON policy and the same model settings."""
    with open(path, "rb") as f:
        return extract.extract(f.read(), CLIENT)


def score(data, asserted, contested):
    """Return (checks, failures). Contested condition numbers are skipped, not failed."""
    checks, fails = [], []
    skip = {int(k) for k in contested}
    by_num = {c["condition_number"]: c for c in data.get("conditions", [])}

    def check(name, got, want):
        ok = got == want
        checks.append(ok)
        if not ok:
            fails.append(f"{name}: got {got!r}, expected {want!r}")

    for field in ("document_type", "jurisdiction", "is_householder", "decision", "time_limit_years",
                  "permission_type", "application_reference", "local_authority"):
        if field in asserted:
            check(field, data.get(field), asserted[field])

    if "condition_count" in asserted:
        check("condition_count", len(data.get("conditions", [])), asserted["condition_count"])

    if "begin_by" in asserted:
        bb = logic.start_deadline(data)["date"]
        check("begin_by", bb.isoformat() if bb else None, asserted["begin_by"])

    for num, want in asserted.get("gates", {}).items():
        if int(num) in skip:
            continue
        check(f"#{num} gate", (by_num.get(int(num)) or {}).get("gate"), want)

    if "gate_ambiguous" in asserted:
        got = sorted(c["condition_number"] for c in data.get("conditions", [])
                     if c.get("gate_ambiguous") and c["condition_number"] not in skip)
        want = sorted(n for n in asserted["gate_ambiguous"] if n not in skip)
        check("gate_ambiguous set", got, want)

    if "flags" in asserted:
        want_flags = asserted["flags"]
        got_flags = logic.get_flags(data)
        check("flag count", len(got_flags), want_flags["count"])
        for spec in want_flags.get("must_include", []):
            hit = any(
                f.get("type") == spec["type"]
                and spec["detail_contains"].lower() in (f.get("detail") or "").lower()
                and (spec.get("condition") is None or f.get("condition") == spec["condition"])
                for f in got_flags
            )
            checks.append(hit)
            if not hit:
                fails.append(f"missing flag: {spec['type']} containing {spec['detail_contains']!r}")

    for num, want in asserted.get("specialists", {}).items():
        if int(num) in skip:
            continue
        got = logic.specialists_for(by_num.get(int(num)) or {})
        check(f"#{num} specialist", sorted(got), sorted(want))

    for num in asserted.get("specialist_is_empty", []):
        if num in skip:
            continue
        got = logic.specialists_for(by_num.get(num) or {})
        checks.append(got == [])
        if got:
            fails.append(f"#{num} specialist: got {got!r}, expected none (in-house)")

    return checks, fails


def fingerprint(data):
    """The values we care about staying stable between identical runs."""
    fp = {f"top.{k}": data.get(k) for k in
          ("document_type", "jurisdiction", "is_householder", "decision", "time_limit_years")}
    fp["top.condition_count"] = len(data.get("conditions", []))
    fp["top.flags"] = sorted(f"{f.get('type')}:{f.get('condition')}" for f in logic.get_flags(data))
    for c in data.get("conditions", []):
        n = c["condition_number"]
        fp[f"#{n}.gate"] = c.get("gate")
        fp[f"#{n}.ambiguous"] = c.get("gate_ambiguous")
        fp[f"#{n}.discharge"] = c.get("discharge_required")
        fp[f"#{n}.specialist"] = sorted(logic.specialists_for(c))
    return fp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--file")
    ap.add_argument("--save", help="write each analysis to this folder as JSON (fixtures for tests)")
    ap.add_argument("--jobs", type=int, default=1, help="notices to analyse in parallel")
    args = ap.parse_args()

    key = json.load(open(KEY_PATH))
    targets = [k for k in key if not k.startswith("_")]
    if args.file:
        targets = [t for t in targets if t == args.file] or sys.exit(f"{args.file} not in the key")

    # Analyse everything up front (optionally in parallel), then report in order.
    from concurrent.futures import ThreadPoolExecutor
    jobs = [(name, i) for name in targets for i in range(args.runs)]
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(lambda j: analyse(os.path.join(ROOT, j[0])), jobs))
    by_name = defaultdict(list)
    for (name, _), data in zip(jobs, results):
        by_name[name].append(data)

    if args.save:
        os.makedirs(args.save, exist_ok=True)
        for name, runs in by_name.items():
            with open(os.path.join(args.save, name.replace(".pdf", ".json")), "w") as f:
                json.dump(runs[0], f, indent=2, ensure_ascii=False)

    grand_ok = grand_total = 0
    total_cost = 0.0
    for name in targets:
        entry = key[name]
        asserted, contested = entry.get("asserted", {}), entry.get("contested", {})
        print("=" * 78)
        print(name)
        print("=" * 78)

        runs = by_name[name]
        run_costs = [cost_usd(r.get("_usage")) for r in runs]
        total_cost += sum(run_costs)
        u = runs[0].get("_usage") or {}
        print(f"  COST         ${run_costs[0]:.3f} per run "
              f"({u.get('input_tokens', 0):,} in / {u.get('output_tokens', 0):,} out tokens)")

        checks, fails = score(runs[0], asserted, contested)
        ok, total = sum(checks), len(checks)
        grand_ok += ok
        grand_total += total
        pct = 100 * ok / total if total else 0
        print(f"  CORRECTNESS  {ok}/{total}  ({pct:.0f}%)   [{len(contested)} contested, not scored]")
        for f in fails:
            print(f"     FAIL  {f}")

        if args.runs > 1:
            fps = [fingerprint(r) for r in runs]
            fields = sorted({k for fp in fps for k in fp})
            unstable = defaultdict(list)
            for f in fields:
                vals = [fp.get(f) for fp in fps]
                if len(set(map(repr, vals))) > 1:
                    unstable[f] = vals
            stable = len(fields) - len(unstable)
            print(f"  STABILITY    {stable}/{len(fields)} fields identical across "
                  f"{args.runs} runs ({100 * stable / len(fields):.1f}%)")
            for f, vals in sorted(unstable.items()):
                counts = Counter(map(repr, vals))
                print(f"     DRIFT {f}: " + "  ".join(f"{v}x{c}" for v, c in counts.items()))
            if not unstable:
                print("     no drift — every field identical across runs")

        if contested:
            print("  CONTESTED (decide these, then move them into asserted):")
            for num, why in sorted(contested.items(), key=lambda kv: int(kv[0])):
                print(f"     #{num}  {why}")
        print()

    if grand_total:
        print("=" * 78)
        print(f"TOTAL CORRECTNESS  {grand_ok}/{grand_total}  ({100 * grand_ok / grand_total:.0f}%)")
        print(f"TOTAL COST         ${total_cost:.2f} for {len(jobs)} analyses "
              f"(${total_cost / max(1, len(jobs)):.3f} average)")
    return 0 if grand_ok == grand_total else 1


if __name__ == "__main__":
    sys.exit(main())
