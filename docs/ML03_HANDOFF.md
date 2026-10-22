# Hướng dẫn bàn giao ML-03

## Các file cần đưa vào repository

- `ml/notebooks/03_lstm.ipynb`: notebook riêng ML-03, giữ output đã chạy; không chứa nội dung bài báo.
- `ml/requirements-lstm.txt`: phiên bản các thư viện chính đã ghi nhận; không phải lockfile đầy đủ.
- `docs/ML03_REPORT.md`: báo cáo thí nghiệm và giới hạn.
- `docs/reports/ml03_20261022.json`: số liệu tổng hợp, hash và bằng chứng kiểm tra.
- Tài liệu hướng dẫn này.

## Chạy lại

Mở notebook bằng Colab, bật GPU. Lần chạy gốc dùng Python 3.13.15, TensorFlow 2.21.0, Keras 3.13.2. Kiểm tra môi trường trước khi chạy. Có thể cài các thư viện từ file requirements trong môi trường phù hợp, rồi restart runtime nếu đã import chúng trước khi cài. Colab cung cấp google.colab; notebook này không được thiết kế chạy trực tiếp bằng Python thuần trên Windows.

Chuẩn bị checkpoint tin cậy `sic_ai_step10.joblib` từ DATA-02/bước 10 của nhóm. File không nằm trong repository. SHA256 của checkpoint lần chạy này:
`63e7a206a500cd1774314d83e6cee178e5e3386cecc5d78d0731153389946323`.

Chạy cell đầu để upload và khôi phục train/validation/test cùng các baseline. Chạy tuần tự đến cell tải ZIP. Không cần chạy lại toàn bộ notebook EDA, LIME hoặc subject evaluation. Khi chỉ sửa văn bản báo cáo, không cần chạy huấn luyện lại. Điểm GPU không được bảo đảm giống tuyệt đối dù đã đặt seed.

Đầu vào bắt buộc: checkpoint có train_df, val_df, test_df, traditional_models, comparison_df, split_manifest, validation_predictions, quarantine_review, quarantine_near_conflicts. Các bảng dữ liệu cần có text_clean, label, _row_id, group_id. Checkpoint chỉ được mở nếu tin cậy do nhóm tạo.

## Giữ ở máy hoặc nơi lưu artifact của nhóm

`Fake.csv`, `True.csv`, checkpoint `.joblib`, `best_lstm.keras`, ZIP kết quả, manifest và dự đoán từng bài không nằm trong gói Git này. Gói Colab gốc vẫn giữ tại máy để đối chiếu. JSON báo cáo chỉ chứa số liệu tổng hợp, cấu hình và hash.

## Trước khi push

Đồng bộ main và làm trên nhánh riêng ML-03 theo quy ước nhóm. Chép năm file trong gói vào đúng thư mục sau khi kiểm tra không ghi đè công việc người khác. Xem danh sách file và diff trước khi commit. Không dùng git add toàn bộ thư mục dữ liệu. Liên kết PR với issue #5 và nhờ review. Việc đóng gói này chưa tạo commit, push hoặc PR.

Bản notebook đầy đủ đã chỉnh mô tả vẫn là tài liệu làm việc của bạn; notebook bàn giao chỉ tách phạm vi ML-03 và giữ nguyên sáu cell code liên quan cùng output. Gói tách chưa được chạy end-to-end trong một phiên Colab mới; đã kiểm tra thứ tự phụ thuộc và cú pháp.
