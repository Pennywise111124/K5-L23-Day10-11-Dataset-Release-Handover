# Day 10 Lab — Nhóm 11: Kế hoạch, phân vai và điều kiện PASS

Seed luyện tập: **11007** · Release v1: **lab250_d3cc716c084b** · Lô sạch: `runs/clean` (seed 5, 50 ảnh)
Thời lượng: ~4 giờ · 6 người · Chấm: 100 điểm (xem [RUBRIC.md](RUBRIC.md))

> Cách đọc tài liệu này: mỗi mục có **điều kiện PASS** là các dòng tick được. Chỉ đóng một mục khi mọi dòng đã tick **và có bằng chứng** (lệnh chạy, file, số liệu thật). Các ngưỡng ghi "mục tiêu nhóm" là do nhóm tự đặt cho chắc điểm, không phải quy định của giảng viên.

---

## 0. Quy ước chung

- Windows PowerShell: dùng `py`, chạy từng lệnh riêng, thêm `-X utf8` nếu lỗi font.
- Mọi lệnh chạy từ thư mục gốc repo.
- **Chỉ N1 chạy** `lineage.py`, `pack_release.py`, `check_handover.py`, `export_submission.py` (máy đã chạy `run_lab.py`, giữ lineage chuẩn). Không ai chạy lại `run_lab.py`.
- Người khác tạo lô trên máy mình bằng: `py scripts/inject_release.py --seed 11007 --out runs/r11007` (cùng seed ra cùng `release_id`).
- Seed thêm để thử validator: `--seed 11 --out runs/r11`, `--seed 22 --out runs/r22`; lô sạch: `--seed 5 --no-faults --out runs/clean`.
- **Cấm** (vi phạm là 0 điểm mục liên quan, xem [RULES.md](RULES.md)):
  - validator đọc `_private/`, `data_source/`, annotation COCO, hoặc dùng mạng;
  - chạy `--dev-truth`, `--truth-dir`; dò đáp án bằng cách nộp thử từng phần danh sách lỗi;
  - sửa `scripts/` hoặc `delivery/`; bịa số liệu (F1, hash, kết quả review, người gán/kiểm);
  - nhúng tên ảnh, id hay đáp án của bất kỳ seed nào vào code;
  - commit `data_source/`, `runs/`, `*.zip`, `delivery/` của đề ẩn, secret.
- Validator chỉ dùng thư viện chuẩn (được import `scripts/pngutil.py`). Pillow chỉ dùng ở `tools/`.

## 1. Phân vai và file sở hữu

| | Vai | File sở hữu (chỉ người này sửa) |
|---|---|---|
| **N1** | Trưởng nhóm, máy chủ release | `submission/TEAM.md`, `validator/validate.py`, `README.md`, README của v2 |
| **N2** | Luật file + metadata | `validator/common.py`, `validator/rules_file.py` |
| **N3** | Luật nhãn + panoptic | `validator/rules_label.py`, `validator/rules_panoptic.py` |
| **N4** | Đối chiếu det ↔ panoptic | `validator/crosscheck.py` |
| **N5** | Viewer + dựng v2 | `tools/viewer.py`, `tools/review_queue.py`, `tools/build_v2.py` |
| **N6** | Truy vết, bảo mật, báo cáo, QA | `tools/trace_query.py`, `submission/r11007/security.md`, `submission/REPORT.md`, `submission/prompts.md` |

Giao diện module (chốt ở 0:15, không đổi về sau):
- Mỗi module luật có `check(delivery_dir: Path) -> list[dict]`, mỗi phần tử `{"type": ..., "target": ...}`. `scene_leak` có target là `scene_id`; mọi loại khác là tên ảnh **không có đuôi**.
- `crosscheck.candidates(delivery_dir) -> list[dict]` với `{"image", "guess", "reason", "score"}`.
- `validate.py <delivery> --out errors.json [--candidates c.json]` (CLI cố định). Ghi thêm lỗi luật ra `rules.json` để `merge_review.py` dùng.
- Git: mỗi người chỉ sửa file của mình; `git pull --rebase` trước mỗi lần push.

---

## 2. Lịch và cổng kiểm tra (gate)

