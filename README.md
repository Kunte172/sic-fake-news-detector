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
   # Windows PowerShell: $env:MODEL_PATH="ml/artifacts/baseline.joblib"
   # macOS/Linux: export MODEL_PATH=ml/artifacts/baseline.joblib
   uvicorn backend.app.main:app --reload --port 8000
   ```

3. Trong terminal khác:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Mở `http://localhost:5173`. Tài liệu API ở `http://localhost:8000/docs`. Nếu chưa có `MODEL_PATH`, `/api/v1/analyze` trả `503` thay vì hiển thị kết quả giả.

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
- Chưa có: kiểm tra gần trùng, đánh giá theo chủ đề, SVM/Naive Bayes, LSTM, LIME, URL, đăng nhập, lưu lịch sử và triển khai cloud. Xem [bảng công việc](docs/TASK_BOARD.md).
- Bộ dữ liệu Kaggle chủ yếu là bài báo tiếng Anh và chứa sai lệch nguồn giữa hai nhãn. Không dùng kết quả v0 để khẳng định độ chính xác đối với mạng xã hội hoặc tiếng Việt.

## Cộng tác

Đọc [hướng dẫn giao việc bằng GitHub Issues](docs/GITHUB_ISSUES.md), [quy trình Git và PR](docs/COLLABORATION.md), [quy tắc đánh giá](docs/DATA_AND_EVALUATION.md), [hợp đồng API](docs/API_CONTRACT.md) và [bảng công việc](docs/TASK_BOARD.md) trước khi nhận việc. Các issue trong bảng đã được tạo; chỉ mở issue mới cho đầu việc phát sinh. Mỗi đầu việc dùng một nhánh và gửi PR vào `main`. Không commit CSV, model artifact, `.env` hoặc dữ liệu người dùng.

Xem [hướng dẫn đưa lên GitHub](docs/GITHUB_SETUP.md) nếu bắt đầu từ bản ZIP.
