# DATA-02 — Hướng dẫn bàn giao

Phạm vi: issue #2, kiểm toán dấu nguồn, trùng/gần trùng và ranh giới train/validation/test. Không triển khai API-01, UI-01, không huấn luyện lại hay chọn lại mô hình.

## File cần đưa vào dự án

Giữ nguyên cấu trúc thư mục trong gói bàn giao:

- `backend/app/colab_preprocessing.py`: hàm làm sạch lấy nguyên văn từ gói Colab đã tải xuống, có checksum trong báo cáo.
- `backend/app/preprocessing.py`: chỉ bổ sung tên `clean_colab_text`; các hàm baseline-v0 giữ nguyên.
- `backend/tests/test_data_audit.py`: kiểm thử làm sạch, cách ly, nhóm gần trùng, tách tập và đối chiếu checkpoint.
- `backend/requirements-dev.txt`: thêm `datasketch==2.0.0` cho kiểm thử và CI.
- `ml/requirements-audit.txt`: phụ thuộc của chương trình audit.
- `ml/requirements-audit-replay.txt`: phiên bản thư viện dùng để tái lập lần kiểm tra này.
- `ml/src/audit_data.py`: chương trình kiểm toán có thể chạy lại từ hai CSV gốc.
- `docs/DATA02_REPORT.md` và `docs/reports/data02_verified.json`: kết quả và bằng chứng tổng hợp.
- Tài liệu này.

Gói được chuẩn bị trên `main` tại commit `ee259851b177f3d0162abefde314f01dcda4292c`. Nếu nhóm đã sửa các file có sẵn, ghép phần thay đổi thay vì ghi đè toàn bộ. DATA-02 đã được gửi trong PR #15 trên nhánh `feat/2-data-audit`. Nhánh đã được đồng bộ với `main` có DATA-01. Chạy lại 29 kiểm thử backend trên máy: tất cả đều đạt.
## Chạy lại với dữ liệu Colab đã làm

Đặt `Fake.csv`, `True.csv` vào `ml/data/raw/`. Hai file lấy từ bộ Kaggle được chỉ trong README. Giữ checkpoint do chính bạn tạo `sic_ai_step10.joblib` ở máy; không đưa lên Git.

Từ thư mục gốc repository, trong môi trường Python riêng:

```bash
python -m pip install -r ml/requirements-audit-replay.txt
python -m ml.src.audit_data --data-dir ml/data/raw --output-dir ml/artifacts/data02 --checkpoint "DUONG_DAN/sic_ai_step10.joblib" --trust-local-checkpoint
python -m unittest discover -s backend/tests -v
python -m compileall -q backend ml
```

Thay `DUONG_DAN` bằng vị trí checkpoint của bạn. Cờ xác nhận chỉ dùng cho checkpoint tin cậy do bạn tạo: joblib không phải định dạng an toàn để mở file không rõ nguồn.

Chế độ này khôi phục chính phép chia đã đánh giá trên Colab. Nó dừng với lỗi nếu dữ liệu gốc, tập ID được giữ/cách ly, nội dung làm sạch, manifest hoặc ranh giới nhóm không khớp. Nó không tự đổi test để làm cho kiểm tra đạt.

Nếu không còn checkpoint, có thể bỏ hai tham số checkpoint để tạo **thí nghiệm mới**. Khi đó phải coi manifest mới là một phiên bản dữ liệu mới, không gắn các điểm Accuracy/F1 Colab cũ vào nó. Chương trình không đảm bảo phiên bản scikit-learn khác nhau tạo cùng phép chia.

## Đầu ra cục bộ

Trong `ml/artifacts/data02/`:

- `audit_summary.json`: số lượng, checksum, phiên bản thư viện và trạng thái kiểm tra.
- `marker_rates.csv`: số bài, mẫu số và tỷ lệ từng dấu hiệu ở mỗi giai đoạn.
- `subject_by_label.csv`, `month_by_label.csv`: kiểm tra lệch chủ đề/thời gian.
- `prepared_splits.csv`, `split_manifest.csv`: dữ liệu sạch và phép chia.
- `near_pairs.csv`: các cặp gần trùng phát hiện bằng LSH rồi xác nhận bằng Jaccard chính xác.
- `excluded_*.csv`: các dòng bị loại/giữ riêng, vẫn còn nội dung gốc để kiểm tra.
- `exclusions_by_label.csv`: tác động của từng bước theo nhãn.