| Mốc | Pha | Gate (phải PASS mới sang pha sau) |
|---|---|---|
| 0:15 | CP0 | G0 |
| 0:55 | CP1 | G1 |
| 1:50 | CP2 | G2 |
| 2:05 | CP3 | G3 |
| 2:45 | CP4 | G4 |
| 3:05 | CP5 | G5 |
| 3:15 | CP6a | G6 |
| 3:55 | CP6b | G7 (đề ẩn) |

### G0 — Chuẩn bị (0:00–0:15)
- [ ] Mỗi người: `py --version` ≥ 3.10; Pillow cài được (`py -m pip install pillow`); dữ liệu đã tải (`data_source/` có 250 ảnh + calib).
- [ ] Mỗi người có `runs/r11007/delivery/` với `release.json` ghi `lab250_d3cc716c084b`.
- [ ] Có `runs/r11/`, `runs/r22/` và `runs/clean/` (50 ảnh).
- [ ] `submission/TEAM.md` đủ: thành viên, MSHV, GitHub, phân vai, seed 11007.
- [ ] Mỗi người đã đặt `git config user.name` và `user.email` của chính mình.
- [ ] Đã chốt giao diện module (mục 1). Commit `P0: chia viec`.
- [ ] Mỗi người đã đọc `docs/DELIVERY.md`.

### G1 — Lỗi luật (0:15–0:55)
Lệnh kiểm:
```powershell
py -X utf8 validator/validate.py runs/r11007/delivery --out runs/r11007/errors.json
py -X utf8 scripts/score_findings.py --run runs/r11007
```
- [ ] `score_findings.py`: **F1 lỗi luật = 1,0** (làm tròn một chữ số) trên **seed 11007, 11 và 22**.
- [ ] Trên `runs/clean`: **0 lỗi luật** được báo.
- [ ] Validator chạy xong **≤ 60 giây** cho 250 ảnh (mục tiêu nhóm; vì đề ẩn chỉ có 40 phút).
- [ ] Không có import nào ngoài thư viện chuẩn và `pngutil`; không có đường dẫn tới `_private`, `data_source`, `cache`, không có `urllib`/`socket`/`requests`.
- [ ] Không có tên ảnh, `scene_id` hay id nào của seed nằm cứng trong code.
- [ ] Chạy được trên thư mục có tên ảnh dạng `img_0001` (thử với lô `--opaque`: `py scripts/inject_release.py --seed 33 --opaque --out runs/r33`) mà không lỗi.
- [ ] `errors.json` đúng định dạng `{"errors": [{"type": ..., "target": ...}]}`, không trùng cặp `(type, target)`.
- [ ] Mỗi ảnh tối đa một lỗi trong danh sách (đúng quy ước lô).

### G2 — Đối chiếu + xem ảnh (0:55–1:50)
Lệnh kiểm:
```powershell
py -X utf8 validator/validate.py runs/clean/delivery --out runs/clean/errors.json --candidates runs/clean/candidates.json
py -X utf8 scripts/merge_review.py --rules runs/r11007/rules.json --review runs/r11007/review_log.csv --out runs/r11007/errors.json
py -X utf8 scripts/score_findings.py --run runs/r11007
```
- [ ] **Số ứng viên trên lô sạch đã đo và ghi lại** (con số thật, vào `REPORT.md`).
- [ ] **Hàng đợi ứng viên ≤ khoảng 80 ảnh** cho lô 250 ảnh (mục tiêu nhóm: 6 người × 20 phút ÷ ~1,5 phút/ảnh); nếu vượt, siết ngưỡng hoặc cải thiện ghép và ghi lý do.
- [ ] **F1 nhóm gán nhãn ≥ 0,6** (đủ điểm mục 1.3); mục tiêu nhóm **≥ 0,8**.
- [ ] **F1 tổng ≥ 0,9** (README ước lượng với đối chiếu đúng + xem ảnh cẩn thận).
- [ ] `candidates.json` đúng định dạng; có đủ 5 loại: `class_swap`, `category_swap`, `bbox_drift`, `missing_box`, `instance_merge`.
- [ ] Phân biệt `class_swap` / `category_swap` **bằng mắt**, không đoán.
- [ ] `review_log.csv`: cột `image,type,verdict,note`.
  - Mọi lỗi gán nhãn trong `errors.json` có đúng một dòng `confirmed`.
  - Mọi `note` **≥ 20 ký tự**, nói **thấy gì** (ví dụ "xe tải mui kín, detection ghi car"), không chép giống nhau giữa các dòng (H3).
  - Có ít nhất vài dòng `rejected` kèm lý do (vật bị che, crowd...). Nếu hàng đợi không có ca lệch tự nhiên thì `REPORT.md` phải chứng minh bằng số liệu trên lô sạch.
  - Ghi **tên người xem** trong mỗi dòng. Cả 6 người đều có dòng review.
