"""validate.py <delivery> --out errors.json [--candidates candidates.json]

Chi doc thu muc delivery. Chi dung thu vien chuan. Khong dung mang.
Moi anh mang toi da mot loi (uu tien: file > nhan > panoptic).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import crosscheck  # noqa: E402
import rules_file  # noqa: E402
import rules_label  # noqa: E402
import rules_panoptic  # noqa: E402
from common import Delivery  # noqa: E402

PRIORITY = ["missing_image", "wrong_hash", "invalid_class", "bbox_out_of_bounds", "duplicate_box",
            "invalid_category_id", "thing_overlap", "guideline_mismatch", "scene_leak"]


def rule_errors(d: Delivery) -> list[dict]:
    found: list[dict] = []
    for mod in (rules_file, rules_label, rules_panoptic):
        try:  # mot module loi khong duoc lam chet ca validator (de an chi co 40 phut)
            found += mod.check(d)
        except Exception as exc:  # noqa: BLE001
            print(f"CANH BAO: {mod.__name__} loi: {exc!r}", file=sys.stderr)
    best: dict[str, dict] = {}
    for e in found:
        t = e["target"]
        if e["type"] == "scene_leak":
            best[t] = e
            continue
        if t not in best or PRIORITY.index(e["type"]) < PRIORITY.index(best[t]["type"]):
            best[t] = e
    return sorted(best.values(), key=lambda e: (e["type"], e["target"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("delivery")
    ap.add_argument("--out", required=True)
    ap.add_argument("--candidates")
    args = ap.parse_args()
    d = Delivery(Path(args.delivery))
    errors = rule_errors(d)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"errors": errors}, ensure_ascii=False, indent=1), encoding="utf-8")
    # rules.json: chi loi luat, de merge_review.py gop voi cac dong confirmed
    (out.parent / "rules.json").write_text(json.dumps({"errors": errors}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(errors)} loi luat -> {out}")
    if args.candidates:
        skip = {e["target"] for e in errors}
        try:
            cands = crosscheck.candidates(d, skip=skip)
        except Exception as exc:  # noqa: BLE001
            print(f"CANH BAO: crosscheck loi: {exc!r}", file=sys.stderr)
            cands = []
        Path(args.candidates).parent.mkdir(parents=True, exist_ok=True)
        Path(args.candidates).write_text(json.dumps({"candidates": cands}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(cands)} ung vien -> {args.candidates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
