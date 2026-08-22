"""Score the prompt against a hand-made answer key, and measure run-to-run stability.

    python3 eval/run_eval.py                 # score every notice in the key, one run each
    python3 eval/run_eval.py --runs 3        # also report stability across 3 runs
    python3 eval/run_eval.py --file 21_04939_FUL--3474437.pdf

Correctness answers "is it right?". Stability answers "does it say the same thing twice?".
Both matter: a prompt change that raises the score by luck shows up as instability here.
"""
import argparse
import base64
import io
import json
import os
import sys
from collections import Counter, defaultdict

import pdfplumber

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import app  # noqa: E402

KEY_PATH = os.path.join(ROOT, "eval", "answer_key.json")


def analyse(path):
    """Same pipeline app.py uses: digital text, falling back to vision for scans."""
    with open(path, "rb") as f:
        raw = f.read()
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        text = "".join(p.extract_text() or "" for p in pdf.pages)
    if len(text.strip()) >= 100:
        content = text
    else:
        content = [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                            "data": base64.standard_b64encode(raw).decode()}},
            {"type": "text", "text": "Analyse this planning decision notice."},
        ]
    msg = app.client.messages.create(
        model="claude-sonnet-4-5", max_tokens=8000, temperature=0,
        system=app.system_prompt, messages=[{"role": "user", "content": content}],
    )
    return json.loads(app.strip_fences(msg.content[0].text))


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

    for field in ("document_type", "jurisdiction", "is_householder", "decision", "time_limit_years"):
        if field in asserted:
            check(field, data.get(field), asserted[field])

    if "condition_count" in asserted:
        check("condition_count", len(data.get("conditions", [])), asserted["condition_count"])

    if "begin_by" in asserted:
        bb = app.compute_begin_by(data.get("decision_date"), data.get("time_limit_years"))
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
        got_flags = app.get_flags(data)
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
        got = app.specialists_for(by_num.get(int(num)) or {})
        check(f"#{num} specialist", sorted(got), sorted(want))

    for num in asserted.get("specialist_is_empty", []):
        if num in skip:
            continue
        got = app.specialists_for(by_num.get(num) or {})
        checks.append(got == [])
        if got:
            fails.append(f"#{num} specialist: got {got!r}, expected none (in-house)")

    return checks, fails


def fingerprint(data):
    """The values we care about staying stable between identical runs."""
    fp = {f"top.{k}": data.get(k) for k in
          ("document_type", "jurisdiction", "is_householder", "decision", "time_limit_years")}
    fp["top.condition_count"] = len(data.get("conditions", []))
    fp["top.flags"] = sorted(f"{f.get('type')}:{f.get('condition')}" for f in app.get_flags(data))
    for c in data.get("conditions", []):
        n = c["condition_number"]
        fp[f"#{n}.gate"] = c.get("gate")
        fp[f"#{n}.ambiguous"] = c.get("gate_ambiguous")
        fp[f"#{n}.discharge"] = c.get("discharge_required")
        fp[f"#{n}.specialist"] = sorted(app.specialists_for(c))
    return fp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--file")
    args = ap.parse_args()

    key = json.load(open(KEY_PATH))
    targets = [k for k in key if not k.startswith("_")]
    if args.file:
        targets = [t for t in targets if t == args.file] or sys.exit(f"{args.file} not in the key")

    grand_ok = grand_total = 0
    for name in targets:
        entry = key[name]
        asserted, contested = entry.get("asserted", {}), entry.get("contested", {})
        print("=" * 78)
        print(name)
        print("=" * 78)

        runs = [analyse(os.path.join(ROOT, name)) for _ in range(args.runs)]

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
    return 0 if grand_ok == grand_total else 1


if __name__ == "__main__":
    sys.exit(main())
