# Day 10 Lab — Nhóm 11: Kế hoạch chi tiết, phân vai và điều kiện PASS

Seed luyện tập: **11007** · Release v1: **lab250_d3cc716c084b** · Lô sạch: `runs/clean` (seed 5, 50 ảnh)
Thời lượng: ~4 giờ · 6 người · Chấm: 100 điểm (xem [RUBRIC.md](RUBRIC.md)) · Mốc: [CHECKPOINTS.md](CHECKPOINTS.md) · Lệnh: [GUIDE.md](GUIDE.md) · Định dạng lô: [docs/DELIVERY.md](docs/DELIVERY.md)

> **Cách đọc tài liệu này.** Mỗi pha có 4 phần: **(A) Việc từng người** (bước đánh số, làm tuần tự), **(B) Gate** (dòng tick được), **(C) Kết quả đạt được sau CP** (thứ phải có trong tay, kèm bằng chứng), **(D) Nếu trễ**. Chỉ đóng một pha khi mọi dòng gate đã tick **và có bằng chứng** (lệnh chạy, file, số liệu thật). Ngưỡng ghi "mục tiêu nhóm" do nhóm tự đặt để chắc điểm, không phải quy định của giảng viên.

## Sự thật đã kiểm trong repo (dùng làm chuẩn, khỏi đoán)

- `runs/r11007/` và `runs/clean/` **đã có trên máy N1**; `runs/lineage.jsonl` đã có 2 dòng (`inject` và `train R-021`). **N1 không chạy lại `run_lab.py`** (sẽ gắn R-021 lần hai).
- `jobs.csv` seed 11007: **v1.2 = J01–J04, v1.3 = J05–J10** (không phải J01–J03 như ví dụ trong mẫu). Dòng `Guideline:` của README v2 phải ghi đúng: `v1.2 (J01–J04), v1.3 (J05–J10)`.
- `incoming/ticket.md`: team AI báo **`bottle`** bị bỏ sót ở **scene_157** và **scene_511**. `changelog.md`: v1.3 đổi quy tắc lớp **`bottle`** (vật bị che > 50% hoặc cắt mép **vẫn phải gán box**; v1.2 cho phép bỏ qua). Vậy `tier_a` ∈ {ảnh thuộc scene_157/scene_511, job v1.2, có box lớp `bottle`}; `tier_b` = ảnh khác, job v1.2, có box `bottle`.
- `check_handover.py` kiểm **H1–H17** (bảng ở mục 8). Người chấm chạy **bản gốc**, nên không ai được sửa `scripts/`.
- `merge_review.py` bỏ lỗi gán nhãn trong `rules.json`, chỉ lấy lỗi gán nhãn từ dòng `confirmed`; nó **báo lỗi dừng** nếu có dòng `confirmed` mà `type` không phải lỗi gán nhãn.
- `export_submission.py --run` chỉ chép `errors.json, candidates.json, review_log.csv, trace.json, security.md, handover/` (trừ `.zip`) và `runs/lineage.jsonl → submission/lineage.jsonl`. **Không** chép `rules.json`, `de_an/`, `TEAM/REPORT/prompts`.
- `.gitignore` đã chặn `/data_source`, `/runs`, `*.zip`, `/delivery`.

---

## 0. Quy ước chung

- Windows PowerShell: dùng `py`, chạy từng lệnh riêng, thêm `-X utf8` nếu lỗi font. Mọi lệnh chạy từ thư mục gốc repo.
- **Chỉ N1 chạy** `lineage.py`, `pack_release.py`, `check_handover.py`, `export_submission.py` và `build_v2.py` (máy chủ release, giữ lineage chuẩn).
- Người khác tạo lô trên máy mình: `py scripts/inject_release.py --seed 11007 --out runs/r11007` (cùng seed → cùng lô, cùng `release_id`; máy họ không có R-021, đúng chủ ý).
- Seed thử: `--seed 11 --out runs/r11`, `--seed 22 --out runs/r22`, lô sạch `--seed 5 --no-faults --out runs/clean`, lô đề-ẩn-giả `--seed 33 --opaque --out runs/r33`.
- **Cấm** (vi phạm là 0 điểm mục liên quan, xem [RULES.md](RULES.md)):
  - validator đọc `_private/`, `data_source/`, annotation COCO, hoặc dùng mạng;
  - chạy `--dev-truth`, `--truth-dir`; dò đáp án bằng cách nộp thử từng phần danh sách lỗi / dùng `score_findings.py` dò từng ảnh;
  - sửa `scripts/` hoặc `delivery/`; bịa số liệu (F1, hash, kết quả review, người gán/kiểm);
  - nhúng tên ảnh, id hay đáp án của bất kỳ seed nào vào code; dựa vào tham số `inject_release.py`;
  - commit `data_source/`, `runs/`, `*.zip`, `delivery/` của đề ẩn, secret.
- Validator chỉ dùng thư viện chuẩn (được import `scripts/pngutil.py`). Pillow chỉ dùng ở `tools/`.
- Gặp bug trong `scripts/`: **ghi vào `REPORT.md` mục 6, không sửa.**
- Git: mỗi người chỉ sửa file của mình; `git pull --rebase` trước mỗi lần push; commit message `P<pha>: <việc>`; mỗi người dùng **tên và email Git của chính mình**, ≥ 2 commit có nội dung (kiểm: `git shortlog -sne HEAD`).
- AI: ai dùng AI thì thêm **một dòng vào `prompts.md` ngay lúc dùng** (prompt tóm tắt, AI sai ở đâu, kiểm lại thế nào). Ngoại lệ cấm: không dùng AI thay mắt người ở bước xem ảnh.

## 1. Phân vai, file sở hữu và giao diện

| | Vai | File sở hữu (chỉ người này sửa) |
|---|---|---|
| **N1** | Trưởng nhóm, máy chủ release | `submission/TEAM.md`, `validator/validate.py`, `README.md`, README.txt của v2 |
| **N2** | Luật file + metadata | `validator/common.py`, `validator/rules_file.py` |
| **N3** | Luật nhãn + panoptic | `validator/rules_label.py`, `validator/rules_panoptic.py` |
| **N4** | Đối chiếu det ↔ panoptic | `validator/crosscheck.py` |
| **N5** | Viewer + hàng đợi + dựng v2 | `tools/viewer.py`, `tools/review_queue.py`, `tools/build_v2.py` |
| **N6** | Truy vết, bảo mật, báo cáo, QA | `tools/trace_query.py`, `submission/r11007/security.md`, `submission/REPORT.md`, `submission/prompts.md` |

**Giao diện module (chốt ở 0:15, không đổi về sau):**
- `common.py` (N2) cung cấp: đọc `manifest.json`, `metadata.json`, `jobs.csv`, `classes.txt`, `panoptic.json`; đọc nhãn YOLO; tính sha256 bằng `rb`; cache đọc mask PNG (dùng chung cho N3 và N4).
- Mỗi module luật: `check(delivery_dir: Path) -> list[dict]`, phần tử `{"type": ..., "target": ...}`. `scene_leak`: target là `scene_id`. Mọi loại khác: tên ảnh **không đuôi**.
- `crosscheck.candidates(delivery_dir) -> list[dict]` với `{"image", "guess", "reason", "score"}`; `guess` ∈ {`class_swap`, `category_swap`, `bbox_drift`, `missing_box`, `instance_merge`}.
- CLI cố định: `validate.py <delivery> --out <file> [--candidates <file>]`. **Quy ước nhóm:** `--out` luôn trỏ vào **`rules.json`** (chỉ lỗi luật). `errors.json` cuối cùng chỉ do `merge_review.py` tạo. Riêng lúc chấm tạm ở CP1 thì chép `rules.json` thành `errors.json`.
- **Thứ tự ưu tiên khi một ảnh dính nhiều luật** (mỗi ảnh chỉ một lỗi, khớp cách `check_handover.py` tự kiểm): `missing_image` → `wrong_hash` → `guideline_mismatch` → `invalid_class` → `bbox_out_of_bounds` → … Ảnh thiếu file thì bỏ qua mọi kiểm tra sau; `scene_leak` đứng riêng theo cảnh.
- `validate.py` chạy từng module trong `try/except`: một module lỗi chỉ in cảnh báo, không làm chết cả validator (quan trọng ở 40 phút đề ẩn).

## 2. Dòng thời gian và luồng file giữa các máy

| Mốc | Pha | CP |
|---|---|---|
| 0:00–0:15 | Pha 0 Chuẩn bị | CP0 |
| 0:15–0:55 | Pha 1 Lỗi luật | CP1 |
| 0:55–1:50 | Pha 2 Đối chiếu + xem ảnh | CP2 |
| 1:50–2:05 | Pha 3 Quyết định + lineage | CP3 |
| 2:05–2:45 | Pha 4 Bàn giao v2 | CP4 |
| 2:45–3:05 | Pha 5 Truy vết | CP5 |
| 3:05–3:15 | Pha 6a Bảo mật + khoá repo | CP6a |
| 3:15–3:55 | Pha 6b Đề ẩn (40 phút) | CP6b |

