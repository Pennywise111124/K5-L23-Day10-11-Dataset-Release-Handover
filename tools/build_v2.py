"""build_v2.py — N5: Dựng bàn giao v2 từ delivery v1 + errors.json.

Chạy bởi N1 trên máy chủ (có runs/r11007/):
    python tools/build_v2.py --run runs/r11007

Output: runs/r11007/handover/lab250_d3cc716c084b_v2/
  images/            - ảnh copy nguyên byte (trừ rework)
  labels/            - nhãn copy nguyên byte (trừ rework) — KHÔNG sửa tay
  rework_queue.csv   - image,type,annotator,reviewer,action
  manifest.csv       - file,sha256 cho mọi file images/ + labels/
  label_summary.csv  - class,count + dòng TOTAL
  truyvet.csv        - image,scene_id,split,job_id,annotator,reviewer,guideline
  README.txt         - N1 viết tay theo templates/README.txt

KHÔNG sửa gì trong delivery/.
"""

# ---------------------------------------------------------------------------
# NOTE (Pha 1): Đây là nháp. Logic phân loại và 7 file sẽ hoàn thiện ở Pha 4.
# ---------------------------------------------------------------------------

import sys
import json
import csv
import shutil
import hashlib
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Bảng phân loại lỗi (theo PLAN_NHOM11.md mục 7)
# ---------------------------------------------------------------------------
REWORK_TYPES = {
    "missing_image",
    "invalid_class",
    "bbox_out_of_bounds",
    "duplicate_box",
    "class_swap",
    "bbox_drift",
    "missing_box",
}
FIX_TYPES = {
    "wrong_hash",
    "guideline_mismatch",
    "scene_leak",
}
PANOPTIC_TYPES = {
    "invalid_category_id",
    "thing_overlap",
    "category_swap",
    "instance_merge",
}


