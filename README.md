# SIC Fake News Lens

Khung đồ án nhóm **Đề tài 19 — Phát hiện tin giả bằng NLP trên cloud**. Bản v0 cung cấp baseline TF-IDF + Logistic Regression, API dự đoán văn bản khi đã huấn luyện mô hình, và giao diện React. Đây là công cụ hỗ trợ sàng lọc bài báo tiếng Anh; điểm dự đoán không xác minh sự thật của sự kiện.

## Bắt đầu nhanh

Yêu cầu: Python 3.11+ và Node.js 20+. Mở terminal ở thư mục gốc repository.

1. Tải `Fake.csv`, `True.csv` từ [bộ dữ liệu Kaggle](https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset) và đặt vào `ml/data/raw/`. Không commit dữ liệu.
2. Cài thư viện, huấn luyện baseline và khởi chạy API:

   ```bash
   python -m venv .venv
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   # macOS/Linux: source .venv/bin/activate
   python -m pip install -r backend/requirements-dev.txt
   python -m ml.src.train_baseline --data-dir ml/data/raw --output-dir ml/artifacts
   # Tạo khóa riêng cho máy này, tối thiểu 32 ký tự. Không commit khóa lên Git.
   # Windows PowerShell: $env:SECRET_KEY="<your-unique-secret-at-least-32-characters>"
   # macOS/Linux: export SECRET_KEY="<your-unique-secret-at-least-32-characters>"
   python -m alembic upgrade head
   # Windows PowerShell: $env:MODEL_PATH="ml/artifacts/baseline.joblib"
   # macOS/Linux: export MODEL_PATH=ml/artifacts/baseline.joblib
   uvicorn backend.app.main:app --reload --port 8000
   ```

   Để bật xác minh email và quên mật khẩu bằng mã OTP, tạo file `backend/.env` từ
   `backend/.env.example`, điền thông tin SMTP rồi chạy API:

   ```powershell
   Copy-Item backend\.env.example backend\.env
   notepad backend\.env
   ```

   Không dùng mật khẩu Gmail thông thường và không commit các giá trị này vào mã nguồn.
   Backend tự đọc `backend/.env` khi khởi động. Chạy `alembic upgrade head` sau khi cập nhật để tạo bảng mã xác minh.

3. Trong terminal khác:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Mở `http://localhost:5173`. Tài liệu API ở `http://localhost:8000/docs`. Nếu chưa có `MODEL_PATH`, `/api/v1/analyze` trả `503` thay vì hiển thị kết quả giả.
Để bật đối chiếu fact-check, tạo API key cho Google Fact Check Tools API rồi đặt
`GOOGLE_FACT_CHECK_API_KEY=<your-key>` trong `backend/.env`. Không có key, hệ thống
vẫn phân tích mô hình nhưng bắt buộc trả kết luận `Chưa đủ dữ kiện`; không được hiểu là
bài đúng hay bài sai.

### Dùng mô hình ML-01 để phân tích bài báo hoặc URL

PR ML-01/ML-04 đã được nối vào API. Để bật mô hình SVM đã audit, cần có bộ chia
DATA-02 và tạo đủ ba artifact cùng một lần chạy:

```powershell
python -m ml.src.train_classic_models
python -m ml.src.calibrate_selected
$env:MODEL_PATH="ml/artifacts/ml01/ml01_selected.joblib"
$env:MODEL_REPORT_PATH="ml/artifacts/ml01/ml01_report.json"
$env:MODEL_CALIBRATION_PATH="ml/artifacts/ml01/ml01_calibration.json"
uvicorn backend.app.main:app --reload --port 8000
```

`MODEL_PATH` một mình chỉ dùng được với baseline có `predict_proba`; ML-01 Linear SVM
bắt buộc có report và calibration khớp checksum. Giao diện gửi nội dung dán vào
`POST /api/v1/analyze` bằng `text`, hoặc gửi URL bằng `url`; backend sẽ tải và trích
xuất bài báo an toàn trước khi đưa vào cùng mô hình. Kết quả mới hiển thị nhãn,
điểm lớp Fake đã hiệu chỉnh và các từ/cụm từ đóng góp. UI luôn đánh dấu
`NEEDS_REVIEW`: score là tín hiệu sàng lọc, không phải xác suất sự thật. Để cải thiện
độ bao phủ ngoài miền Kaggle, cần bổ sung một tập bài báo từ nhiều nguồn (khoa học,
chính thống, quốc tế) có nhãn do nhóm kiểm duyệt; không được trộn dữ liệu chưa gán
nhãn vào tập huấn luyện.