**Chạy song song (không chờ nhau):** N5 dựng viewer và `build_v2.py` từ Pha 1; N6 dựng `trace_query.py` + nháp `security.md` từ Pha 1 (truy vết không phụ thuộc `errors.json`); N4 chuẩn bị đọc mask từ Pha 1.

**Luồng file (vì `runs/` không commit mà `check_handover.py`/`export_submission.py` đọc `runs/` trên máy N1):**

| File | Ai tạo | Đường đi | Đích trên máy N1 |
|---|---|---|---|
| mã nguồn `validator/`, `tools/` | N2–N6 | Git push → N1 `git pull --rebase` | repo |
| `review_<tên>.csv` (mỗi người một file) | từng người | Git `submission/r11007/review/` | pull |
| `review_log.csv` (gộp) | N5 | Git `submission/r11007/review_log.csv` | N1 chép vào `runs/r11007/review_log.csv` |
| `rules.json`, `candidates.json`, `errors.json` | N1 | chạy trên máy N1 | `runs/r11007/` |
| `trace.json` | N6 chạy `trace_query.py` (cùng kết quả mọi máy) | Git `submission/r11007/trace.json` | N1 chép vào `runs/r11007/` |
| `security.md` | N6 | Git `submission/r11007/security.md` | N1 chép vào `runs/r11007/` |

Mọi máy ra cùng `candidates.json`/`rules.json` vì thuật toán xác định và cùng lô (kiểm: so sha256 file giữa hai máy một lần).

---

## 3. Pha 0 — Chuẩn bị (0:00–0:15)

### (A) Việc từng người
**Cả nhóm (mỗi người trên máy mình):**
1. `py --version` ≥ 3.10. Cài Pillow nếu là N5 (viewer) và nên cài cho cả nhóm xem ảnh: `py -m pip install pillow`.
2. `git clone` repo nhóm; `git config user.name "<tên thật>"`, `git config user.email "<email của mình>"`.
3. Tải dữ liệu: `py scripts/download_public.py` (~1 GB; ra 250 ảnh + 50 ảnh calib). Mọi máy ra cùng 250 ảnh.
4. Sau khi N1 báo seed: `py scripts/inject_release.py --seed 11007 --out runs/r11007`, rồi tạo `runs/r11`, `runs/r22`, `runs/clean`, `runs/r33` (`--opaque`) như mục 0.
5. Đọc nhanh tài liệu (10 phút, tóm tắt miệng 1 phút cho nhóm): N1–N2 đọc [GUIDE.md](GUIDE.md); N3–N4 đọc [docs/DELIVERY.md](docs/DELIVERY.md); N5–N6 đọc [RUBRIC.md](RUBRIC.md).
6. Mở `runs/r11007/delivery/`, xem tận mắt: `manifest.json`, `metadata.json`, `jobs.csv`, một file `labels/*.txt`, `classes.txt`, `panoptic.json`, `guideline/changelog.md`, `incoming/ticket.md`.

**N1 (làm trước, song song):**
1. Fork/tạo repo từ repo đề (hỏi giảng viên đúng repo cần fork), đặt tên **`K5-L23-DAY10-NHOM11-Release`**, **Public**; mời 5 người còn lại với quyền write.
2. Đổi tiêu đề `README.md` thành `# Day 10 Lab — Nhóm 11` ngay bây giờ (đỡ quên lúc nộp).
3. Điền `submission/TEAM.md`: họ tên, MSHV, GitHub, phần chính của từng người, seed 11007, URL repo.
4. **Không chạy lại `run_lab.py`.** Chỉ kiểm: `runs/r11007/delivery/release.json` ghi `lab250_d3cc716c084b`; `runs/lineage.jsonl` có `inject` và `train R-021`.
5. Nhắn nhóm: seed, `release_id`, tên repo, giao diện module (mục 1), luồng file (mục 2).
6. Commit + push `P0: chia viec`.

### (B) Gate G0
- [ ] Mỗi người: Python ≥ 3.10; Pillow cài được; `data_source/` có 250 ảnh + calib.
- [ ] Mỗi người có `runs/r11007/delivery/release.json` = `lab250_d3cc716c084b`; có `runs/r11`, `r22`, `r33` (opaque), `clean` (50 ảnh).
- [ ] `submission/TEAM.md` đủ; mỗi người `git config user.name/email` của chính mình.
- [ ] Giao diện module chốt; commit `P0: chia viec` đã push; repo public đúng tên; README đã đổi tiêu đề.
- [ ] Mỗi người đã đọc phần tài liệu được giao và tóm tắt miệng.

### (C) Kết quả đạt được sau CP0
- 6 máy có **cùng** `release_id` (đối chiếu miệng); repo public có 6 thành viên; TEAM.md không còn `<<`; mỗi người biết vai, file sở hữu, và có bản tóm tắt tài liệu.
- Bằng chứng: `git log` có `P0: chia viec`; `git shortlog -sne HEAD` thấy đúng tên/email N1.

### (D) Nếu trễ
Tải dữ liệu chậm: một người tải xong thì chuyển `data_source/` qua ổ chung cho máy khác (không commit). Làm tài liệu sau, giữ nguyên giờ sang Pha 1.

---

## 4. Pha 1 — Bắt lỗi luật (0:15–0:55) → CP1

Mục tiêu: `validate.py` cho **F1 lỗi luật = 1,0** trên **seed 11007, 11, 22**, lô sạch **0 lỗi luật**, chạy ≤ 60 s/250 ảnh, chạy được trên lô `--opaque`.

### (A) Việc từng người
**Cả nhóm (5 phút đầu):** mở `runs/r11007/delivery/`, nhìn tận mắt các file ở G0 bước 6; xác nhận giao diện module.

**N2** (10 phút đầu: push `common.py`, sau đó `rules_file.py`):
1. `common.py`: hàm đọc manifest/metadata/jobs/classes/panoptic; đọc nhãn YOLO (bỏ dòng trống); `sha256_file(path)` mở `rb`; cache mask.
2. `missing_image`: ảnh có trong manifest nhưng file không tồn tại → báo, rồi **bỏ qua ảnh đó** ở mọi kiểm tra sau.
3. `wrong_hash`: tính sha256 thật của `image`, `label`, `mask` rồi so với `image_sha256/label_sha256/mask_sha256` của manifest (không chỉ kiểm dài 64 ký tự).
4. `scene_leak`: gom `metadata.json` theo `scene_id`; cảnh có cả `train` và `val` → **một** lỗi, target = `scene_id`.
5. `guideline_mismatch`: so `guideline_version` của ảnh với `guideline` của **job** trong `jobs.csv` (không so với ảnh khác).
6. `invalid_category_id`: `category_id` của segment không có trong `categories` (được viết ở N2 hoặc N3 — chốt: **N2** viết, đặt trong `rules_file.py`, vì chỉ cần `panoptic.json`).
7. Chạy trên 3 seed + clean; commit `P1: rules_file`.

**N3** (`rules_label.py`, `rules_panoptic.py`):
1. `invalid_class`: `class_id` ngoài 0–79.
2. `bbox_out_of_bounds`: `x±w/2` hoặc `y±h/2` vượt [0,1] quá **1 pixel** (dùng kích thước ảnh thật hoặc `panoptic.json`); dung sai nhỏ, chỉ nới nếu lô sạch báo thừa (box có thể chỉ tràn mép chút).
3. `duplicate_box`: cùng lớp, **cùng kích thước**, tâm lệch ≤ 2–3 pixel. Không dùng IoU thấp (COCO có cặp chồng tự nhiên tới IoU ≈ 0,66).
4. `thing_overlap`: dùng `scripts/pngutil.py` đọc mask, đếm pixel theo `id = R + G·256 + B·65536`, **bỏ id 0 và `iscrowd`**, báo khi `area` khai báo **lớn hơn** số pixel thật. Cache kết quả đếm (đọc PNG thuần Python chậm); dùng chung cache với N4.
5. Đo thời gian trên 250 ảnh; commit `P1: rules_label`.

**N4** (chuẩn bị Pha 2, chưa viết ghép hoàn chỉnh):
1. Đọc `pngutil.py`; viết hàm mask → với mỗi segment tính bbox và số pixel.
2. Thử trên 3–4 ảnh; phác bản ghép box YOLO (đổi sang pixel) với segment thing bằng IoU; ghép lớp qua tên (`classes.txt` ↔ `categories`).
3. In thử số cặp ghép được trên `runs/clean`; commit nháp `P1: crosscheck skeleton`.

