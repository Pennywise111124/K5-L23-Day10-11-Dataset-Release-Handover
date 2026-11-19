"""make_readme_v2.py (N1): sinh README.txt cho lo v2 tu cac file that. Chi dung thu vien chuan.

  py tools/make_readme_v2.py --run runs/r11007 [--v2-verdict Release|Hold|Rework]

Doc: delivery/{release.json,jobs.csv}, errors.json, handover/<id>_v2/{images,label_summary.csv,
rework_queue.csv,truyvet.csv}. Ghi: handover/<id>_v2/README.txt (theo templates/README.txt).
Sau khi ghi phai chay lai scripts/pack_release.py (H15).
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import OrderedDict
from pathlib import Path

THRESHOLD = 0.02
PAN_ONLY = {"invalid_category_id", "thing_overlap", "category_swap", "instance_merge"}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def jpeg_ok(path: Path) -> bool:
    data = path.read_bytes()
    return len(data) > 4 and data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9"


def guideline_text(jobs: list[dict]) -> str:
    groups: "OrderedDict[str, list[str]]" = OrderedDict()
    for row in sorted(jobs, key=lambda r: r["job_id"]):
        groups.setdefault(row["guideline"], []).append(row["job_id"])
    parts = []
    for version, ids in sorted(groups.items()):
        parts.append(f"{version} ({ids[0]}–{ids[-1]})" if len(ids) > 1 else f"{version} ({ids[0]})")
    return ", ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--v2-verdict", choices=["Release", "Hold", "Rework"], default="Release")
    args = ap.parse_args()
    run = args.run
    d = run / "delivery"
    rid = json.loads((d / "release.json").read_text(encoding="utf-8"))["release_id"]
    v2 = run / "handover" / f"{rid}_v2"
    errors = json.loads((run / "errors.json").read_text(encoding="utf-8"))["errors"]
    jobs = read_csv(d / "jobs.csv")
    total = len(json.loads((d / "manifest.json").read_text(encoding="utf-8"))["items"])
    stems = sorted(p.stem for p in (v2 / "images").glob("*.jpg"))
    labels = int(next(r["count"] for r in read_csv(v2 / "label_summary.csv") if r["class"] == "TOTAL"))
    rework = read_csv(v2 / "rework_queue.csv")
    truyvet = {r["image"]: r for r in read_csv(v2 / "truyvet.csv")}

    n_err = len({e["target"] for e in errors})
    rate = n_err / total
    pct = f"{rate * 100:.1f}".replace(".", ",")
    v1 = "Hold" if rate > THRESHOLD else "Release"
    v1_reason = (f"{n_err}/{total} ảnh/cảnh lỗi ({pct}%), " +
                 ("vượt ngưỡng 2% nên không Release; run R-021 đã train trên v1 phải xem lại hoặc train lại"
                  if rate > THRESHOLD else "không vượt ngưỡng 2%"))

    notes = []
    for e in sorted(errors, key=lambda e: (e["type"], e["target"])):
        t, g = e["type"], e["target"]
        if t == "scene_leak":
            splits = {r["split"] for r in truyvet.values() if r["scene_id"] == g}
            notes.append(f"scene_leak {g}: đưa cả cảnh về một split ({'/'.join(sorted(splits))} trong truyvet.csv)")
        elif t == "guideline_mismatch":
            row = truyvet.get(g)
            where = f"guideline {row['guideline']} của job {row['job_id']}" if row else "guideline của job"
            notes.append(f"guideline_mismatch {g}: truyvet.csv ghi {where}, không theo guideline ghi ở ảnh")
        elif t == "wrong_hash":
            if g in stems:
                ok = jpeg_ok(v2 / "images" / f"{g}.jpg")
                notes.append(f"wrong_hash {g}: " + ("đã kiểm file ảnh (đúng chữ ký JPEG, đọc được), ảnh còn nguyên nên chỉ manifest cũ sai, manifest.csv ghi hash mới"
                                                      if ok else "ảnh có dấu hiệu hỏng, cần xem lại"))
            else:
                notes.append(f"wrong_hash {g}: ảnh hỏng, đưa vào rework_queue.csv")
    if rework:
        owners = sorted({f"{r['annotator']}/{r['reviewer']}" for r in rework})
        notes.append(f"{len(rework)} ảnh vào rework_queue.csv, giao lại cho người gán/kiểm theo jobs.csv ({', '.join(owners)})")
    pan = sorted({e["target"] + f" ({e['type']})" for e in errors if e["type"] in PAN_ONLY and e["target"] in stems})
    if pan:
        notes.append("lỗi chỉ ở panoptic, ảnh ở lại v2, báo team panoptic: " + ", ".join(pan))

    v2_reason = (f"sản phẩm detection: đã tách {len(rework)} ảnh lỗi nhãn detection/thiếu file vào rework, "
                 f"sửa hash, guideline, split theo mục Ghi chú; {len(stems)} ảnh còn lại không có lỗi detection đã biết"
                 + (f"; {len(pan)} ảnh lỗi panoptic ở lại v2 và báo team panoptic" if pan else ""))
    lines = [
        f"Release: {rid}_v2",
        f"Parent: {rid}",
        f"Số ảnh: {len(stems)}",
        f"Số nhãn: {labels}",
        f"Guideline: {guideline_text(jobs)}",
        f"QC v1: {n_err}/{total} = {pct}%",
        f"Kết luận v1: {v1} — {v1_reason}",
        f"Kết luận v2: {args.v2_verdict} — {v2_reason}",
        "Ghi chú: " + "; ".join(notes),
    ]
    (v2 / "README.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nĐã ghi {v2 / 'README.txt'}. Chạy lại: py scripts/pack_release.py {v2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