- [ ] Không dùng `score_findings.py` để dò từng ảnh; `review_log.csv` là kết quả xem ảnh.
- [ ] `viewer.py` chạy được trên lô `--opaque` và hiển thị ảnh nhỏ (~240×320) đủ rõ để quyết định.
- [ ] `REPORT.md` đã có câu trả lời "vì sao báo hết ứng viên làm F1 giảm" kèm **số liệu thật** của nhóm (precision, recall, F1 theo nhóm lỗi).

### G3 — Quyết định + lineage (1:50–2:05)
```powershell
py -X utf8 scripts/lineage.py record --event decision --release-id lab250_d3cc716c084b --decision HOLD
py -X utf8 scripts/lineage.py impact --release-id lab250_d3cc716c084b
```
- [ ] Tỉ lệ lỗi = `len(errors.json["errors"]) / 250`, ghi rõ mẫu số. Mỗi `scene_leak` tính là một ảnh.
- [ ] Nếu **> 2%** thì quyết định là **HOLD** (nếu ≤ 2% thì Release; kết luận phải theo con số thật).
- [ ] `impact` in dòng **`R-021: affected=True action=review_or_retrain`**.
- [ ] `REPORT.md` giải thích vì sao `R-021` phải xem lại hoặc train lại (đổi dataset không tự sửa model đã học).

### G4 — Bàn giao v2 (2:05–2:45)
Thư mục: `runs/r11007/handover/lab250_d3cc716c084b_v2/`. Lệnh kiểm:
```powershell
py -X utf8 scripts/pack_release.py runs/r11007/handover/lab250_d3cc716c084b_v2
py -X utf8 scripts/lineage.py record --event release --release-id lab250_d3cc716c084b_v2 --parent lab250_d3cc716c084b
py -X utf8 scripts/check_handover.py --run runs/r11007
```
- [ ] **H1:** `delivery/` (v1) không bị sửa. Mọi việc nằm trong `handover/`.
- [ ] v2 đủ 7 phần: `images/`, `labels/`, `rework_queue.csv`, `manifest.csv`, `label_summary.csv`, `truyvet.csv`, `README.txt`.
- [ ] `images/`, `labels/` copy **nguyên byte** từ v1, trừ ảnh phải gán lại. Nhãn không sửa tay.
- [ ] Sửa ngay trong v2: `wrong_hash` (mở ảnh kiểm trước: ảnh còn nguyên thì ghi hash mới, ảnh hỏng thì vào rework), `guideline_mismatch` (theo **job**), `scene_leak` (đưa cả cảnh về một split).
- [ ] Vào `rework_queue.csv` và **rời v2**: `missing_image`, `invalid_class`, `bbox_out_of_bounds`, `duplicate_box`, `class_swap`, `bbox_drift`, `missing_box`.
- [ ] Ảnh chỉ lỗi panoptic (`invalid_category_id`, `thing_overlap`, `category_swap`, `instance_merge`) **ở lại v2**, ghi vào phần Ghi chú của `README.txt` để báo team panoptic.
- [ ] `rework_queue.csv` có cột `image,type,annotator,reviewer,action`; người gán/kiểm **đúng theo `jobs.csv`**; mọi ảnh trong đó có lỗi trong `errors.json`.
- [ ] `manifest.csv` (`file,sha256`) có mọi file trong `images/` và `labels/`, đường dẫn dạng `images/x.jpg`, hash đúng.
- [ ] `label_summary.csv` (`class,count`) theo tên trong `classes.txt`, dòng cuối `TOTAL`, **khớp** số box trong `labels/` của v2.
- [ ] `truyvet.csv` (`image,scene_id,split,job_id,annotator,reviewer,guideline`): guideline lấy theo job, mỗi cảnh chỉ một split.
- [ ] `README.txt` theo `templates/README.txt`: dòng `QC v1: <số lỗi>/250` **đúng** với `errors.json`, kết luận v1 và v2 đúng ngưỡng 2%, phần Ghi chú nói rõ đã sửa gì (hash, guideline, split) và vì sao.
- [ ] Lineage có HOLD cho v1 và release v2 có `--parent` là v1.
- [ ] `check_handover.py` (bản gốc, chưa sửa) chỉ còn FAIL ở trace và security nếu chưa làm (H16, H17).
- [ ] Sau khi sửa bất cứ file nào trong v2: chạy lại `pack_release.py` (H15).
- [ ] `REPORT.md` giải thích hash chứng minh điều gì (file không đổi so với khi lập manifest) và **không** chứng minh điều gì (nhãn đúng).