**N5:**
1. `tools/viewer.py` (Pillow): nhận tên ảnh (có hoặc không đuôi) và đường dẫn `delivery`; vẽ box detection (màu một), viền segment panoptic (màu hai), ghi tên lớp; phóng to 2–3× cho ảnh nhỏ (~240×320); chế độ `--crop <box>` cắt quanh một box; lưu `runs/viewer_out/<tên>.png`.
2. Thử trên `runs/r11007` và `runs/r33` (tên `img_0001`); commit `P1: viewer`.
3. Bắt đầu nháp `tools/build_v2.py` theo bảng phân loại ở Pha 4.

**N6:**
1. `tools/trace_query.py <delivery> --out trace.json` theo tiêu chí Pha 5 (đọc `ticket.md`, `changelog.md` bằng **phân tích văn bản tổng quát**: lấy tên lớp bằng cách khớp với `classes.txt`, lấy `scene_<n>` bằng regex; **không** nhúng `bottle`/`scene_157` vào code).
2. Nháp `security.md` (ba mục), tạo khung `REPORT.md` và `prompts.md`.
3. QA: chạy validator trên seed 11, 22, 33 và clean khi N1 gộp xong, báo lỗi cho N2/N3.

**N1:**
1. Viết `validate.py` (argparse đúng CLI; gọi `rules_file`, `rules_label`, `rules_panoptic`; gộp, loại trùng `(type, target)`, áp thứ tự ưu tiên "mỗi ảnh một lỗi"; ghi `{"errors": [...]}`).
2. Nối trước phần `--candidates` (gọi `crosscheck.candidates` nếu module có; chưa có thì ghi `[]`).
3. Chạy và chấm tạm:
   ```powershell
   py -X utf8 validator/validate.py runs/r11007/delivery --out runs/r11007/rules.json
   Copy-Item runs/r11007/rules.json runs/r11007/errors.json
   py -X utf8 scripts/score_findings.py --run runs/r11007
   ```
   Lặp với `r11`, `r22` (cũng `Copy-Item` rồi chấm) và lô sạch (phải **0 lỗi**).
4. Kiểm chéo `file_rule_errors` của `check_handover.py`: validator phải báo **đủ** các lỗi luật mức file mà H2 tự thấy (không thiếu).
5. Thử `r33` (`--opaque`): không crash, chạy ≤ 60 s. Commit `P1: validate`.

### (B) Gate G1
- [ ] `score_findings.py`: **F1 lỗi luật = 1,0** trên **seed 11007, 11 và 22**.
- [ ] `runs/clean`: **0 lỗi luật** được báo.
- [ ] Validator ≤ **60 giây** cho 250 ảnh (mục tiêu nhóm).
- [ ] Chỉ import thư viện chuẩn + `pngutil`; không có đường dẫn tới `_private`, `data_source`, `cache`; không `urllib`/`socket`/`requests`.
- [ ] Không có tên ảnh, `scene_id` hay id của seed nằm cứng trong code (`Select-String -Path validator\*.py -Pattern "0000000|scene_|_private|data_source|urllib|socket|requests"` không ra gì).
- [ ] Chạy được trên `runs/r33` (`--opaque`, tên `img_0001`) không lỗi.
- [ ] Định dạng `{"errors": [{"type","target"}]}`, không trùng `(type, target)`, mỗi ảnh tối đa một lỗi.
- [ ] Mỗi người đã commit `P1: <module>`.

### (C) Kết quả đạt được sau CP1
- `validator/` chạy một lệnh ra `rules.json`; **F1 lỗi luật = 1,0 trên 3 seed, 0 báo thừa trên lô sạch** (ghi 3 con số + thời gian chạy vào ghi chú nhóm, để N6 đưa vào `REPORT.md` mục 1).
- Viewer vẽ được box + viền segment, phóng to được; `trace_query.py` có bản đầu; `build_v2.py` có nháp.
- Cả nhóm trả lời được 3 câu CP1: vì sao `wrong_hash` phải tính lại sha256; target của `scene_leak` là gì; vì sao `guideline_mismatch` so với job.

### (D) Nếu trễ
Chấp nhận thiếu **một luật hiếm**, miễn lô sạch không báo thừa. **Một người ở lại sửa** (N2/N3 theo luật lỗi); cả nhóm sang Pha 2 vì xem ảnh cần nhiều tay.

---

## 5. Pha 2 — Đối chiếu + xem ảnh (0:55–1:50) → CP2

Mục tiêu: `candidates.json` đủ 5 loại, hàng đợi ≤ ~80 ảnh, `review_log.csv` hoàn chỉnh, `errors.json` chốt, viewer sẵn sàng cho đề ẩn.

### (A) Việc từng người
**N4** (trọng tâm pha, hoàn thiện `crosscheck.py`):
1. Đổi box YOLO sang pixel; ghép mỗi box với segment thing có bbox gần nhất (IoU); ghép lớp qua tên.
2. Dùng **pixel mask**: cặp ghép đúng thì gần như toàn bộ pixel segment nằm trong box. Tỉ lệ pixel ra ngoài box lớn → `bbox_drift`. Một segment có pixel nằm trong **hai** box cùng lớp → `instance_merge`.
3. Cùng vị trí khác lớp → `class_swap` hoặc `category_swap` (chưa biết bên nào sai: ghi `guess`, để mắt người quyết).
4. Segment thing lớn không có box → `missing_box`. **Bỏ segment `iscrowd`.**
5. Đo nhiễu: chạy trên `runs/clean` (50 ảnh), ghi **số ứng viên thật**. Cùng N5 chọn ngưỡng sao cho hàng đợi ≤ ~80/250 ảnh mà không bỏ sót ở seed 11007 (so sánh hàng đợi với lỗi luật/`errors` chỉ ở mức F1 tổng của `score_findings.py`, **không dò từng ảnh**). Ghi lý do chọn ngưỡng.
6. Giữ `score` thang rõ ràng để sắp xếp. Cho phép vài ứng viên điểm thấp lọt hàng đợi để có ca `rejected` tự nhiên. Commit `P2: crosscheck`.

**N1:**
1. Nối `crosscheck` vào `validate.py`:
   ```powershell
   py -X utf8 validator/validate.py runs/r11007/delivery --out runs/r11007/rules.json --candidates runs/r11007/candidates.json
   ```
2. Pull `submission/r11007/review/` và `review_log.csv` khi N5 xong; chép vào `runs/r11007/`.
3. Gộp và chấm:
   ```powershell
   py -X utf8 scripts/merge_review.py --rules runs/r11007/rules.json --review runs/r11007/review_log.csv --out runs/r11007/errors.json
   py -X utf8 scripts/score_findings.py --run runs/r11007
   ```
4. Soát từng dòng `review_log.csv`: note ≥ 20 ký tự, không trùng, có tên người xem.

**N2, N3:** chạy lại validator trên 11007/11/22/clean sau khi N1 gộp; sửa báo thừa/sót; rồi chuyển sang hỗ trợ xem ảnh (nhận thêm hàng đợi nếu cần).

**N5:**
1. `tools/review_queue.py`: sắp ứng viên theo `score` giảm dần, chia 6 phần theo **vị trí `i mod 6`** (ảnh thứ i → người i), ghi `review_queue_<n>.txt`; tạo sẵn `review_<tên>.csv` có header `image,type,verdict,note`; thêm lệnh `merge` gộp 6 file thành `review_log.csv` (kiểm cột, `note` ≥ 20 ký tự, không trùng, `verdict` ∈ {confirmed, rejected}).
2. Phát viewer cho mọi người; chạy thử trên `runs/r33`.
3. Gộp `review_<tên>.csv` thành `review_log.csv`, push lên Git.

**Cả nhóm — xem ảnh (bắt buộc, ai cũng phải xem):**
1. Mở viewer cho từng ảnh trong hàng đợi của mình; nhìn vật thật; phóng to/cắt khi ảnh nhỏ.
2. Ghi `review_<tên>.csv`: `image,type,verdict,note` (`image` không đuôi; `type` là loại lỗi gán nhãn bạn kết luận). `verdict` = `confirmed` hoặc `rejected`.
3. `note` ≥ 20 ký tự, nói **thấy gì**, ghi **tên người xem**, không chép giống nhau; note có dấu phẩy thì bọc `"..."`. Tốt: `"[Lan] xe tải mui kín, detection ghi car, panoptic ghi truck đúng → class_swap"`. Xấu: `"có lỗi"`, `"OK"`.
4. Detection và panoptic bất đồng về lớp: ảnh cho biết bên nào sai. Detection sai → `class_swap`; panoptic sai → `category_swap`.
5. Lệch tự nhiên (vật bị che, crowd) → `rejected` kèm lý do.
6. Không dùng AI thay mắt; không dò điểm bằng `score_findings.py`.
7. Commit `P2: review_<tên>` (mỗi người đẩy file của mình).