# ---------------------------------------------------------------------------
# Tiện ích
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    """Tính SHA-256 bằng rb — đúng quy định."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_errors(errors_path: Path) -> dict[str, str]:
    """Đọc errors.json -> {image_stem: error_type} (mỗi ảnh tối đa một lỗi)."""
    if not errors_path.exists():
        print(f"[build_v2] WARN: Không tìm thấy {errors_path}")
        return {}
    data = json.loads(errors_path.read_text(encoding="utf-8"))
    result = {}
    for err in data.get("errors", []):
        t = err.get("type", "")
        target = err.get("target", "")
        # target có thể là tên ảnh (không đuôi) hoặc scene_id
        if t == "scene_leak":
            # scene_leak: target là scene_id, không phải ảnh cụ thể
            # Xử lý ở bước khác
            continue
        result[target] = t
    return result


def load_scene_leaks(errors_path: Path) -> set[str]:
    """Lấy danh sách scene_id bị scene_leak."""
    if not errors_path.exists():
        return set()
    data = json.loads(errors_path.read_text(encoding="utf-8"))
    return {e["target"] for e in data.get("errors", []) if e.get("type") == "scene_leak"}


def load_metadata(delivery_dir: Path) -> dict[str, dict]:
    """Đọc metadata.json -> {image_stem: {scene_id, split, job_id, guideline_version}}."""
    path = delivery_dir / "metadata.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["image"]: item for item in data.get("items", [])}


def load_jobs(delivery_dir: Path) -> dict[str, dict]:
    """Đọc jobs.csv -> {job_id: {annotator, reviewer, guideline}}."""
    path = delivery_dir / "jobs.csv"
    jobs = {}
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs[row["job_id"]] = {
                "annotator": row["annotator"],
                "reviewer": row["reviewer"],
                "guideline": row["guideline"],
            }
    return jobs


def load_classes(delivery_dir: Path) -> list[str]:
    """Đọc classes.txt -> list tên lớp."""
    path = delivery_dir / "classes.txt"
    classes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            classes.append(parts[1])
        else:
            classes.append(parts[0])
    return classes


def load_manifest(delivery_dir: Path) -> dict:
    """Đọc manifest.json -> dict {stem: {image, label, mask, ...}}."""
    path = delivery_dir / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("items", {})  # dict: stem -> info


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------

def build_v2(run_dir: Path):
    delivery_dir = run_dir / "delivery"
    errors_path = run_dir / "errors.json"
    release_path = delivery_dir / "release.json"

    # Lấy release_id
    release_id = json.loads(release_path.read_text(encoding="utf-8")).get("release_id", "unknown")
    v2_id = f"{release_id}_v2"
    out_dir = run_dir / "handover" / v2_id

    print(f"[build_v2] release_id = {release_id}")
    print(f"[build_v2] output     = {out_dir}")

    # Tạo thư mục output
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    (out_dir / "labels").mkdir(parents=True, exist_ok=True)

    # Load dữ liệu
    errors_by_image = load_errors(errors_path)
    scene_leaks = load_scene_leaks(errors_path)
    metadata = load_metadata(delivery_dir)
    jobs = load_jobs(delivery_dir)
    classes = load_classes(delivery_dir)
    manifest_items = load_manifest(delivery_dir)

    # Build metadata lookup: image -> scene_id
    image_to_scene = {item["image"]: item["scene_id"] for item in metadata.values()
                      if isinstance(item, dict)}
    # Actually metadata is {stem: item_dict}
    image_to_scene = {}
    image_to_meta = {}
    for stem, item in (metadata.items() if isinstance(metadata, dict) else
                       {it["image"]: it for it in metadata}.items()):
        image_to_scene[stem] = item.get("scene_id", "")
        image_to_meta[stem] = item

    # Xác định split đa số cho cảnh bị scene_leak
    # (cả cảnh chuyển về split chiếm đa số)
    scene_split_votes = {}  # scene_id -> Counter
    for stem, item in image_to_meta.items():
        scene = item.get("scene_id", "")
        split = item.get("split", "")
        if scene and split:
            scene_split_votes.setdefault(scene, {})
            scene_split_votes[scene][split] = scene_split_votes[scene].get(split, 0) + 1

    def majority_split(scene_id):
        votes = scene_split_votes.get(scene_id, {})
        if not votes:
            return "train"
        return max(votes, key=votes.get)

    # Phân loại từng ảnh
    rework_list = []       # Ảnh cần rework
    panoptic_list = []     # Ảnh lỗi panoptic, ở lại v2
    fix_list = []          # Ảnh sửa ngay, ở lại v2
    clean_list = []        # Ảnh không lỗi

    all_stems = list(manifest_items.keys())
    for stem in all_stems:
        err_type = errors_by_image.get(stem)
        # Kiểm tra scene_leak: ảnh ở cảnh bị scene_leak
        meta = image_to_meta.get(stem, {})
        is_scene_leak = meta.get("scene_id", "") in scene_leaks

        if err_type in REWORK_TYPES:
            rework_list.append((stem, err_type))
        elif err_type in PANOPTIC_TYPES:
            panoptic_list.append((stem, err_type))
        elif err_type in FIX_TYPES or is_scene_leak:
            fix_list.append((stem, err_type or "scene_leak"))
        else:
            clean_list.append(stem)

    stay_v2 = [s for s, _ in fix_list] + [s for s, _ in panoptic_list] + clean_list
    rework_stems = {s for s, _ in rework_list}

    print(f"[build_v2] Tổng ảnh: {len(all_stems)}")
    print(f"[build_v2]   Ở lại v2 (sạch):        {len(clean_list)}")
    print(f"[build_v2]   Ở lại v2 (sửa luật):    {len(fix_list)}")
    print(f"[build_v2]   Ở lại v2 (panoptic):     {len(panoptic_list)} → báo team panoptic")
    print(f"[build_v2]   Rework (rời v2):         {len(rework_list)}")

    # --- 1. Copy images + labels (nguyên byte) cho ảnh ở lại v2 ---
    for stem in stay_v2:
        # Tìm file ảnh
        for ext in (".jpg", ".jpeg", ".png"):
            src = delivery_dir / "images" / f"{stem}{ext}"
            if src.exists():
                shutil.copy2(src, out_dir / "images" / src.name)
                break
        # Copy nhãn
        label_src = delivery_dir / "labels" / f"{stem}.txt"
        if label_src.exists():
            shutil.copy2(label_src, out_dir / "labels" / label_src.name)

    # --- 2. manifest.csv ---
    manifest_rows = []
    for f in sorted((out_dir / "images").iterdir()):
        rel = f"images/{f.name}"
        manifest_rows.append({"file": rel, "sha256": sha256_file(f)})
    for f in sorted((out_dir / "labels").iterdir()):
        rel = f"labels/{f.name}"
        manifest_rows.append({"file": rel, "sha256": sha256_file(f)})

    with open(out_dir / "manifest.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file", "sha256"])
        w.writeheader()
        w.writerows(manifest_rows)
    print(f"[build_v2] manifest.csv: {len(manifest_rows)} dòng")

    # --- 3. label_summary.csv ---
    class_counts = {name: 0 for name in classes}
    total_boxes = 0
    for lf in sorted((out_dir / "labels").iterdir()):
        for line in lf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if parts:
                try:
                    cls_id = int(parts[0])
                    if 0 <= cls_id < len(classes):
                        class_counts[classes[cls_id]] += 1
                        total_boxes += 1
                except ValueError:
                    pass

    with open(out_dir / "label_summary.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["class", "count"])
        for name in classes:
            w.writerow([name, class_counts.get(name, 0)])
        w.writerow(["TOTAL", total_boxes])
    print(f"[build_v2] label_summary.csv: TOTAL={total_boxes}")

    # --- 4. rework_queue.csv ---
    rework_rows = []
    for stem, err_type in rework_list:
        meta = image_to_meta.get(stem, {})
        job_id = meta.get("job_id", "")
        job_info = jobs.get(job_id, {"annotator": "", "reviewer": "", "guideline": ""})
        # Gợi ý action theo loại lỗi
        action_map = {
            "missing_image": "Tìm và tải lại ảnh gốc từ nguồn",
            "invalid_class": "Kiểm tra và sửa class_id về đúng 0–79",
            "bbox_out_of_bounds": "Vẽ lại box nằm trong biên ảnh",
            "duplicate_box": "Xoá box trùng lặp cùng lớp cùng vị trí",
            "class_swap": "Kiểm tra ảnh thật, sửa lại class_id detection",
            "bbox_drift": "Căn chỉnh lại box cho khớp với vật thể",
            "missing_box": "Vẽ thêm box cho vật thể bị bỏ sót",
        }
        action = action_map.get(err_type, f"Xem lại annotation do lỗi {err_type}")
        rework_rows.append({
            "image": stem,
            "type": err_type,
            "annotator": job_info["annotator"],
            "reviewer": job_info["reviewer"],
            "action": action,
        })

    with open(out_dir / "rework_queue.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["image", "type", "annotator", "reviewer", "action"])
        w.writeheader()
        w.writerows(rework_rows)
    print(f"[build_v2] rework_queue.csv: {len(rework_rows)} ảnh")
    if panoptic_list:
        print(f"[build_v2]   Ảnh panoptic ở lại v2: {[s for s,_ in panoptic_list]}")

    # --- 5. truyvet.csv ---
    truyvet_rows = []
    for stem in stay_v2:
        meta = image_to_meta.get(stem, {})
        job_id = meta.get("job_id", "")
        job_info = jobs.get(job_id, {"annotator": "", "reviewer": "", "guideline": ""})
        scene_id = meta.get("scene_id", "")

        # Xác định split: nếu cảnh bị scene_leak → split đa số
        if scene_id in scene_leaks:
            split = majority_split(scene_id)
        else:
            split = meta.get("split", "")

        truyvet_rows.append({
            "image": stem,
            "scene_id": scene_id,
            "split": split,
            "job_id": job_id,
            "annotator": job_info["annotator"],
            "reviewer": job_info["reviewer"],
            "guideline": job_info["guideline"],  # theo job, không theo ảnh
        })

    with open(out_dir / "truyvet.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["image", "scene_id", "split", "job_id",
                                          "annotator", "reviewer", "guideline"])
        w.writeheader()
        w.writerows(truyvet_rows)
    print(f"[build_v2] truyvet.csv: {len(truyvet_rows)} dòng")

    # --- 6. Tóm tắt cho N1 viết README.txt ---
    num_images = len(list((out_dir / "images").iterdir()))
    print(f"\n[build_v2] === TÓM TẮT CHO N1 (dán vào README.txt) ===")
    print(f"  Release:    {v2_id}")
    print(f"  Parent:     {release_id}")
    print(f"  Số ảnh:     {num_images}")
    print(f"  Số nhãn:    {total_boxes}  (dòng TOTAL của label_summary.csv)")
    print(f"  Rework:     {len(rework_list)} ảnh → {[s for s,_ in rework_list]}")
    print(f"  Panoptic:   {[s for s,_ in panoptic_list]}")
    if scene_leaks:
        for scene_id in scene_leaks:
            print(f"  scene_leak {scene_id} → đưa cả cảnh về split '{majority_split(scene_id)}'")
    print(f"[build_v2] XONG. Thư mục: {out_dir}")
    print(f"[build_v2] Tiếp theo N1 chạy: py scripts/pack_release.py {out_dir}")

    return out_dir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Dựng bàn giao v2 từ delivery + errors.json")
    parser.add_argument("--run", type=Path, default=Path("runs/r11007"),
                        help="Thư mục run (chứa delivery/ và errors.json)")
    args = parser.parse_args()

    if not (args.run / "delivery").exists():
        sys.exit(f"[build_v2] Không tìm thấy: {args.run / 'delivery'}")
    if not (args.run / "errors.json").exists():
        print(f"[build_v2] WARN: errors.json chưa có. Build_v2 cần errors.json ở Pha 4.")
        print(f"[build_v2] Hiện tại chạy ở chế độ nháp (Pha 1) — chỉ thử cấu trúc.")

    build_v2(args.run)


if __name__ == "__main__":
    main()