### G5 — Truy vết (2:45–3:05)
```powershell
py -X utf8 tools/trace_query.py runs/r11007/delivery --out runs/r11007/trace.json
py -X utf8 scripts/score_findings.py --run runs/r11007
```
- [ ] `trace.json` có ba khóa `tier_a`, `tier_b`, `notify`.
- [ ] **`tier_a`:** ảnh thuộc cảnh team AI nêu trong `incoming/ticket.md`, **job theo guideline cũ (v1.2)**, có ít nhất một **box detection** (trong `labels/`) thuộc lớp bị đổi quy tắc ở `changelog.md`.
- [ ] **`tier_b`:** ảnh khác cùng điều kiện (job guideline cũ, có lớp đó) mà team AI chưa báo.
- [ ] **`notify`:** mã người gán và người kiểm của các job chứa ảnh tầng a và b; mọi mã **có trong `jobs.csv`**.
- [ ] Dùng guideline ghi ở **job** (`jobs.csv`), không dùng guideline ghi ở từng ảnh (có thể là lỗi `guideline_mismatch`). Dùng `labels/`, không dùng `masks/`.
- [ ] F1 truy vết (tier_a, tier_b, notify) mục tiêu nhóm **≥ 0,9** trên seed luyện tập.
- [ ] `trace_query.py` chạy được trên thư mục `delivery` đề ẩn (tên `img_0001`) mà không sửa code.
- [ ] `REPORT.md` nêu tiêu chí đã dùng (guideline theo job, không theo ảnh).

### G6 — Bảo mật + hoàn thiện (3:05–3:15)
- [ ] `security.md` đủ **ba mục**: ca USB; năm việc được/không (gắn với lô này); ca khuôn mặt.
- [ ] Ca khuôn mặt kết luận **Hold + báo người phụ trách** (không tự làm mờ), **nêu ví dụ ảnh có người thật trong lô của nhóm** (tên ảnh cụ thể, có trong lô). Không chép slide.
- [ ] `check_handover.py --run runs/r11007`: **0 FAIL** (H1–H17).
- [ ] `export_submission.py --run runs/r11007` chạy được; `submission/lineage.jsonl` đã chép từ `runs/lineage.jsonl`.
- [ ] README đổi tiêu đề thành `# Day 10 Lab — Nhóm 11`.