**N6:** ghi số liệu thật vào `REPORT.md`: F1 theo nhóm lỗi (rule / cross_check / overall) trên 11007, 11, 22; số ứng viên trên lô sạch; số ảnh trong hàng đợi; ngưỡng đã chọn và lý do; trả lời "vì sao báo hết ứng viên làm F1 giảm" bằng **số của nhóm** (tính tay: nếu báo hết N ứng viên mà chỉ k thật thì precision = k/(k+FP), recall giữ, F1 giảm; nêu số cụ thể).

### (B) Gate G2
Lệnh kiểm lô sạch: `py -X utf8 validator/validate.py runs/clean/delivery --out runs/clean/rules.json --candidates runs/clean/candidates.json`
- [ ] **Số ứng viên trên lô sạch đã đo và ghi lại** (con số thật, vào `REPORT.md`).
- [ ] **Hàng đợi ≤ ~80 ảnh** cho 250 ảnh (6 người × 20 phút ÷ ~1,5 phút/ảnh); nếu vượt, siết ngưỡng/cải thiện ghép và ghi lý do.
- [ ] **F1 gán nhãn ≥ 0,6** (đủ điểm mục 1c); mục tiêu nhóm **≥ 0,8**. **F1 tổng ≥ 0,9.**
- [ ] `candidates.json` đúng định dạng; có đủ 5 loại: `class_swap`, `category_swap`, `bbox_drift`, `missing_box`, `instance_merge`.
- [ ] `review_log.csv`: cột `image,type,verdict,note`; mọi lỗi gán nhãn trong `errors.json` có đúng một dòng `confirmed`; mọi `note` ≥ 20 ký tự, nói thấy gì, ≥ 70% note khác nhau (H3); **có ít nhất vài dòng `rejected`** kèm lý do (hoặc `REPORT.md` chứng minh bằng số liệu lô sạch); ghi tên người xem; **cả 6 người đều có dòng review**.
- [ ] `class_swap`/`category_swap` phân biệt **bằng mắt**.
- [ ] Viewer chạy được trên lô `--opaque`, ảnh ~240×320 đủ rõ để quyết định.
- [ ] `REPORT.md` có câu trả lời "vì sao báo hết ứng viên làm F1 giảm" kèm P/R/F1 theo nhóm lỗi.

### (C) Kết quả đạt được sau CP2
- **Điểm đo:** F1 luyện tập theo từng nhóm (rule = 1,0; cross_check ≥ 0,8; tổng ≥ 0,9) — ghi bảng 3 seed vào `REPORT.md`.
- `runs/r11007/errors.json` **chốt** (lỗi luật + lỗi gán nhãn `confirmed`); `review_log.csv` có đủ 6 người, có `rejected`; hàng đợi đã đếm; số ứng viên lô sạch đã đo.
- Bằng chứng: `candidates.json`, `review_log.csv`, `errors.json` trên máy N1; đoạn REPORT mục 1–2.
- Cả nhóm trả lời được: lô sạch vẫn có ứng viên vì COCO lệch tự nhiên (vật bị che, crowd); báo hết ứng viên → FP tăng → precision và F1 giảm; làm sao biết `car` hay `truck` sai bên nào (nhìn ảnh).

### (D) Nếu trễ
Siết ngưỡng cho hàng đợi gọn, nhưng **vẫn ghi note thật** cho từng dòng; không bỏ note để chạy kịp. Cần thêm tay thì N2/N3 nhận thêm hàng đợi.

> **Lưu ý điểm:** F1 nhóm `cross_check_review` ≥ 0,6 mới đủ 5 điểm; 0,3 đến dưới 0,6 được một nửa. F1 tổng cao có thể che F1 nhãn thấp vì lỗi luật dễ bắt: **luôn nhìn cả F1 gán nhãn riêng**.

---

## 6. Pha 3 — Quyết định + lineage (1:50–2:05) → CP3

### (A) Việc từng người
**Cả nhóm (5 phút):** tính tỉ lệ lỗi v1 = `len(errors.json["errors"]) / 250` (mỗi ảnh một lỗi, mỗi `scene_leak` tính một ảnh). **> 2% (tức > 5 lỗi) → không Release (HOLD).** Trả lời miệng: vì sao ngưỡng theo tỉ lệ chứ không số lỗi tuyệt đối; đổi dataset không sửa được model đã train.

**N1 (máy có lineage):**
```powershell
py -X utf8 scripts/lineage.py record --event decision --release-id lab250_d3cc716c084b --decision HOLD
py -X utf8 scripts/lineage.py impact --release-id lab250_d3cc716c084b
```
Chụp/ghi dòng `R-021: affected=True action=review_or_retrain`. Chỉ ghi `decision` **một lần**.

**N6:** viết mục "Quyết định và lineage" trong `REPORT.md`: QC v1 = `<lỗi>/250 = x,x%` (con số thật), kết luận HOLD theo ngưỡng 2%, vì sao R-021 phải xem lại hoặc train lại (model R-021 học từ dữ liệu v1 có lỗi; sửa dataset sau đó **không** đổi trọng số đã học).

**N2–N5:** đọc mục này, mỗi người chuẩn bị trả lời một câu vấn đáp CP3.

### (B) Gate G3
- [ ] Tỉ lệ lỗi = `len(errors)/250`, ghi rõ mẫu số; > 2% → HOLD (≤ 2% → Release; kết luận theo số thật).
- [ ] `runs/lineage.jsonl` có dòng `decision HOLD` cho `lab250_d3cc716c084b`.
- [ ] `impact` in `R-021: affected=True action=review_or_retrain`.
- [ ] `REPORT.md` giải thích R-021.

### (C) Kết quả đạt được sau CP3
- Con số **QC v1 = X/250 = y,y%** chốt (dùng nguyên cho README v2 ở Pha 4 — không đổi sau đó trừ khi `errors.json` đổi).
- Lineage có HOLD v1 và `impact` đúng; REPORT mục 3 xong. Trả lời được "vì sao tỉ lệ chứ không số lỗi" (lô to nhỏ khác nhau; 5 lỗi/250 và 5 lỗi/25 000 rất khác) và "đổi dataset có sửa được model đã train không" (không).

### (D) Nếu trễ
Pha ngắn; N1 làm lệnh, N6 viết REPORT song song, phần còn lại sang chuẩn bị Pha 4 (đọc phân loại lỗi).

---

## 7. Pha 4 — Bàn giao v2, không ghi đè v1 (2:05–2:45) → CP4

Tạo `runs/r11007/handover/lab250_d3cc716c084b_v2/`. **Không sửa gì trong `delivery/`.**

### (A) Việc từng người
**Cả nhóm (10 phút đầu):** cùng phân loại từng lỗi trong `errors.json` theo bảng:

| Nhóm | Loại lỗi | Xử lý |
|---|---|---|
| Sửa ngay trong v2 | `wrong_hash` (mở ảnh kiểm trước: ảnh còn nguyên → chỉ manifest sai, ghi hash mới; ảnh hỏng → rework), `guideline_mismatch` (theo job), `scene_leak` (đưa cả cảnh về một split) | ảnh ở lại v2; ghi vào Ghi chú README |
| Rework, rời v2 | `missing_image`, `invalid_class`, `bbox_out_of_bounds`, `duplicate_box`, `class_swap`, `bbox_drift`, `missing_box` | vào `rework_queue.csv`, không có trong `images/`, `labels/` |
| Panoptic, ở lại v2 | `invalid_category_id`, `thing_overlap`, `category_swap`, `instance_merge` | ảnh ở lại v2; ghi trong Ghi chú để báo team panoptic |

**N5** viết `tools/build_v2.py` (commit trước; N1 chạy trên máy chủ). Thuật toán:
1. Đọc `delivery/` + `errors.json`.
2. Với mỗi ảnh thuộc nhóm rework → loại khỏi `images/`, `labels/`; ghi `rework_queue.csv` (`image,type,annotator,reviewer,action`; người gán/kiểm lấy theo **job** của ảnh trong `jobs.csv`; `action` là một câu hành động ngắn, ví dụ "Vẽ lại box quanh người bên trái").
3. Copy **nguyên byte** `images/`, `labels/` của các ảnh còn lại (không sửa tay nhãn). `wrong_hash`: mở ảnh bằng Pillow kiểm; nguyên vẹn → ghi hash thật vào `manifest.csv`; hỏng → chuyển rework (người xem quyết, ghi vào Ghi chú).
4. `manifest.csv` (`file,sha256`) cho **mọi** file trong `images/` và `labels/` (dạng `images/x.jpg`), hash tính từ file thật **trong v2**.
5. `label_summary.csv` (`class,count`) theo tên lớp trong `classes.txt`, dòng cuối `TOTAL`, đếm từ nhãn trong v2.
6. `truyvet.csv` (`image,scene_id,split,job_id,annotator,reviewer,guideline`): `guideline` theo **job**; mỗi cảnh **một split** (đưa cả cảnh về split đa số/đã chọn và ghi vào Ghi chú).
7. In ra số ảnh, số nhãn, danh sách ảnh rework/panoptic để N1 dán vào README.

