"""Luat panoptic: invalid_category_id, thing_overlap."""

from __future__ import annotations

from common import Delivery, segment_counts

AREA_TOL = 0.02  # cho phep area lon hon pixel that toi da 2% (sai so nen/lam tron)


def check(d: Delivery) -> list[dict]:
    errors = []
    for stem in d.stems():
        ann = d.pan_ann.get(stem)
        if not ann:
            continue
        segs = ann["segments_info"]
        if any(s["category_id"] not in d.categories for s in segs):
            errors.append({"type": "invalid_category_id", "target": stem})
            continue
        mp = d.mask_path(stem)
        if not mp.is_file():
            continue
        counts = segment_counts(mp)
        for s in segs:
            cat = d.categories.get(s["category_id"], {})
            if s.get("iscrowd") or not cat.get("isthing"):
                continue
            actual = counts.get(s["id"], 0)
            if s["area"] > 0 and actual < s["area"] * (1 - AREA_TOL):
                errors.append({"type": "thing_overlap", "target": stem})
                break
    return errors