### G7 — Đề ẩn (3:15–3:55)
Trước khi nhận đề: validator, viewer, `merge_review.py`, `trace_query.py` đã sẵn sàng và đã tập chạy trên lô `--opaque`.
```powershell
py -X utf8 validator/validate.py delivery --out submission/de_an/rules.json --candidates submission/de_an/candidates.json
py -X utf8 scripts/merge_review.py --rules submission/de_an/rules.json --review submission/de_an/review_log.csv --out submission/de_an/errors.json
py -X utf8 tools/trace_query.py delivery --out submission/de_an/trace.json
```
- [ ] Validator chạy được trên `delivery/` đề ẩn, không lỗi. Không dựa vào tên ảnh COCO hay tham số `inject_release.py` (đề ẩn bị lật, nén lại, mức lỗi khác).
- [ ] Cả 6 người đều xem ảnh trong hàng đợi chia theo `id mod 6`.
- [ ] `de_an/review_log.csv`: mọi lỗi gán nhãn có dòng `confirmed`, note ≥ 20 ký tự nói thấy gì. Lỗi nào không có dòng `confirmed` sẽ bị **bỏ khỏi chấm**.
- [ ] `class_swap` / `category_swap` phân biệt đúng dựa vào ảnh.
- [ ] `submission/de_an/` có `errors.json`, `candidates.json`, `review_log.csv`, `trace.json`; đã commit và push.
- [ ] **Không commit** thư mục `delivery/` của đề ẩn. Không trao đổi kết quả với nhóm khác trong lúc làm.

---

## 3. Điều kiện PASS theo từng người