**N1:**
1. `git pull --rebase`, chạy `build_v2.py`.
2. Viết `README.txt` theo `templates/README.txt`, **mọi số lấy từ file thật**, đúng định dạng `Khoá: giá trị`:
   - `Release: lab250_d3cc716c084b_v2` · `Parent: lab250_d3cc716c084b`
   - `Số ảnh:` = số file trong `images/` · `Số nhãn:` = dòng `TOTAL` của `label_summary.csv`
   - `Guideline: v1.2 (J01–J04), v1.3 (J05–J10)` (đọc lại `jobs.csv` của seed)
   - `QC v1: <số lỗi>/250 = x,x%` (đúng số mục `errors.json`; **số đầu tiên** sau `QC v1:` phải là số lỗi; không viết "khoảng")
   - `Kết luận v1: Hold — <lý do theo ngưỡng 2%>` (từ đầu tiên đúng `Hold` nếu > 2%)
   - `Kết luận v2: <Release | Hold | Rework> — <đã tách gì, sửa gì, còn gì>`. Gợi ý: tính tỉ lệ ảnh còn lỗi trong v2 (chỉ lỗi panoptic) trên số ảnh v2; ≤ 2% → Release (ghi rõ còn lỗi panoptic báo team panoptic), > 2% → Hold.
   - `Ghi chú:` nói đã sửa gì (split cho cảnh nào, hash đã mở ảnh kiểm, guideline theo job), ảnh rework giao cho ai (A/Q mã người), ảnh lỗi panoptic ở lại v2 (liệt kê tên) để báo team panoptic.
3. Chốt, đóng gói, ghi lineage, kiểm:
   ```powershell
   py -X utf8 scripts/pack_release.py runs/r11007/handover/lab250_d3cc716c084b_v2
   py -X utf8 scripts/lineage.py record --event release --release-id lab250_d3cc716c084b_v2 --parent lab250_d3cc716c084b
   py -X utf8 scripts/check_handover.py --run runs/r11007
   ```
   Đổi bất kỳ file nào trong v2 sau khi đóng gói → chạy lại `pack_release.py` (H15). Chỉ ghi event `release` **một lần**, sau khi nội dung v2 đã chốt.

**N2, N3:** kiểm chéo thủ công v2: số ảnh, nhãn không bị sửa (so hash với `delivery/`), hash đúng, không cảnh nào ở hai split, ảnh trong rework có lỗi trong `errors.json`; chạy lại validator ở những phần áp dụng được trên cấu trúc v2.

**N4:** soát chéo `rework_queue.csv` (đủ cột; không ảnh panoptic-only trong đó; mỗi ảnh một lỗi).

**N6:** viết `REPORT.md` mục 4 (hash chứng minh/không chứng minh) và mục "không ghi đè v1"; chuẩn bị bước truy vết.

### (B) Gate G4
- [ ] **H1:** `delivery/` (v1) không bị sửa; mọi việc ở `handover/`.
- [ ] v2 đủ 7 phần: `images/`, `labels/`, `rework_queue.csv`, `manifest.csv`, `label_summary.csv`, `truyvet.csv`, `README.txt`.
- [ ] `images/`, `labels/` copy nguyên byte từ v1 (trừ ảnh rework); nhãn không sửa tay (H7).
- [ ] Phân loại sửa/rework/giữ đúng bảng; ảnh chỉ lỗi panoptic **ở lại** v2 (H5).
- [ ] `rework_queue.csv` đúng cột; người gán/kiểm đúng `jobs.csv` (H6); mọi ảnh có lỗi trong `errors.json`.
- [ ] `manifest.csv` đủ file, hash đúng (H8); `label_summary.csv` khớp (H9); `truyvet.csv` theo job, không cảnh nào hai split (H10, H11).
- [ ] `README.txt`: `QC v1` đúng; kết luận v1 và v2 đúng ngưỡng 2%; Ghi chú đủ; không "khoảng" (H12, H13).
- [ ] Lineage có HOLD v1 và release v2 `--parent` v1 (H14); `.sha256` khớp (H15).
- [ ] `check_handover.py` (bản gốc) chỉ còn FAIL ở H16/H17 nếu chưa làm.
- [ ] `REPORT.md` giải thích hash (chứng minh file không đổi so với khi lập manifest; **không** chứng minh nhãn đúng).

### (C) Kết quả đạt được sau CP4
- Thư mục `handover/lab250_d3cc716c084b_v2/` + `.sha256`, không `.zip` trong git.
- **`check_handover.py`: H1–H15 PASS** (H16/H17 chờ Pha 5/6a). Ghi dòng "Tổng: x PASS, y FAIL" vào ghi chú nhóm.
- Cả nhóm trả lời được: lỗi nào sửa trong v2, lỗi nào rework; hash chứng minh/không chứng minh gì; vì sao không ghi đè v1 (người dùng/model đã tham chiếu v1; truy vết; id lô = hash nội dung nên sửa v1 là đổi id).
- Mỗi người (N1, N5, N6 chắc chắn) giải thích được một số trong README v2.

### (D) Nếu trễ
Ưu tiên cho `check_handover.py` hết FAIL trước, chỉnh câu chữ README sau.

---

## 8. Pha 5 — Truy vết ticket (2:45–3:05) → CP5

### (A) Việc từng người
**Cả nhóm (5 phút):** đọc `incoming/ticket.md` và `guideline/changelog.md`; xác định lớp bị đổi quy tắc (**bottle**), cảnh team AI báo (**scene_157, scene_511**), job còn guideline cũ v1.2 (**J01–J04** theo `jobs.csv`).

**N6:**
```powershell
py -X utf8 tools/trace_query.py runs/r11007/delivery --out runs/r11007/trace.json
```
- `tier_a`: ảnh trong các cảnh team AI nêu, job guideline cũ, có ≥ 1 box detection (trong `labels/`) thuộc lớp bị đổi quy tắc.
- `tier_b`: ảnh khác cùng điều kiện (job guideline cũ, có lớp đó) chưa ai báo.
- `notify`: mã người gán và người kiểm của các job chứa ảnh tầng a và b.
- Guideline lấy theo **job** (`jobs.csv`), không theo ảnh (có thể chính là `guideline_mismatch`). "Có lớp" = có box detection trong `labels/` (không tính mask).
- Chạy thêm trên `runs/r11`, `runs/r22`, `runs/r33` (đổi lớp/cảnh khác) để chắc code tổng quát.

**N1:** `py -X utf8 scripts/score_findings.py --run runs/r11007` (chấm truy vết), chép `trace.json` vào `runs/r11007/`, rồi `check_handover.py` (H16).

**N4:** soát chéo: đếm lại bằng tay một lớp (ví dụ đếm ảnh có box `bottle` trong job v1.2) và so với `tier_a ∪ tier_b`.

**N6** ghi vào `REPORT.md` mục 5: tiêu chí đã dùng (guideline theo job; "có lớp" = box detection trong `labels/`; vì sao).

**Cả nhóm:** trả lời câu bấm dừng: **vì sao không được bỏ tầng b, và phải báo cho ai?** Nguyên nhân gốc ở các job còn guideline cũ, không ở hai cảnh trong ticket; cùng điều kiện ở cảnh khác cũng sinh cùng lỗi; phải báo **người gán và người kiểm của mọi job liên quan, ở cả hai tầng**.

### (B) Gate G5
- [ ] `trace.json` có ba khoá `tier_a`, `tier_b`, `notify` (list).
- [ ] `tier_a` và `notify` không rỗng; ảnh trong `tier_a ∪ tier_b` có thật trong lô; mã người **có trong `jobs.csv`** (H16).
- [ ] F1 truy vết (tier_a, tier_b, notify) mục tiêu nhóm **≥ 0,9** (cố gắng 1,0) trên seed luyện tập.
- [ ] `trace_query.py` chạy được trên `runs/r33` (tên `img_0001`) mà không sửa code.
- [ ] Không dùng guideline của ảnh; không dùng `masks/`.
- [ ] `REPORT.md` nêu tiêu chí.

### (C) Kết quả đạt được sau CP5
- `trace.json` đúng và `score_findings` cho **F1 truy vết = 1,0** (hoặc ≥ 0,9 kèm giải thích phần lệch); `check_handover.py`: H1–H16 PASS (còn H17 chờ security).
- REPORT mục 5 xong. Cả nhóm trả lời tầng a vs tầng b, vì sao theo job.

### (D) Nếu trễ
Nhờ N4 đếm tay đối chiếu; ưu tiên `tier_a` + `notify` không rỗng (H16) trước, tinh chỉnh `tier_b` sau.

---

## 9. Pha 6a — Bảo mật + khoá repo (3:05–3:15) → CP6a