Các file dữ liệu nằm trong đường dẫn đã được `.gitignore` bỏ qua. Chỉ đưa mã, kiểm thử và báo cáo tổng hợp lên dự án; không đưa CSV bài báo, checkpoint hoặc mô hình vào Git.

## Quy tắc tích hợp cho người làm ML/API tiếp theo

1. Dữ liệu Colab: **0 = Fake, 1 = Real**. Baseline-v0 trong repo: **1 = Fake, 0 = Real**. Phải đọc metadata; không suy ra ý nghĩa nhãn từ số 0/1.
2. DATA-02 dùng **nội dung bài `text`**, không nối tiêu đề, không dùng `subject`, `date`, ID, nhóm hoặc cột kiểm tra làm đặc trưng.
3. Luồng Colab dùng `backend.app.preprocessing.clean_colab_text` (cũng chính là `clean_source_markers` trong module riêng). Làm sạch đúng một lần từ văn bản gốc. Không chạy thêm một bộ làm sạch khác sau đó.
4. `ml/src/train_baseline.py` và API v0 vẫn là baseline cũ; chúng chưa được chuyển sang bộ dữ liệu đã audit. Khi làm ML-01, đọc `prepared_splits.csv`, giữ đúng cột `split`, chỉ fit vectorizer trên train và áp dụng quy ước nhãn rõ ràng. Không gọi lại `train_test_split` trên từng bài.
5. Khi tích hợp SVM Colab, dùng `decision_function`; không gọi `predict_proba` của API baseline-v0 hay biến margin thành phần trăm. Công việc tích hợp mô hình không nằm trong DATA-02.
6. Kết quả test cũ đã được xem; mọi sửa quy tắc dữ liệu/mô hình về sau phải được ghi là thí nghiệm mới, không âm thầm điều chỉnh theo test.

## Tiêu chí nghiệm thu DATA-02

- Có bảng tần suất trước/sau với mẫu và mẫu số rõ ràng.
- Có kiểm tra Reuters/dateline, kiểu mở đầu, URL/nguồn ảnh và chênh lệch `subject`/`date`.
- Có kiểm thử quy tắc làm sạch và tương thích phiên bản Colab.
- Bài rỗng, bản sao và nhóm mâu thuẫn được ghi riêng, không tự đổi nhãn.
- Mỗi thành phần liên thông của các cặp gần trùng đã phát hiện nằm trong một tập.
- Kiểm tra tự động không có ID, khóa nội dung hay nhóm chồng lấn giữa train/validation/test.
- Báo cáo ghi rõ giới hạn: không chứng minh hết sai lệch nguồn, không coi các bài cách ly là nhãn sai.

Chỉ đánh dấu issue hoàn tất sau khi đưa các file vào dự án và chạy kiểm thử trong nhánh tích hợp. Không đánh dấu các issue ML/API/UI khác là hoàn tất theo báo cáo này.
## Kết quả chạy lại sau khi đồng bộ DATA-01

Ngày 19/10/2026, chạy lại trên máy cá nhân với mã tại commit `64ab9fec7b7cd93b09a2b043707afdcb567e7a67`.

- Bộ kiểm thử backend: 29 kiểm thử đạt.
- Kiểm toán dữ liệu thật từ `Fake.csv`, `True.csv` và checkpoint Colab tin cậy `sic_ai_step10.joblib`.
- Đầu vào: 44.898 bài. Giữ lại: 38.164 bài.
- Train: 30.537; validation: 3.824; test: 3.803.
- Sai khác nội dung làm sạch so với checkpoint: 0.
- Trường dữ liệu gốc và manifest chia tập khớp checkpoint.
- Các nhóm gần trùng mới phát hiện không chồng lấn giữa các tập.

Bằng chứng tổng hợp: [Kết quả chạy lại](reports/data02_rerun_2026-10-19.json), gồm checksum dữ liệu, checkpoint, phiên bản thư viện và kết quả đối chiếu.

Đây là kết quả chạy trên máy cá nhân, không phải lần kiểm toán toàn bộ dữ liệu trên CI. Lần chạy này không huấn luyện lại mô hình.