"""Shared delivery readers. All data paths stay inside the supplied delivery.

read_manifest -> image-name keyed items; read_metadata -> image-name keyed rows;
read_jobs -> job-id keyed rows; read_classes -> {int: name}; read_panoptic ->
the original JSON object; read_yolo -> [(class_id, x, y, width, height)].
read_mask -> (width, height, RGB bytearray), shared through a bounded cache.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import Counter
from array import array
from functools import cached_property, lru_cache
from pathlib import Path

if __package__ in (None, ""):
    # N1's CLI may import common as a top-level module from validator/.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.pngutil import read_rgb


def delivery_path(delivery_dir: Path, relative: str) -> Path:
    """Reject absolute paths and paths/symlinks escaping the delivery root."""
    root = Path(delivery_dir).resolve()
    supplied = Path(relative)
    if supplied.is_absolute():
        raise ValueError(f"Expected delivery-relative path: {relative}")
    path = (root / supplied).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Path escapes delivery: {relative}")
    return path


def read_json(path: Path) -> dict:
    with Path(path).open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def read_manifest(delivery_dir: Path) -> dict[str, dict]:
    return read_json(delivery_path(delivery_dir, "manifest.json"))["items"]


def read_metadata(delivery_dir: Path) -> dict[str, dict]:
    rows = read_json(delivery_path(delivery_dir, "metadata.json"))["items"]
    return {row["image"]: row for row in rows}


def read_jobs(delivery_dir: Path) -> dict[str, dict]:
    with delivery_path(delivery_dir, "jobs.csv").open(encoding="utf-8-sig", newline="") as stream:
        return {row["job_id"]: row for row in csv.DictReader(stream)}


def read_classes(delivery_dir: Path) -> dict[int, str]:
    result = {}
    for line in delivery_path(delivery_dir, "classes.txt").read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            class_id, name = line.split(maxsplit=1)
            result[int(class_id)] = name.strip()
    return result


def read_panoptic(delivery_dir: Path) -> dict:
    return read_json(delivery_path(delivery_dir, "panoptic.json"))


def read_yolo(path: Path) -> list[tuple[int, float, float, float, float]]:
    """Skip blank rows; malformed rows raise ValueError with file and line."""
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            class_text, *box_text = line.split()
            class_value = float(class_text)
            box = tuple(map(float, box_text))
            if not class_value.is_integer() or len(box) != 4 or not all(map(math.isfinite, box)):
                raise ValueError("expected integer class and four finite coordinates")
            rows.append((int(class_value), *box))
        except ValueError as exc:
            raise ValueError(f"{path}:{number}: invalid YOLO row") from exc
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@lru_cache(maxsize=32)
def _read_mask(path: Path, mtime_ns: int, size: int) -> tuple[int, int, bytearray]:
    return read_rgb(path)


def read_mask(path: Path) -> tuple[int, int, bytearray]:
    """Cached RGB pixels. Callers must treat the returned bytearray as read-only."""
    path = Path(path).resolve()
    stat = path.stat()
    return _read_mask(path, stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=512)
def _mask_counts(path: Path, mtime_ns: int, size: int) -> Counter:
    _, _, pixels = _read_mask(path, mtime_ns, size)
    return Counter(pixels[i] + (pixels[i + 1] << 8) + (pixels[i + 2] << 16)
                   for i in range(0, len(pixels), 3))


def mask_counts(path: Path) -> Counter:
    """Cached segment pixel counts, including background id 0; do not mutate."""
    path = Path(path).resolve()
    stat = path.stat()
    return _mask_counts(path, stat.st_mtime_ns, stat.st_size)


def clear_mask_cache() -> None:
    _read_mask.cache_clear()
    _mask_counts.cache_clear()


class Delivery:
    """Shared, lazy delivery context for validate.py and rule modules.

    manifest is the original JSON object; items/meta follow the team's shared
    interface. Construct a new context after changing input files.
    Implements os.PathLike so existing check(Path) modules remain compatible.
    """

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise NotADirectoryError(self.root)

    def __fspath__(self) -> str:
        return str(self.root)

    def path(self, relative: str) -> Path:
        return delivery_path(self.root, relative)

    @cached_property
    def manifest(self) -> dict:
        return read_json(self.path("manifest.json"))

    @cached_property
    def items(self) -> dict[str, dict]:
        return self.manifest["items"]

    @cached_property
    def metadata(self) -> dict[str, dict]:
        return read_metadata(self.root)

    @property
    def meta(self) -> dict[str, dict]:
        return self.metadata

    @cached_property
    def jobs(self) -> dict[str, dict]:
        return read_jobs(self.root)

    @cached_property
    def classes(self) -> dict[int, str]:
        return read_classes(self.root)

    @cached_property
    def panoptic(self) -> dict:
        return read_panoptic(self.root)

    @cached_property
    def categories(self) -> dict[int, dict]:
        return {row["id"]: row for row in self.panoptic["categories"]}

    @cached_property
    def pan_images(self) -> dict[str, dict]:
        return {Path(row["file_name"]).stem: row for row in self.panoptic["images"]}

    @cached_property
    def pan_ann(self) -> dict[str, dict]:
        names = {row["id"]: Path(row["file_name"]).stem for row in self.panoptic["images"]}
        return {names[row["image_id"]]: row for row in self.panoptic["annotations"]}

    def stems(self) -> list[str]:
        return sorted(self.items)

    def image_path(self, stem: str) -> Path:
        return self.path(self.items[stem]["image"])

    def label_path(self, stem: str) -> Path:
        return self.path(self.items[stem]["label"])

    def mask_path(self, stem: str) -> Path:
        return self.path(self.items[stem]["mask"])

    def size(self, stem: str) -> tuple[int, int] | None:
        image = self.pan_images.get(stem)
        return (image["width"], image["height"]) if image else None

    def read_label(self, stem: str) -> list[tuple[int, float, float, float, float]]:
        return self.yolo(stem)

    def box_pixels(self, stem: str) -> list[tuple[int, float, float, float, float]]:
        size = self.size(stem)
        if size is None:
            return []
        width, height = size
        return [(cid, (x - w / 2) * width, (y - h / 2) * height,
                 (x + w / 2) * width, (y + h / 2) * height)
                for cid, x, y, w, h in self.read_label(stem)]

    def cat_id_by_name(self) -> dict[str, int]:
        return {row["name"]: cid for cid, row in self.categories.items()}

    def det_to_cat(self) -> dict[int, int]:
        by_name = self.cat_id_by_name()
        return {cid: by_name[name] for cid, name in self.classes.items() if name in by_name}

    def yolo(self, image: str) -> list[tuple[int, float, float, float, float]]:
        return read_yolo(self.label_path(image))

    def mask(self, image: str) -> tuple[int, int, bytearray]:
        return read_mask(self.mask_path(image))

    def mask_counts(self, image: str) -> Counter:
        return mask_counts(self.mask_path(image))


def mask_ids(path: Path) -> tuple[int, int, array]:
    """Team API: RGB mask converted into one unsigned segment ID per pixel."""
    width, height, pixels = read_mask(path)
    return width, height, array("I", (pixels[i] + (pixels[i + 1] << 8) +
                                    (pixels[i + 2] << 16)
                                    for i in range(0, len(pixels), 3)))


def segment_counts(path: Path) -> Counter:
    """Team API alias; reuse the shared count cache."""
    return mask_counts(path)
