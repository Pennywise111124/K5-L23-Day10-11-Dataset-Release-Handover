"""Ghép box detection với segment thing. candidates(delivery, skip=...).

Đọc qua common.Delivery. bbox_drift và instance_merge dùng pixel mask,
không chỉ IoU của bbox. class_swap là giả thuyết khi hai nguồn lệch lớp;
category_swap do người xem ảnh quyết.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from .common import Delivery, mask_ids
else:
    from common import Delivery, mask_ids

# ponytail: ngưỡng đo trên lô sạch. Siết nếu hàng đợi sạch vượt vài chục ảnh.
# MIN_SEG bỏ segment thing quá nhỏ; MIN_MISSING yêu cầu segment không box đủ lớn.
# IN_MATCH: cùng chỗ lệch lớp. IN_DRIFT: cùng lớp nhưng pixel nằm ngoài box.
# IN_MERGE và IN_ONLY: một segment nằm trong hai box cùng lớp.
MIN_SEG = 800
MIN_MISSING = 3500
IN_MATCH = 0.55
IN_DRIFT = 0.72
IN_MERGE = 0.22
IN_ONLY = 0.12


def context(d) -> Delivery:
    return d if isinstance(d, Delivery) else Delivery(Path(d))


def _iou(a, b) -> float:
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if inter <= 0:
        return 0.0
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    den = area_a + area_b - inter
    return inter / den if den else 0.0


def _cover(delivery: Delivery, stem: str, boxes: list[tuple]) -> dict[int, list]:
    """Mỗi segment id -> [số pixel, bbox, pixel trong từng box, pixel chỉ thuộc một box]."""
    width, _, ids = mask_ids(delivery.mask_path(stem))
    n = len(boxes)
    stats: dict[int, list] = {}
    for index, sid in enumerate(ids):
        if not sid:
            continue
        x, y = index % width, index // width
        rec = stats.get(sid)
        if rec is None:
            rec = [0, x, y, x, y, [0] * n, [0] * n]
            stats[sid] = rec
        rec[0] += 1
        if x < rec[1]:
            rec[1] = x
        if y < rec[2]:
            rec[2] = y
        if x > rec[3]:
            rec[3] = x
        if y > rec[4]:
            rec[4] = y
        px, py = x + 0.5, y + 0.5
        contained = []
        for bi, (_, x1, y1, x2, y2) in enumerate(boxes):
            if x1 <= px <= x2 and y1 <= py <= y2:
                contained.append(bi)
        for bi in contained:
            rec[5][bi] += 1
        if len(contained) == 1:
            rec[6][contained[0]] += 1
    return stats


def scan(delivery: Delivery, skip: set[str] | None = None) -> tuple[int, list[dict]]:
    skip = skip or set()
    classes = delivery.classes
    categories = delivery.categories
    matched = 0
    found: list[dict] = []
    for stem in delivery.stems():
        if stem in skip or stem not in delivery.pan_ann:
            continue
        mask = delivery.mask_path(stem)
        if not mask.is_file():
            continue
        boxes = delivery.box_pixels(stem)
        if not boxes and not delivery.label_path(stem).is_file():
            continue
        stats = _cover(delivery, stem, boxes)
        for seg in delivery.pan_ann[stem]["segments_info"]:
            if seg.get("iscrowd"):
                continue
            cat = categories.get(seg["category_id"])
            if cat is None or not cat.get("isthing"):
                continue
            rec = stats.get(seg["id"])
            if rec is None or rec[0] < MIN_SEG:
                continue
            area, x1, y1, x2, y2, hits, only = rec
            sb = (x1, y1, x2 + 1, y2 + 1)
            pan = cat["name"]
            ranked = []
            for bi, (cid, *box) in enumerate(boxes):
                frac = hits[bi] / area
                if frac <= 0 and _iou(sb, box) < 0.1:
                    continue
                name = classes.get(cid, str(cid))
                ranked.append((frac, only[bi] / area, _iou(sb, box), bi, name))
            ranked.sort(reverse=True)
            same = [row for row in ranked if row[0] >= IN_MERGE and row[1] >= IN_ONLY and row[4] == pan]
            if len(same) >= 2:
                found.append({"image": stem, "guess": "instance_merge", "reason": f"pixel segment {pan} nằm trong hai box cùng lớp", "score": round(same[1][0], 4)})
                matched += 1
                continue
            if not ranked:
                if area >= MIN_MISSING:
                    found.append({"image": stem, "guess": "missing_box", "reason": f"segment {pan} {area}px không có box", "score": round(min(1.0, area / 20000), 4)})
                continue
            frac, _, overlap, _, det = ranked[0]
            if frac < 0.15 and overlap < 0.15:
                if area >= MIN_MISSING:
                    found.append({"image": stem, "guess": "missing_box", "reason": f"segment {pan} {area}px không có box", "score": round(min(1.0, area / 20000), 4)})
                continue
            matched += 1
            if det != pan and frac >= IN_MATCH:
                found.append({"image": stem, "guess": "class_swap", "reason": f"cùng chỗ, detection {det}, panoptic {pan}", "score": round(frac, 4)})
            elif det == pan and frac < IN_DRIFT:
                found.append({"image": stem, "guess": "bbox_drift", "reason": f"box {det} để {1 - frac:.0%} pixel segment ra ngoài", "score": round(1 - frac, 4)})
    found.sort(key=lambda row: row["score"], reverse=True)
    return matched, found


def candidates(d, skip=None) -> list[dict]:
    return scan(context(d), set(skip or ()))[1]


if __name__ == "__main__":
    import json

    folder = Path(sys.argv[1])
    n_match, rows = scan(context(folder))
    kinds: dict[str, int] = {}
    images = set()
    for row in rows:
        kinds[row["guess"]] = kinds.get(row["guess"], 0) + 1
        images.add(row["image"])
    print(f"{folder}: ghép {n_match} cặp, {len(rows)} ứng viên trên {len(images)} ảnh {kinds}")
    if len(sys.argv) > 2:
        dest = Path(sys.argv[2])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps({"candidates": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(dest)