### (A) Việc từng người
**Cả nhóm:** mỗi người đọc nháp `security.md` của N6 và bổ sung một ý; **cùng lướt ảnh** (bằng viewer) để chọn ít nhất **một ảnh có người nhìn rõ mặt** trong lô; ghi **tên ảnh đúng như trong lô** (ví dụ dạng `0000000xxxxx`), đã kiểm bằng mắt.

**N6:** hoàn thiện `runs/r11007/security.md` theo `templates/security.md`: **ba mục `##`**, mỗi mục ≥ 80 ký tự nội dung, **không còn `<<`**; giữ nguyên tiêu đề mục 3 có cụm "khuôn mặt" (H17 dò tiêu đề).
1. **Ca USB:** không chép lô về nhà, cũng không gửi email cá nhân hay nhờ người khác làm hộ; xin gia hạn hoặc truy cập từ xa hợp lệ; nêu thay thế cụ thể.
2. **Năm việc được/không (gắn với lô này):** mở job được giao trên máy công ty (**được**); chụp màn hình gửi người quen (**không**); chép lô ra USB (**không**); dán nhãn thật lên chatbot (**không**); đưa tài khoản CVAT cho đồng nghiệp (**không**). Mỗi việc nêu lý do.
3. **Ca khuôn mặt:** kết luận **Hold** (chữ "Hold" có trong mục) + báo người phụ trách; **nêu tên ảnh cụ thể**; giải thích vì sao không tự làm mờ/xoá (đổi dữ liệu khi chưa được phép, mất dấu vết, lệch lineage/hash).

**N1:**
1. Chép `security.md` vào `runs/r11007/`; chạy `check_handover.py`; sửa mọi FAIL.
2. Chạy `py -X utf8 scripts/export_submission.py --run runs/r11007` (xuất lại sau mỗi chỉnh sửa cuối).
3. Kiểm repo: `git ls-files | Select-String -Pattern "data_source|runs/|\.zip$"` và `git diff --stat -- scripts/` **không in gì**; `git shortlog -sne HEAD` đủ 6 người ≥ 2 commit.

**N2–N5:** làm **checklist trước khi nhận đề ẩn** (40 phút không đủ để viết công cụ):
- [ ] Validator chạy được trên seed khác (r11, r22, r33) và trên lô sạch.
- [ ] Viewer vẽ box + viền segment, phóng to, chạy được trên `img_0001`.
- [ ] `review_queue.py` chia hàng đợi chạy được trên `runs/r33`.
- [ ] `merge_review.py` đã chạy thử một lần với `review_log.csv` giả (chỉ để thử luồng, không dùng làm kết quả).
- [ ] `trace_query.py` chạy được trên `runs/r33`.
- [ ] Mọi người đã `pull`, đã commit/push gọn, cùng biết cách chia ảnh.
- [ ] Bài tập nháy (5 phút, chọn một người): chạy cả chuỗi `validate → candidates → queue → merge → trace` trên `runs/r33` và bấm giờ; ghi thời gian từng bước.

### (B) Gate G6
- [ ] `security.md` đủ ba mục, ca khuôn mặt Hold + báo + ảnh cụ thể có trong lô (H17).
- [ ] **`check_handover.py --run runs/r11007`: 0 FAIL** (H1–H17), chạy bản gốc.
- [ ] `export_submission.py --run runs/r11007` chạy xong; `submission/lineage.jsonl` đã có; `submission/r11007/` có `errors.json, candidates.json, review_log.csv, trace.json, security.md, handover/<id>_v2/` và `<id>_v2.sha256`.
- [ ] README tiêu đề `# Day 10 Lab — Nhóm 11`.
- [ ] `git ls-files` sạch (không `data_source/`, `runs/`, `*.zip`, `delivery/`).

### (C) Kết quả đạt được sau CP6a
- **0 FAIL** (17 mã PASS), repo nộp phần luyện tập **hoàn chỉnh và đã push**; checklist trước đề ẩn đã tick; có bảng thời gian một vòng chạy thử `runs/r33`.
- Điểm chắc: mục 3 (25đ), 4b (4đ), 5 (5đ) cơ bản đã đủ bằng chứng.

### (D) Nếu trễ
Ưu tiên 0 FAIL trước; `security.md` ngắn mà đủ ba mục, có Hold và tên ảnh thật.

---

## 10. Pha 6b — Đề ẩn (3:15–3:55, 40 phút) → CP6b

Đề ẩn: 250 ảnh khác (tên dạng `img_0001`), có thể lật/nén lại, mức lỗi có thể khác. **Validator không được dựa vào tên ảnh, nhãn gốc hay tham số `inject_release.py`.**

### Phân thời gian (phút từ lúc nhận đề)

| Phút | Ai | Việc | Lệnh / đầu ra |
|---|---|---|---|
| 0–3 | **N1 tải; cả nhóm giải nén** | Tải `de_an.zip` (tab Releases hoặc LMS), chia sẻ cho cả nhóm; **mỗi người giải nén ra thư mục gốc repo** (để có `delivery/` xem ảnh). **Không commit `delivery/`.** | `delivery/` |
| 3–6 | N1 | Chạy validator | `py -X utf8 validator/validate.py delivery --out submission/de_an/rules.json --candidates submission/de_an/candidates.json` |
| 3–6 | N6 | Chạy truy vết | `py -X utf8 tools/trace_query.py delivery --out submission/de_an/trace.json` |
| 6–8 | N5 | Chia ứng viên đều 6 người (`id mod 6`), push hàng đợi (`submission/de_an/queue/`), cả nhóm `pull` | `review_queue_<n>.txt`, `review_<tên>.csv` |
| 8–28 | **Cả nhóm** | Xem ảnh bằng viewer; mỗi người ghi `review_<tên>.csv` (note ≥ 20 ký tự nói thấy gì; phân biệt class_swap/category_swap bằng ảnh; **mọi lỗi gán nhãn nộp phải có dòng `confirmed`**) | push file của mình |
| 28–33 | N5 gộp; N1 chạy merge | `review_log.csv` → `errors.json` | `py -X utf8 scripts/merge_review.py --rules submission/de_an/rules.json --review submission/de_an/review_log.csv --out submission/de_an/errors.json` |
| 33–37 | N2, N3, N4 soát lỗi luật + ca còn nghi, kiểm định dạng `errors.json`; N6 soát `trace.json` (ba khoá, tên ảnh có thật); đối chiếu tổng số lỗi hợp lý | | |
| 37–40 | **N1** | Commit + push `submission/de_an/` gồm `errors.json`, `candidates.json`, `review_log.csv`, `trace.json` | `git add submission/de_an; git commit; git push` |

Nguyên tắc: **không trao đổi kết quả với nhóm khác**. Nếu lỗi gán nhãn nào chưa có `confirmed` thì bị bỏ khỏi chấm: soát một lần trước khi push.

### (B) Gate G7
- [ ] Validator chạy trên `delivery/` đề ẩn không lỗi (chạy < 60 s).
- [ ] Cả 6 người đều xem ảnh trong hàng đợi chia theo `id mod 6`; `review_log.csv`: mọi lỗi gán nhãn có `confirmed`, note ≥ 20 ký tự nói thấy gì.
- [ ] `class_swap`/`category_swap` dựa vào ảnh.
- [ ] `submission/de_an/` có đủ 4 file; đã commit + push; **không** commit `delivery/` đề ẩn.

### (C) Kết quả đạt được sau CP6b
- `submission/de_an/` đủ 4 file trên GitHub; repo vẫn sạch; CP6a vẫn 0 FAIL (không ai đụng `runs/r11007`).
- Điểm mục 1, 2a/2c, 4a phụ thuộc đúng bước này; ưu tiên **đúng và có note thật** hơn nhiều.

### (D) Nếu trễ
Hết phút 33 mà chưa xem xong: giữ các dòng `confirmed` đã chắc, **không** thêm ứng viên chưa xem vào `errors.json`; push đúng giờ.

---

## 11. Nộp bài

**N1 đối chiếu danh sách cuối (cả nhóm đọc cùng):**
- [ ] Repo public `K5-L23-DAY10-NHOM11-Release`; README tiêu đề `# Day 10 Lab — Nhóm 11`.
- [ ] `validator/validate.py` chạy được, chỉ đọc delivery, lô sạch không báo lỗi luật.
- [ ] `submission/`: `TEAM.md` (đủ, không `<<`), `REPORT.md`, `prompts.md` (không còn dòng mẫu `<<>>`), `lineage.jsonl`, `r11007/` (errors, candidates, review_log, trace, security, `handover/<id>_v2/` và `.sha256`, không `.zip`), `de_an/`.
- [ ] `REPORT.md` trả lời **5 câu**, mọi số lấy từ file/lệnh thật: (1) vì sao báo hết ứng viên làm F1 giảm (số của nhóm); (2) số ứng viên lô sạch, ngưỡng đã chọn và lý do; (3) vì sao R-021 phải xem lại/train lại; (4) hash chứng minh gì / không chứng minh gì; (5) tiêu chí truy vết (guideline theo job). Mục 6: bug `scripts/` nếu có.
- [ ] Mọi lỗi gán nhãn có dòng `confirmed` kèm ghi chú cụ thể.
- [ ] Không commit `data_source/`, `runs/`, `*.zip`, `delivery/`; `scripts/` không sửa (`git diff --stat -- scripts/` rỗng).
- [ ] Mỗi người ≥ 2 commit có nội dung, đúng tên và email.
- [ ] Nộp link repo lên LMS https://aithucchien.vinuni.edu.vn (hoặc kênh giảng viên chỉ định). Sau khi nộp: clone repo ở thư mục mới và kiểm `git ls-files` thấy đủ cấu trúc.

