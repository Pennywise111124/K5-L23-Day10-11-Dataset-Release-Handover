"""Dung lo ban giao v2 (san pham DETECTION) tu delivery v1 + errors.json. Khong sua delivery/.

  py tools/build_v2.py --run runs/r11007

Quy tac (xem GUIDE Pha 4):
  - anh loi nhan detection / thieu file  -> rework_queue.csv, roi khoi v2
  - wrong_hash: mo anh kiem; anh con nguyen -> chi ghi hash moi vao manifest; anh hong -> rework
  - guideline_mismatch: truyvet.csv lay guideline theo JOB
  - scene_leak: dua ca canh ve mot split (split da so cua canh)
  - loi chi o panoptic: anh o lai v2, ghi vao Ghi chu README de bao team panoptic
Nhan trong labels/ la ban sao nguyen byte tu v1 (khong sua tay).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

DET_REWORK = {"missing_image", "invalid_class", "bbox_out_of_bounds", "duplicate_box", "class_swap", "bbox_drift", "missing_box"}
PAN_ONLY = {"invalid_category_id", "thing_overlap", "category_swap", "instance_merge"}
ACTION = {
    "missing_image": "tim lai anh goc roi gan lai nhan detection",
    "invalid_class": "gan lai class_id hop le (0-79)",
    "bbox_out_of_bounds": "ve lai box nam trong anh",
    "duplicate_box": "xoa box lap, gan lai nhan detection",
    "class_swap": "gan lai lop cua box detection dung voi vat trong anh",
    "bbox_drift": "ve lai box cho khop vat",
    "missing_box": "bo sung box detection con thieu",
    "wrong_hash": "anh hong, tai lai anh va gan lai",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pct(x: float) -> str:
    return f"{round(x * 100, 1)}".replace(".", ",") + "%"


def image_ok(path: Path, size) -> bool:
    try:
        from PIL import Image

        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            im.load()
            return size is None or im.size == tuple(size)
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    args = ap.parse_args()
    run = Path(args.run)
    d = run / "delivery"
    rid = json.loads((d / "release.json").read_text(encoding="utf-8"))["release_id"]
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))["items"]
    meta = {m["image"]: m for m in json.loads((d / "metadata.json").read_text(encoding="utf-8"))["items"]}
    with open(d / "jobs.csv", newline="", encoding="utf-8") as f:
        jobs = {r["job_id"]: r for r in csv.DictReader(f)}
    pan = json.loads((d / "panoptic.json").read_text(encoding="utf-8"))
    sizes = {Path(i["file_name"]).stem: (i["width"], i["height"]) for i in pan["images"]}
    names = [ln.split(" ", 1)[1].strip() for ln in (d / "classes.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
    errors = json.loads((run / "errors.json").read_text(encoding="utf-8"))["errors"]

    types = defaultdict(set)
    for e in errors:
        types[e["target"]].add(e["type"])

    rework = {}
    hash_notes = []
    for stem, ts in sorted(types.items()):
        if stem not in man:
            continue
        hit = sorted(ts & DET_REWORK)
        if hit:
            rework[stem] = hit[0]
        elif "wrong_hash" in ts:
            if image_ok(d / man[stem]["image"], sizes.get(stem)):
                hash_notes.append(f"wrong_hash {stem}: đã mở ảnh kiểm, ảnh còn nguyên và đúng kích thước nên chỉ manifest cũ sai, ghi hash mới")
            else:
                rework[stem] = "wrong_hash"
                hash_notes.append(f"wrong_hash {stem}: ảnh hỏng khi mở, đưa vào rework")

    v2 = run / "handover" / f"{rid}_v2"
    if v2.exists():
        shutil.rmtree(v2)
    (v2 / "images").mkdir(parents=True)
    (v2 / "labels").mkdir()
    keep = [s for s in sorted(man) if s not in rework and (d / man[s]["image"]).is_file()]
    for s in keep:
        shutil.copyfile(d / man[s]["image"], v2 / "images" / f"{s}.jpg")
        shutil.copyfile(d / man[s]["label"], v2 / "labels" / f"{s}.txt")

    with open(v2 / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "sha256"])
        for sub in ("images", "labels"):
            for p in sorted((v2 / sub).iterdir()):
                w.writerow([f"{sub}/{p.name}", sha(p)])

    counts = Counter()
    for s in keep:
        for ln in (v2 / "labels" / f"{s}.txt").read_text(encoding="utf-8").splitlines():
            if ln.strip():
                counts[names[int(float(ln.split()[0]))]] += 1
    with open(v2 / "label_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["class", "count"])
        for n in names:
            if counts.get(n):
                w.writerow([n, counts[n]])
        w.writerow(["TOTAL", sum(counts.values())])

    by_scene = defaultdict(Counter)
    for m in meta.values():
        by_scene[m["scene_id"]][m["split"]] += 1
    scene_split = {}
    for sc, c in by_scene.items():
        top = c.most_common()
        scene_split[sc] = "train" if len(top) > 1 and top[0][1] == top[1][1] else top[0][0]

    with open(v2 / "truyvet.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image", "scene_id", "split", "job_id", "annotator", "reviewer", "guideline"])
        for s in keep:
            m = meta[s]
            j = jobs[m["job_id"]]
            w.writerow([s, m["scene_id"], scene_split[m["scene_id"]], m["job_id"], j["annotator"], j["reviewer"], j["guideline"]])

    with open(v2 / "rework_queue.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image", "type", "annotator", "reviewer", "action"])
        for s in sorted(rework):
            j = jobs[meta[s]["job_id"]]
            w.writerow([s, rework[s], j["annotator"], j["reviewer"], ACTION.get(rework[s], "gan lai")])

    err_targets = {e["target"] for e in errors}
    n1 = len(err_targets)
    rate = n1 / len(man)
    gl = defaultdict(list)
    for jid, j in sorted(jobs.items()):
        gl[j["guideline"]].append(jid)
    gl_txt = ", ".join(f"{g} ({v[0]}-{v[-1]})" if len(v) > 1 else f"{g} ({v[0]})" for g, v in sorted(gl.items()))
    pan_imgs = sorted(s for s in keep if types.get(s, set()) & PAN_ONLY)
    leaks = sorted(t for t in err_targets if t.startswith("scene_"))
    gmm = sorted(s for s, ts in types.items() if "guideline_mismatch" in ts)

    note = []
    if leaks:
        note.append("scene_leak " + ", ".join(leaks) + ": đưa cả cảnh về một split (split đa số của cảnh)")
    if gmm:
        note.append("guideline_mismatch " + ", ".join(gmm) + ": truyvet.csv ghi guideline theo job")
    note += hash_notes
    if rework:
        owners = sorted({f"{jobs[meta[s]['job_id']]['annotator']}/{jobs[meta[s]['job_id']]['reviewer']}" for s in rework})
        note.append(f"{len(rework)} ảnh vào rework_queue.csv, giao lại cho người gán/kiểm theo jobs.csv ({', '.join(owners)})")
    if pan_imgs:
        note.append("lỗi chỉ ở panoptic, ảnh ở lại v2, báo team panoptic: "
                    + ", ".join(f"{s} ({'/'.join(sorted(types[s] & PAN_ONLY))})" for s in pan_imgs))

    v1_dec = "Hold" if rate > 0.02 else "Release"
    lines = [
        f"Release: {rid}_v2",
        f"Parent: {rid}",
        f"Số ảnh: {len(keep)}",
        f"Số nhãn: {sum(counts.values())}",
        f"Guideline: {gl_txt}",
        f"QC v1: {n1}/{len(man)} = {pct(rate)}",
        f"Kết luận v1: {v1_dec} — {n1}/{len(man)} ảnh/cảnh lỗi ({pct(rate)}), vượt ngưỡng 2% nên không Release; run R-021 đã train trên v1 phải xem lại hoặc train lại",
        f"Kết luận v2: Release — sản phẩm detection: đã tách {len(rework)} ảnh lỗi nhãn detection/thiếu file vào rework, "
        f"sửa hash, guideline, split trong truyvet.csv; {len(keep)} ảnh còn lại không có lỗi detection đã biết; "
        f"{len(pan_imgs)} ảnh lỗi panoptic ở lại v2 và báo team panoptic",
        "Ghi chú: " + "; ".join(note),
    ]
    (v2 / "README.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"v2: {len(keep)} ảnh, {sum(counts.values())} nhãn, {len(rework)} rework -> {v2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
