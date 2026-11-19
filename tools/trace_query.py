"""Truy vet ticket cua team AI: anh nao, tang nao, bao ai.

  py tools/trace_query.py <delivery> --out trace.json

- Doc incoming/ticket.md (canh team AI neu) va guideline/changelog.md (lop bi doi quy tac).
- Dung guideline ghi o JOB (jobs.csv), khong dung guideline ghi o tung anh (co the la loi guideline_mismatch).
- Dung box DETECTION trong labels/, khong dung masks/.
tier_a: anh trong cac canh team AI neu, job guideline cu, co it nhat mot box thuoc lop bi doi quy tac.
tier_b: cac anh khac cung dieu kien (job guideline cu, co lop do) ma chua ai bao.
notify: ma nguoi gan va nguoi kiem cua cac job chua anh tang a va b.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


def vkey(v: str):
    return tuple(int(x) for x in re.findall(r"\d+", v))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("delivery")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    d = Path(args.delivery)

    ticket = (d / "incoming" / "ticket.md").read_text(encoding="utf-8")
    scenes = set(re.findall(r"scene_\d+", ticket))

    changelog = (d / "guideline" / "changelog.md").read_text(encoding="utf-8")
    sections = re.split(r"^##\s+", changelog, flags=re.M)[1:]
    latest, changed = None, set()
    for sec in sections:
        head, _, body = sec.partition("\n")
        ver = head.strip()
        if latest is None or vkey(ver) > vkey(latest):
            latest = ver
            changed = set(re.findall(r"`([^`]+)`", body))  # lop bi doi quy tac o ban moi nhat
    classes = {}
    for ln in (d / "classes.txt").read_text(encoding="utf-8").splitlines():
        if ln.strip():
            cid, _, name = ln.partition(" ")
            classes[name.strip()] = int(cid)
    changed_ids = {classes[c] for c in changed if c in classes}

    with open(d / "jobs.csv", newline="", encoding="utf-8") as f:
        jobs = {r["job_id"]: r for r in csv.DictReader(f)}
    meta = {m["image"]: m for m in json.loads((d / "metadata.json").read_text(encoding="utf-8"))["items"]}
    manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))["items"]

    tier_a, tier_b = [], []
    for stem in sorted(manifest):
        m = meta.get(stem)
        if not m:
            continue
        job = jobs.get(m["job_id"])
        if not job or vkey(job["guideline"]) >= vkey(latest):  # chi job theo guideline cu
            continue
        lab = d / manifest[stem].get("label", f"labels/{stem}.txt")
        if not lab.is_file():
            continue
        has = any(int(float(ln.split()[0])) in changed_ids for ln in lab.read_text(encoding="utf-8").splitlines() if ln.strip())
        if not has:
            continue
        (tier_a if m["scene_id"] in scenes else tier_b).append(stem)

    people = set()
    for stem in tier_a + tier_b:
        j = jobs[meta[stem]["job_id"]]
        people |= {j["annotator"], j["reviewer"]}
    out = {"tier_a": tier_a, "tier_b": tier_b, "notify": sorted(people)}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"lop doi quy tac: {sorted(changed)}; canh: {sorted(scenes)}; tier_a {len(tier_a)}, tier_b {len(tier_b)}, notify {sorted(people)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