API yêu cầu `SECRET_KEY` khi khởi động. Dùng cùng một khóa bí mật cho các phiên bản chạy chung tài khoản; đổi khóa sẽ làm token cũ hết hiệu lực. Nếu dùng database khác mặc định, đặt `DATABASE_URL` trước lệnh Alembic và trước khi chạy API. File SQLite local không được commit. Để tạo ADMIN trên database mới, đặt `ADMIN_EMAIL` và `ADMIN_PASSWORD` trong môi trường trước khi khởi động lần đầu; không dùng mật khẩu mẫu ở môi trường triển khai.

## Cấu trúc

| Thư mục | Chủ trách nhiệm | Nội dung |
| --- | --- | --- |
| `ml/` | Nhóm dữ liệu và mô hình | EDA, xử lý rò rỉ, baseline, LSTM, đánh giá |
| `backend/` | Nhóm API | Suy luận, tài khoản, lịch sử, phản hồi, quản trị |
| `frontend/` | Nhóm UI | Form nhập, kết quả, lịch sử, dashboard |
| `docs/` | Cả nhóm | Phạm vi, hợp đồng API, phương pháp, phân công |
| `.github/` | Cả nhóm | CI, mẫu issue và pull request |

## Tình trạng v0

- Đã có: làm sạch dấu Reuters ở mở đầu, lọc dữ liệu trùng chính xác sau làm sạch, baseline Logistic Regression, phép chia train/test cố định, báo cáo Accuracy và F1, API text, giao diện cơ bản.
- Các phần hiện có và chưa có tiếp tục được theo dõi tại [bảng công việc](docs/TASK_BOARD.md); đăng nhập đã có trong API, còn lịch sử và triển khai cloud đang thực hiện.
- Bộ dữ liệu Kaggle chủ yếu là bài báo tiếng Anh và chứa sai lệch nguồn giữa hai nhãn. Không dùng kết quả v0 để khẳng định độ chính xác đối với mạng xã hội hoặc tiếng Việt.

## Cộng tác

Đọc [hướng dẫn giao việc bằng GitHub Issues](docs/GITHUB_ISSUES.md), [quy trình Git và PR](docs/COLLABORATION.md), [quy tắc đánh giá](docs/DATA_AND_EVALUATION.md), [hợp đồng API](docs/API_CONTRACT.md) và [bảng công việc](docs/TASK_BOARD.md) trước khi nhận việc. Các issue trong bảng đã được tạo; chỉ mở issue mới cho đầu việc phát sinh. Mỗi đầu việc dùng một nhánh và gửi PR vào `main`. Không commit CSV, model artifact, `.env` hoặc dữ liệu người dùng.

Xem [hướng dẫn đưa lên GitHub](docs/GITHUB_SETUP.md) nếu bắt đầu từ bản ZIP.

## Dùng ML-01 và giải thích trong ứng dụng

Baseline cũ vẫn chạy theo phần bắt đầu nhanh. Để dùng mô hình ML-01 đã audit, giữ cùng artifact, báo cáo và hiệu chỉnh của một lần chạy:

```powershell
python -m ml.src.train_classic_models
python -m ml.src.calibrate_selected
$env:MODEL_PATH="ml/artifacts/ml01/ml01_selected.joblib"
$env:MODEL_REPORT_PATH="ml/artifacts/ml01/ml01_report.json"
$env:MODEL_CALIBRATION_PATH="ml/artifacts/ml01/ml01_calibration.json"
# Tùy chọn: LIME chạy 1000 perturbations mỗi lượt, làm tăng độ trễ.
python -m pip install -r ml/requirements-explain.txt
$env:ENABLE_LIME="true"
python -m uvicorn backend.app.main:app --reload --port 8000
```

Cần `prepared_splits.csv` DATA-02 và SECRET_KEY/database theo hướng dẫn phía trên. Chạy lại calibrate_selected nếu calibration cũ chưa có checksum mô hình. Chương trình đối chiếu checksum splits với báo cáo ML-01; API từ chối calibration của artifact khác. Chỉ tải joblib tin cậy do nhóm tạo.

API trả nhãn theo mô hình, điểm Fake đã hiệu chỉnh và đóng góp chính xác theo TF-IDF × hệ số (bao gồm cặp từ). Tổng đóng góp hiển thị + phần còn lại + hệ số chặn bằng margin Fake; không cộng các giá trị này như phần trăm. Điểm trên 0,5 không nhất thiết tương ứng SUSPICIOUS: nhãn theo SVM là kết quả chính thức. LIME chỉ là xấp xỉ, UI cảnh báo khi fidelity dưới 0,5 (ngưỡng hiển thị quy ước, không phải chuẩn đảm bảo chất lượng).

Giải thích hiện hiển thị ở kết quả mới, chưa lưu trong lịch sử. Thiếu artifact/hiệu chỉnh trả 503; văn bản rỗng sau làm sạch trả 422. Không cần DATA-03/LIAR.