---

## 12. Điều kiện PASS theo từng người (tick cuối)

### N1 — Trưởng nhóm, máy chủ release
- [ ] `TEAM.md` đủ; commit `P0` đúng giờ; repo public đúng tên; README đổi tiêu đề.
- [ ] `validate.py` đúng CLI, gọi đủ module (có `try/except`), ghi `rules.json`/`candidates.json`; không đọc nguồn cấm.
- [ ] Lineage: HOLD, release v2 có parent; `impact` ra `R-021: affected=True`.
- [ ] README v2 đúng mẫu, số lấy từ file thật; `check_handover.py` 0 FAIL; `export_submission.py` xong; nộp link LMS.
- [ ] Soát từng dòng `review_log.csv`; ≥ 2 commit; có dòng review của mình.

### N2 — Luật file + metadata
- [ ] `common.py` dùng được trong 10 phút đầu Pha 1.
- [ ] `missing_image`, `wrong_hash` (rb; image/label/mask), `scene_leak`, `guideline_mismatch` (theo job), `invalid_category_id`: F1 = 1,0 trên 11007/11/22, 0 báo nhầm ở lô sạch.
- [ ] Sửa theo báo lỗi của N6 (QA); ≥ 2 commit; có dòng review.

### N3 — Luật nhãn + panoptic
- [ ] `invalid_class`, `bbox_out_of_bounds` (dung sai < 1 px), `duplicate_box` (cùng lớp, cùng kích thước, tâm lệch ≤ 2–3 px), `thing_overlap` (id = R + G·256 + B·65536, bỏ id 0 và `iscrowd`, so với `area`): F1 = 1,0 trên 3 seed, 0 báo nhầm ở lô sạch.
- [ ] Đo thời gian `thing_overlap` 250 ảnh; tổng ≤ 60 s (cache). ≥ 2 commit; có dòng review.

### N4 — Đối chiếu det ↔ panoptic
- [ ] Ghép IoU + tên lớp; dùng pixel mask cho `bbox_drift`/`instance_merge`; bỏ `iscrowd`.
- [ ] `candidates.json` đủ 5 loại, có `score`; số ứng viên lô sạch đã đo; ngưỡng có lý do bằng số liệu.
- [ ] Hàng đợi ≤ ~80; không bỏ sót ca thật vì ngưỡng quá chặt. ≥ 2 commit; có dòng review.

### N5 — Viewer + dựng v2
- [ ] `viewer.py`: box (màu một), viền segment (màu hai), tên lớp, phóng to 2–3×, cắt vùng; chạy trên `img_0001`.
- [ ] `review_queue.py`: sắp theo `score`, chia 6 phần theo `id mod 6`, ghi/gộp `review_<tên>.csv` đúng cột.
- [ ] `build_v2.py` tạo đủ 7 phần, đúng quy tắc, không sửa nhãn tay, không đụng `delivery/`.
- [ ] ≥ 2 commit; có dòng review.

### N6 — Truy vết, bảo mật, báo cáo, QA
- [ ] `trace_query.py` đạt G5, chạy được trên đề ẩn (không nhúng `bottle`/scene cứng).
- [ ] `security.md` đạt G6 (H17).
- [ ] `REPORT.md` đủ 5 mục + bug `scripts/` (nếu có); `prompts.md` đủ cột (prompt, AI sai ở đâu, kiểm lại thế nào).
- [ ] QA: chạy validator trên seed 11, 22, 33 (`--opaque`) và `runs/clean`; báo lỗi cho N2/N3. ≥ 2 commit; có dòng review.

## 13. Quy đổi sang điểm RUBRIC

| # | Hạng mục | Điểm | Điều kiện đạt tối đa | Gate |
|---|---|---:|---|---|
| 1a | F1 tuyệt đối đề ẩn | 20 | `rank F1` ≥ 0,9 (điểm = 20 × F1; < 0,5 thì 0) | G1, G2, G7 |
| 1b | Xếp hạng giữa các nhóm | 10 | Đứng đầu | G7 |
| 1c | F1 lỗi gán nhãn đề ẩn | 5 | F1 `cross_check_review` ≥ 0,6 (0,3–0,6: một nửa) | G2, G7 |
| 2a | Mọi lỗi gán nhãn có `confirmed` (đề ẩn) | 8 | Ghi chú nói rõ thấy gì | G7 |
| 2b | Phân biệt lỗi vs lệch tự nhiên | 4 | Có dòng `rejected` kèm lý do, hoặc `REPORT.md` đo lô sạch | G2 |
| 2c | Phân biệt `class_swap`/`category_swap` | 3 | Dựa vào ảnh | G7 |
| 3a | `check_handover.py` không FAIL | 10 | 0 FAIL, bản gốc | G4, G6 |
| 3b | `rework_queue.csv` + `README.txt` | 6 | Giao đúng người, đúng ngưỡng 2%, Ghi chú đủ | G4 |
| 3c | Lineage | 5 | HOLD v1, release v2 có parent, giải thích R-021 | G3, G4 |
| 3d | Không ghi đè | 4 | v1 giữ nguyên, `REPORT.md` giải thích hash | G4 |
| 4a | Truy vết đề ẩn | 6 | Trung bình F1 `tier_a`, `tier_b`, `notify` = 1 | G7 |
| 4b | Truy vết seed luyện tập | 4 | `trace.json` đúng + tiêu chí trong `REPORT.md` | G5 |
| 5 | Bảo mật | 5 | `security.md` đủ ba mục, Hold + báo, ví dụ thật | G6 |
| 6a | Commit | 4 | Mỗi người ≥ 2 commit có nội dung, thứ tự hợp lý theo pha | mục 11 |
| 6b | Dùng AI minh bạch | 3 | `prompts.md` đủ | mục 11 |
| 6c | `REPORT.md` | 3 | Đủ 5 mục, số liệu thật | mục 11 |

Vấn đáp (~3 phút/người, ngẫu nhiên): ai không trả lời được thì phần điểm cá nhân (mục 6) tối đa một nửa.

## 14. Mã H1–H17 của `check_handover.py` và cách tránh FAIL

| Mã | Kiểm | Cách tránh |
|---|---|---|
| H1 | v1 giữ nguyên (release_id, hash nhãn/mask) | Không sửa `delivery/`. Lỡ sửa: tạo lại lô cùng seed bằng `inject_release.py` (không chạy `run_lab.py`) |
| H2 | `errors.json` có đủ lỗi luật mức file mà bộ kiểm tự thấy | Validator đủ 7 luật mức file; dùng đúng `rules.json` → merge |
| H3 | Mọi lỗi gán nhãn có `confirmed`; **mọi** note ≥ 20 ký tự; ≥ 70% note khác nhau | Viết note riêng từng dòng; cả dòng `rejected` cũng ≥ 20 ký tự |
| H4 | v2 đủ 7 phần | Chạy `build_v2.py` đủ |
| H5 | `images/`=`labels/`; ảnh lỗi detection/thiếu file ở rework; ảnh rework phải có lỗi trong `errors.json`; ảnh panoptic-only **ở lại** | Dùng bảng phân loại; không đưa ảnh không lỗi vào rework |
| H6 | Rework đúng người gán/kiểm theo job | Lấy `annotator/reviewer` từ `jobs.csv` theo `job_id` của ảnh |
| H7 | Nhãn v2 = nhãn v1 (hash) | Copy nguyên byte |
| H8 | `manifest.csv` đủ file, hash đúng | Lập lại manifest sau mọi thay đổi, rồi pack |
| H9 | `label_summary.csv` khớp nhãn v2 | Đếm từ `labels/` của v2, tên lớp theo `classes.txt`, dòng `TOTAL` |
| H10–H11 | `truyvet.csv` theo job; cảnh một split | Guideline theo job; sửa split cả cảnh |
| H12 | README: Release, Parent, Số ảnh, Số nhãn khớp | Lấy số từ file thật |
| H13 | `QC v1: a/b` khớp `errors.json`; kết luận v1 đúng 2%; có kết luận v2; khớp lineage | Từ đầu của kết luận là `Hold`/`Rework`/`Release` |
| H14 | Lineage HOLD v1 và release v2 có parent | Ghi đúng `release_id`, `--parent` |
| H15 | `.sha256` khớp nội dung hiện tại | Chạy lại `pack_release.py` sau mọi sửa |
| H16 | `trace.json`: ba khoá; `tier_a`, `notify` không rỗng; ảnh/người có thật | `trace_query.py` đúng |
| H17 | `security.md`: ≥ 3 mục ≥ 80 ký tự; mục "khuôn mặt" có `Hold` + tên ảnh thật; không `<<` | Giữ tiêu đề có "khuôn mặt"; không để placeholder |