### N1 — Trưởng nhóm, máy chủ release
- [ ] `TEAM.md` đủ thông tin; commit `P0` đúng giờ.
- [ ] `validate.py` đúng giao diện CLI, gọi đủ module, ghi `errors.json`, `rules.json` và `candidates.json`; không đọc nguồn cấm.
- [ ] Chạy lineage (HOLD, release v2 + parent) và `impact` ra `R-021: affected=True`.
- [ ] `README.txt` của v2 đúng mẫu, mọi số lấy từ file thật.
- [ ] `check_handover.py` 0 FAIL; `export_submission.py` xong; đổi tiêu đề README; repo public tên **`K5-L23-DAY10-NHOM11-Release`**; nộp link lên LMS (https://aithucchien.vinuni.edu.vn).
- [ ] Soát từng dòng `review_log.csv` (không để dòng chép giống nhau, thiếu ghi chú, hay thiếu tên người xem).
- [ ] ≥ 2 commit có nội dung.

### N2 — Luật file + metadata
- [ ] `common.py` dùng được trong 10 phút đầu Pha 1.
- [ ] `missing_image`, `wrong_hash` (sha256 trên bytes `rb`, đủ image/label/mask), `scene_leak` (target `scene_id`), `guideline_mismatch` (so với **job**), `invalid_category_id`: đạt F1 = 1,0 trên seed 11007, 11, 22 và 0 báo nhầm trên `runs/clean`.
- [ ] Không có `wrong_hash` báo nhầm (không chỉ kiểm định dạng 64 ký tự).
- [ ] Đã sửa theo báo lỗi của N6 (QA); ≥ 2 commit; có dòng review của mình.

### N3 — Luật nhãn + panoptic
- [ ] `invalid_class`, `bbox_out_of_bounds` (có dung sai < 1 pixel), `duplicate_box` (cùng lớp, **cùng kích thước**, tâm lệch ≤ 2–3 px, không dùng IoU thấp), `thing_overlap` (id = R + G·256 + B·256², bỏ id 0 và `iscrowd`, so với `area`): F1 = 1,0 trên 3 seed và 0 báo nhầm ở lô sạch.
- [ ] `thing_overlap` đo thời gian trên 250 ảnh; tổng validator vẫn ≤ 60 giây (cache kết quả đọc PNG nếu cần).
- [ ] ≥ 2 commit; có dòng review của mình.

### N4 — Đối chiếu det ↔ panoptic
- [ ] Ghép box YOLO (đổi sang pixel) với segment thing theo IoU; ghép lớp qua **tên** (`classes.txt` ↔ `categories`).
- [ ] Dùng **pixel của mask** (không chỉ IoU bbox) để bắt `bbox_drift` và `instance_merge`; bỏ segment `iscrowd`.
- [ ] `candidates.json` đủ 5 loại, có `score` để sắp xếp.
- [ ] Số ứng viên trên lô sạch đã đo; ngưỡng đã chọn cùng N5 và có lý do bằng số liệu.
- [ ] Recall lỗi gán nhãn trên seed 11007 cao (không bỏ sót ca thật vì ngưỡng quá chặt) và hàng đợi vẫn ≤ ~80.
- [ ] ≥ 2 commit; có dòng review của mình.

### N5 — Viewer + dựng v2
- [ ] `viewer.py` (Pillow): vẽ box detection (màu một), viền segment panoptic (màu hai), ghi tên lớp, phóng to 2–3 lần, có cắt vùng quanh vật. Chạy được trên `delivery/` bất kỳ, kể cả tên `img_0001`.
- [ ] `review_queue.py`: sắp theo `score`, chia 6 phần theo `id mod 6`, ghi `review_<tên>.csv` đúng cột.
- [ ] `build_v2.py` tạo đủ 7 phần của v2, đúng quy tắc sửa/rework/giữ (mục G4), **không sửa nhãn tay**, không đụng `delivery/`.
- [ ] Phối hợp N4 đo nhiễu trên lô sạch.
- [ ] ≥ 2 commit; có dòng review của mình.

### N6 — Truy vết, bảo mật, báo cáo, QA
- [ ] `trace_query.py` đạt G5; chạy được trên đề ẩn.
- [ ] `security.md` đạt G6.
- [ ] `REPORT.md` có đủ 5 mục: (1) vì sao báo hết ứng viên làm F1 giảm (số liệu thật); (2) số ứng viên lô sạch và ngưỡng đã chọn; (3) vì sao `R-021` phải xem lại hoặc train lại; (4) hash chứng minh gì và không chứng minh gì; (5) tiêu chí truy vết (guideline theo job). Ghi thêm bug thật của `scripts/` nếu tìm thấy (không sửa `scripts/`).
- [ ] `prompts.md` đủ theo [RULES.md](RULES.md) (prompt, chỗ AI sai, cách kiểm lại).
- [ ] QA: chạy validator trên seed 11, 22, 33 (`--opaque`) và `runs/clean`; báo lỗi cho N2/N3.
- [ ] ≥ 2 commit; có dòng review của mình.

---

## 4. Quy đổi sang điểm RUBRIC và mục tiêu nhóm

| # | Hạng mục | Điểm | Điều kiện để đạt tối đa | Gate |
|---|---|---:|---|---|
| 1a | F1 tuyệt đối đề ẩn | 20 | `rank F1` ≥ 0,9 (điểm = 20 × F1) | G1, G2, G7 |
| 1b | Xếp hạng giữa các nhóm | 10 | Đứng đầu | G7 |
| 1c | F1 lỗi gán nhãn đề ẩn | 5 | F1 `cross_check_review` ≥ 0,6 | G2, G7 |
| 2a | Mọi lỗi gán nhãn có `confirmed` (đề ẩn) | 8 | Ghi chú nói rõ thấy gì | G7 |
| 2b | Phân biệt lỗi vs lệch tự nhiên | 4 | Có dòng `rejected` kèm lý do, hoặc `REPORT.md` đo lô sạch | G2 |
| 2c | Phân biệt `class_swap` / `category_swap` | 3 | Dựa vào ảnh | G7 |
| 3a | `check_handover.py` không FAIL | 10 | 0 FAIL, chạy bản gốc | G4, G6 |
| 3b | `rework_queue.csv` + `README.txt` | 6 | Giao đúng người, đúng ngưỡng 2%, Ghi chú đủ | G4 |
| 3c | Lineage | 5 | HOLD v1, release v2 có parent, giải thích `R-021` | G3, G4 |
| 3d | Không ghi đè | 4 | v1 giữ nguyên, `REPORT.md` giải thích hash | G4 |
| 4a | Truy vết đề ẩn | 6 | Trung bình F1 của `tier_a`, `tier_b`, `notify` = 1 | G7 |
| 4b | Truy vết seed luyện tập | 4 | `trace.json` đúng + tiêu chí trong `REPORT.md` | G5 |
| 5 | Bảo mật | 5 | `security.md` đủ ba mục, Hold + báo, ví dụ thật | G6 |
| 6a | Commit | 4 | Mỗi người ≥ 2 commit có nội dung | mục 5 |
| 6b | Dùng AI minh bạch | 3 | `prompts.md` đủ | mục 5 |
| 6c | `REPORT.md` | 3 | Đủ 5 mục, số liệu thật | mục 5 |

Vấn đáp (~3 phút/người, ngẫu nhiên): ai không trả lời được thì phần điểm cá nhân (mục 6) tối đa một nửa.

## 5. Điều kiện PASS cuối cùng trước khi nộp (mọi dòng phải tick)

**Kết quả đo**
- [ ] F1 lỗi luật = 1,0 trên seed 11007, 11, 22 và 0 lỗi luật trên `runs/clean`.
- [ ] F1 tổng ≥ 0,9; F1 gán nhãn ≥ 0,6 (mục tiêu nhóm ≥ 0,8) trên seed luyện tập.
- [ ] F1 truy vết ≥ 0,9 trên seed luyện tập.
- [ ] `check_handover.py --run runs/r11007`: 0 FAIL (bản gốc, chưa sửa).
- [ ] `py -X utf8 -m unittest discover -s tests` (hoặc cách chạy trong `tests/`) không lỗi.

**Repo và cấu trúc nộp** (theo [SUBMISSION.md](SUBMISSION.md))
- [ ] Repo public tên `K5-L23-DAY10-NHOM11-Release`; tiêu đề README là `# Day 10 Lab — Nhóm 11`.
- [ ] Có: `validator/validate.py`, `submission/TEAM.md`, `REPORT.md`, `prompts.md`, `lineage.jsonl`.
- [ ] Có: `submission/r11007/` (`errors.json`, `candidates.json`, `review_log.csv`, `trace.json`, `security.md`, `handover/<release_id>_v2/` và `<release_id>_v2.sha256`).
- [ ] Có: `submission/de_an/` (`errors.json`, `candidates.json`, `review_log.csv`, `trace.json`).
- [ ] **Không** có `data_source/`, `runs/`, `*.zip`, `delivery/` của đề ẩn, secret trong repo (`git ls-files` để kiểm).
- [ ] `scripts/` không bị sửa (`git diff` so với bản gốc của đề không có thay đổi trong `scripts/`).

**Trung thực**
- [ ] Mọi số trong `README.txt` và `REPORT.md` lấy từ file/lệnh thật; không bịa F1, hash, kết quả review, người gán/kiểm.
- [ ] Mọi dòng `confirmed`/`rejected` là kết luận của một người trong nhóm, có tên người xem.
- [ ] Mỗi người ≥ 2 commit có nội dung, đúng tên và email của mình (`git shortlog -sne`).

**Vấn đáp (cả nhóm chuẩn bị 10 phút)**
- [ ] Mỗi người giải thích được một đoạn validator và sửa khi đổi yêu cầu (N2, N3, N4 nắm phần mình; N1, N5, N6 nắm phần `validate.py`, viewer, trace).
- [ ] Mỗi người giải thích được dòng `confirmed`/`rejected` của chính mình: đã thấy gì trong ảnh.
- [ ] Mỗi người giải thích được một con số trong `README.txt` của v2 (số ảnh, số nhãn, QC v1 = lỗi/250).
- [ ] Trả lời được: vì sao báo hết ứng viên làm F1 giảm; vì sao `R-021` phải xem lại; hash chứng minh gì và không chứng minh gì; `tier_a` khác `tier_b` thế nào; vì sao lấy guideline theo job; vì sao thấy khuôn mặt là Hold + báo người phụ trách.

## 6. Lệnh tự kiểm tra nhanh (chạy từ gốc repo)

```powershell
# Lỗi luật trên 3 seed + lô sạch
py -X utf8 validator/validate.py runs/r11007/delivery --out runs/r11007/errors.json
py -X utf8 scripts/score_findings.py --run runs/r11007
py -X utf8 validator/validate.py runs/clean/delivery --out runs/clean/errors.json --candidates runs/clean/candidates.json

# Bàn giao
py -X utf8 scripts/check_handover.py --run runs/r11007

# Kiểm repo sạch
git ls-files | Select-String -Pattern "data_source|runs/|\.zip$"
git diff --stat -- scripts/
git shortlog -sne
```

Hai lệnh `git ls-files | Select-String ...` và `git diff -- scripts/` phải **không in ra gì**.
