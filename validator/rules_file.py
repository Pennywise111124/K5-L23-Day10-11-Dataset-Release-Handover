"""N2 file/metadata rules. Run with python -m validator.rules_file DELIVERY."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

if __package__:
    from .common import Delivery, delivery_path, sha256_file
else:
    from common import Delivery, delivery_path, sha256_file


def check(delivery_dir: Path | Delivery) -> list[dict]:
    context = delivery_dir if isinstance(delivery_dir, Delivery) else Delivery(delivery_dir)
    delivery_dir = context.root
    manifest = context.items
    metadata = context.metadata
    jobs = context.jobs
    panoptic = context.panoptic
    categories = {row["id"] for row in panoptic["categories"]}
    # Resolve via images[].id: opaque image names need not encode numeric IDs.
    names = {row["id"]: Path(row["file_name"]).stem for row in panoptic["images"]}
    invalid_categories = {
        names[row["image_id"]] for row in panoptic["annotations"]
        if any(segment["category_id"] not in categories for segment in row["segments_info"])
    }
    scenes = defaultdict(set)
    errors = []
    for name, item in sorted(manifest.items()):
        meta = metadata[name]
        scenes[meta["scene_id"]].add(meta["split"])
        if not delivery_path(delivery_dir, item["image"]).is_file():
            kind = "missing_image"
        elif any(
            not delivery_path(delivery_dir, item[field]).is_file()
            or sha256_file(delivery_path(delivery_dir, item[field])) != item[field + "_sha256"]
            for field in ("image", "label", "mask")
        ):
            kind = "wrong_hash"
        elif meta["guideline_version"] != jobs[meta["job_id"]]["guideline"]:
            kind = "guideline_mismatch"
        elif name in invalid_categories:
            kind = "invalid_category_id"
        else:
            continue
        errors.append({"type": kind, "target": name})
    errors.extend({"type": "scene_leak", "target": scene}
                  for scene, splits in sorted(scenes.items()) if {"train", "val"} <= splits)
    return errors


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("delivery", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    output = json.dumps({"errors": check(args.delivery)}, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