## 15. Bẫy hay gặp

- `wrong_hash` báo nhầm: hash trên bytes, mở `rb`.
- `thing_overlap` báo cả lô: so với `area`, bỏ id 0, đếm theo `R + G·256 + B·65536`, bỏ `iscrowd`.
- Ứng viên quá nhiều: đo trên lô sạch, dùng pixel mask, bỏ `iscrowd`.
- `duplicate_box` báo nhầm ở mép: kiểm theo kích thước + độ lệch tâm.
- H5 FAIL: ảnh chỉ lỗi panoptic ở lại v2, không vào rework.
- H1 FAIL: lỡ sửa `delivery/` → tạo lại lô cùng seed; chỉ làm trong `handover/`.
- H8 FAIL: sửa file sau khi lập manifest → lập lại manifest rồi pack.
- H13 FAIL: `QC v1:` phải là `<số lỗi>/250`, số đầu tiên đúng `errors.json`.
- `git shortlog -sne` không kèm `HEAD` có thể treo đợi stdin: dùng `git shortlog -sne HEAD`.
- `run_lab.py` chạy lần hai gắn thêm R-021 vào lineage: **không chạy lại.**
- Đề ẩn: validator không dựa vào tên ảnh, nhãn gốc hay tham số `inject_release.py`; chạy thử `runs/r33` (`--opaque`).
- Số liệu giả hoặc sửa `scripts/` → 0 điểm phần liên quan.

## 16. Ôn vấn đáp / bài kiểm tra về repo (cả nhóm, 10 phút)

Mỗi người: (1) giải thích một đoạn validator của mình và biết sửa khi đổi yêu cầu (N2, N3, N4; N1 cho `validate.py`; N5/N6 cho viewer/trace); (2) giải thích một dòng `confirmed`/`rejected` của chính mình: đã thấy gì trong ảnh; (3) giải thích một con số trong `README.txt` v2 (số ảnh, số nhãn, QC v1/250).

| Câu hỏi | Đáp án ngắn |
|---|---|
| Báo hết ứng viên vì sao F1 giảm? | Phần lớn ứng viên là lệch tự nhiên của COCO → thành FP; precision = TP/(TP+FP) tụt; recall không tăng thêm đáng kể → F1 giảm. Nêu số: lô sạch có `<số ứng viên>` ứng viên, hàng đợi `<n>`, F1 gán nhãn `<giá trị thật>`. |
| `wrong_hash` vì sao phải tính lại sha256? | Kiểm 64 ký tự chỉ kiểm định dạng; phải hash bytes thật rồi so. |
| `scene_leak` target là gì? | `scene_id`, một lỗi mỗi cảnh có ảnh ở cả train và val. |
| `guideline_mismatch` vì sao so với job? | Guideline chuẩn nằm ở job; so với ảnh khác thì không biết bên nào đúng. |
| Lô sạch vì sao vẫn có ứng viên? | COCO vốn lệch giữa detection và panoptic (vật bị che, crowd). |
| `car` (detection) vs `truck` (panoptic) sai bên nào? | Mở ảnh: detection sai → `class_swap`; panoptic sai → `category_swap`. |
| Ngưỡng theo tỉ lệ, không theo số lỗi? | Số lỗi tuyệt đối không so được giữa lô to/nhỏ; > 2% ảnh lỗi → không Release. |
| Đổi dataset có sửa model đã train? | Không; R-021 đã học từ v1 nên phải xem lại hoặc train lại. |
| Hash chứng minh gì / không? | Chứng minh file không đổi so với lúc lập manifest; **không** chứng minh nhãn đúng. |
| Vì sao không ghi đè v1? | Giữ dấu vết và id (id = hash nội dung); bên đã dùng v1 vẫn tham chiếu được; lineage cần v1 → v2 có parent. |
| Lỗi nào sửa trong v2, lỗi nào rework? | Sửa: wrong_hash/guideline_mismatch/scene_leak. Rework: lỗi nhãn detection + thiếu file. Panoptic-only: ở lại, báo team panoptic. |
| `tier_a` khác `tier_b`? | a: ảnh trong cảnh team AI báo + job guideline cũ + có box lớp đổi; b: cùng điều kiện nhưng cảnh khác, chưa ai báo. |
| Vì sao không bỏ tầng b, phải báo ai? | Nguyên nhân gốc ở job guideline cũ; phải báo người gán + người kiểm của mọi job liên quan ở cả hai tầng. |
| Vì sao guideline theo job? | Guideline từng ảnh có thể chính là lỗi `guideline_mismatch`. |
| Thấy mặt người rõ trong lô? | Hold lô + báo người phụ trách; không tự làm mờ/xoá (đổi dữ liệu khi chưa được phép, mất dấu vết). Nêu ảnh cụ thể. |
| Vì sao validator không được đọc `_private`/`data_source`? | Đó là đáp án/nguồn gốc; đề ẩn không có; đọc là 0 điểm mục 1. |

## 17. Lệnh tự kiểm tra nhanh (từ gốc repo)

```powershell
# Lỗi luật trên 3 seed + lô sạch
foreach ($s in 11007,11,22) {
  py -X utf8 validator/validate.py runs/r$s/delivery --out runs/r$s/rules.json
  Copy-Item runs/r$s/rules.json runs/r$s/errors.json   # chỉ để chấm tạm ở CP1
  py -X utf8 scripts/score_findings.py --run runs/r$s
}
py -X utf8 validator/validate.py runs/clean/delivery --out runs/clean/rules.json --candidates runs/clean/candidates.json
py -X utf8 validator/validate.py runs/r33/delivery --out runs/r33/rules.json --candidates runs/r33/candidates.json   # opaque

# Bàn giao
py -X utf8 scripts/check_handover.py --run runs/r11007
py -X utf8 -m unittest discover -s tests

# Kiểm repo sạch (hai lệnh đầu phải không in gì)
git ls-files | Select-String -Pattern "data_source|runs/|\.zip$"
git diff --stat -- scripts/
git shortlog -sne HEAD
```

> Chú ý: `Copy-Item rules.json errors.json` làm **trước** `merge_review.py` ở CP2 sẽ bị `merge_review.py` ghi đè — đúng ý. Không chép lại `rules.json` thành `errors.json` sau CP2.

## 18. Điều kiện PASS cuối cùng trước khi nộp (mọi dòng phải tick)

**Kết quả đo**
- [ ] F1 lỗi luật = 1,0 trên seed 11007, 11, 22 và 0 lỗi luật trên `runs/clean`.
- [ ] F1 tổng ≥ 0,9; F1 gán nhãn ≥ 0,6 (mục tiêu nhóm ≥ 0,8) trên seed luyện tập.
- [ ] F1 truy vết ≥ 0,9 (mục tiêu 1,0) trên seed luyện tập.
- [ ] `check_handover.py --run runs/r11007`: 0 FAIL (bản gốc).
- [ ] `py -X utf8 -m unittest discover -s tests` không lỗi.

**Repo và cấu trúc nộp** (theo [SUBMISSION.md](SUBMISSION.md))
- [ ] Repo public `K5-L23-DAY10-NHOM11-Release`; README tiêu đề `# Day 10 Lab — Nhóm 11`.
- [ ] Có `validator/validate.py`, `submission/TEAM.md`, `REPORT.md`, `prompts.md`, `lineage.jsonl`.
- [ ] Có `submission/r11007/` (`errors.json`, `candidates.json`, `review_log.csv`, `trace.json`, `security.md`, `handover/<release_id>_v2/` và `<release_id>_v2.sha256`).
- [ ] Có `submission/de_an/` (`errors.json`, `candidates.json`, `review_log.csv`, `trace.json`).
- [ ] **Không** có `data_source/`, `runs/`, `*.zip`, `delivery/` của đề ẩn, secret trong repo.
- [ ] `scripts/` không bị sửa.

**Trung thực**
- [ ] Mọi số trong `README.txt` và `REPORT.md` lấy từ file/lệnh thật.
- [ ] Mọi dòng `confirmed`/`rejected` là kết luận của một người trong nhóm, có tên người xem.
- [ ] Mỗi người ≥ 2 commit có nội dung, đúng tên/email (`git shortlog -sne HEAD`).

**Vấn đáp**
- [ ] Mục 16 đã ôn xong; mỗi người trả lời được 3 phần (validator, dòng review, số README).
