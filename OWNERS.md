# Chia file sở hữu — Nhóm 11 (6 người)

Theo [PLAN_NHOM11.md](PLAN_NHOM11.md). **Chỉ người sở hữu sửa file của mình.** Người khác cần đổi gì thì nhắn chủ file hoặc mở PR/nhánh riêng để chủ file duyệt. `git pull --rebase` trước mỗi lần push.

| Mã | Vai |
|---|---|
| **N1** | Trưởng nhóm, máy chủ release (giữ `runs/lineage.jsonl`) |
| **N2** | Luật file + metadata |
| **N3** | Luật nhãn + panoptic |
| **N4** | Đối chiếu detection ↔ panoptic |
| **N5** | Viewer + dựng lô v2 |
| **N6** | Truy vết, bảo mật, báo cáo, QA |

## 1. Code do nhóm viết

| File | Chủ | Nội dung | Ghi chú |
|---|---|---|---|
| `validator/validate.py` | **N1** | CLI, gộp các module, ghi `errors.json`/`rules.json`/`candidates.json` | giao diện cố định `validate.py <delivery> --out ... [--candidates ...]` |
| `validator/common.py` | **N2** | đọc manifest/metadata/jobs/classes/panoptic, đọc mask nhanh | mọi module khác import file này: đổi giao diện phải báo cả nhóm |
| `validator/rules_file.py` | **N2** | `missing_image`, `wrong_hash`, `scene_leak`, `guideline_mismatch`, `invalid_category_id` | N2 đã cài cả `invalid_category_id`; N3 cũng cài trong `rules_panoptic.py`. `validate.py` loại trùng `(type, target)` nên không sai kết quả, nhưng nên thống nhất giữ một nơi |
| `validator/rules_label.py` | **N3** | `invalid_class`, `bbox_out_of_bounds`, `duplicate_box` | |
| `validator/rules_panoptic.py` | **N3** | `invalid_category_id`, `thing_overlap` | PLAN gán `invalid_category_id` cho N2, nhưng code chung một file với `thing_overlap` nên **N3 giữ cả file**; N2 hỗ trợ kiểm thử |
| `validator/crosscheck.py` | **N4** | ghép box ↔ segment, sinh `candidates.json`, ngưỡng và bộ lọc nhiễu | |
| `tools/viewer.py` | **N5** | vẽ box + mask, cắt vùng quanh ứng viên | |
| `tools/build_v2.py` | **N5** | dựng `handover/<release_id>_v2/` | chạy bằng `--run runs/r<seed>` |
| `tools/review_queue.py` | **N5** | **chưa viết** (cập nhật sau lần pull 33738af): sắp ứng viên theo `score`, chia 6 phần theo `id mod 6`, ra `review_<tên>.csv` | việc còn lại của N5 |
| `tools/trace_query.py` | **N6** | truy vết `tier_a`/`tier_b`/`notify` | |
| `tests/` (nếu thêm test của nhóm) | **N6** | `tests/test_pipeline.py` là file gốc của đề, không sửa | |

## 2. Tài liệu và bài nộp

| File | Chủ | Ghi chú |
|---|---|---|
| `README.md` | **N1** | tiêu đề `# Day 10 Lab — Nhóm 11` đã đổi |
| `OWNERS.md`, `PLAN_NHOM11.md` | **N1** | |
| `submission/TEAM.md` | **N1** | cả nhóm điền dòng của mình |
| `submission/REPORT.md` | **N6** | N1/N4 gửi số liệu cho N6 |
| `submission/prompts.md` | **N6** | mỗi người gửi dòng của mình cho N6 gom |
| `submission/lineage.jsonl` | **N1** | chép từ `runs/lineage.jsonl` |
| `submission/r11007/errors.json` | **N1** | sinh bằng `merge_review.py` |
| `submission/r11007/candidates.json` | **N4** | |
| `submission/r11007/review_log.csv` | **N1 gộp**; **mỗi người** ghi dòng review của mình | mỗi dòng ghi tên người xem; N1 soát từng dòng |
| `submission/r11007/trace.json` | **N6** | |
| `submission/r11007/security.md` | **N6** | |
| `submission/r11007/handover/<release_id>_v2/` và `.sha256` | **N5** dựng, **N1** đóng gói | không sửa tay sau khi `pack_release.py` |
| `submission/de_an/*` (đề ẩn) | **N1** chạy `validate.py`; **cả nhóm** review; **N6** `trace.json` | không commit `delivery/` của đề |

## 3. File của đề: không ai sửa

`scripts/*`, `docs/*`, `templates/*`, `examples/*`, `GUIDE.md`, `RUBRIC.md`, `CHECKPOINTS.md`, `SUBMISSION.md`, `RULES.md`, `.gitignore`, `validator/README.md`, `tests/test_pipeline.py`.
Sửa `scripts/` để qua bộ kiểm bị 0 điểm mục bàn giao. Tìm thấy bug thật thì ghi vào `submission/REPORT.md` (mục 6, N6) và báo giảng viên.

## 4. Không commit

`runs/`, `data_source/`, `*.zip`, `delivery/` của đề ẩn, `__pycache__/`. Lệnh `lineage.py`, `pack_release.py`, `check_handover.py`, `export_submission.py` chỉ chạy trên máy của **N1**.

## 5. Phụ thuộc giữa các người

```
N2 (common.py) ──► N3, N4, N5, N6 import
N2 + N3 (rules_*) ──► N1 (validate.py)
N4 (crosscheck.py) ──► N1 (validate.py), N5 (review_queue)
N1 (errors.json) ──► N5 (build_v2.py) ──► N1 (pack_release, check_handover)
```

## 6. Commit tối thiểu mỗi người (≥ 2, đúng tên và email của mình)

| | Commit 1 | Commit 2 |
|---|---|---|
| N1 | `OWNERS.md`, `TEAM.md`, `validate.py` | `README.md`, `errors.json`, `lineage.jsonl`, lô v2 đóng gói |
| N2 | `common.py`, `rules_file.py` | sửa sau QA + dòng review |
| N3 | `rules_label.py`, `rules_panoptic.py` | tối ưu `thing_overlap` + dòng review |
| N4 | `crosscheck.py` | chỉnh ngưỡng, `candidates.json` + dòng review |
| N5 | `viewer.py` | `build_v2.py`, `review_queue.py` + dòng review |
| N6 | `trace_query.py`, `security.md` | `REPORT.md`, `prompts.md` + dòng review |
