# Triển khai SIC lên Render

Hướng dẫn này dùng hai dịch vụ Render riêng: **Web Service** cho FastAPI và **Static Site** cho Vite/React. CI của repository kiểm tra `npm test` và `npm run build`; thay đổi frontend khôi phục ứng dụng đã được merge vào `main` và CI gần nhất đã thành công. Không thể đảm bảo trạng thái deploy thực tế nếu chưa chạy build trên Render và chưa cấu hình đủ biến môi trường/dịch vụ bên ngoài.

## 1. Tạo PostgreSQL

Tạo một PostgreSQL database trên Render. Chọn gói phù hợp với tài khoản/chi phí của bạn; không dùng SQLite của filesystem dịch vụ cho dữ liệu cần giữ lâu dài. Lấy **Internal Database URL** để cấu hình cho backend.

## 2. Tạo API Web Service

Chọn repository `Kunte172/sic-fake-news-detector`, branch `main`, runtime **Python** và cấu hình:

- Root Directory: để trống (repository root)
- Build Command: `python -m pip install -r backend/requirements.txt`
- Start Command: `alembic upgrade head && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

Thêm biến môi trường:

- `SECRET_KEY`: chuỗi ngẫu nhiên bí mật, tối thiểu 32 ký tự; tạo riêng trên Render, không đưa vào Git.
- `DATABASE_URL`: Internal Database URL của PostgreSQL vừa tạo. Backend chuyển tiếp scheme `postgres://`/`postgresql://` sang driver `psycopg` có trong requirements.
- `PYTHON_VERSION`: `3.11.11` (hoặc bản Python 3.11 được Render hỗ trợ trong thời điểm deploy).
- `MODEL_PATH`: đường dẫn tới artifact mô hình nếu đã cung cấp artifact cho dịch vụ.
- `ADMIN_EMAIL` và `ADMIN_PASSWORD`: tài khoản quản trị. Nếu email đã đăng ký trước, mật khẩu cấu hình phải khớp mật khẩu hiện tại của tài khoản đó thì API mới nâng quyền lên `ADMIN` khi khởi động. Đăng xuất rồi đăng nhập lại để làm mới phiên; kiểm tra `role` tại `/api/v1/auth/me`. Không dùng mật khẩu mẫu.

**Lưu ý về mô hình:** artifact mô hình không nằm trong Git. Nếu chưa đưa một artifact tương thích vào môi trường backend và chưa đặt `MODEL_PATH`, dịch vụ API vẫn có thể khởi động nhưng `/api/v1/analyze` sẽ trả `503 Model not loaded`. Kiểm tra `model_loaded` trong phản hồi `/health`. Với mô hình ML-01 cần cấu hình đồng bộ `MODEL_PATH`, `MODEL_REPORT_PATH` và `MODEL_CALIBRATION_PATH` như README hướng dẫn; không tự ý dùng artifact không khớp checksum.

## 3. Tạo Static Site cho frontend

Tạo Static Site từ cùng repository/branch `main`:

- Build Command: `cd frontend && npm ci && npm run build`
- Publish Directory: `frontend/dist`
- Rewrite rule: source `/*`, destination `/index.html`, action **Rewrite** (để các đường dẫn SPA như `/auth` tải được).

Thêm biến môi trường build:

- `VITE_API_BASE_URL`: URL công khai của API Web Service, ví dụ `https://sic-fake-news-api.onrender.com` (không thêm `/api/v1`; frontend tự nối phần đó).

Cấu hình CORS backend hiện cho phép frontend origin `https://sic-fake-news-web.onrender.com`. Dùng đúng hostname Static Site đó hoặc cập nhật cấu hình CORS trong backend nếu hostname Render của bạn khác; sau khi đổi env/code cần deploy lại API.

## 4. Kiểm tra sau deploy

1. Mở `https://<api-service>.onrender.com/health`: phải trả JSON có `"status":"ok"`. `model_loaded` phải là `true` để phân tích hoạt động.
2. Mở URL Static Site, tải lại trực tiếp `/auth` và `/analyze` để kiểm tra rewrite.
3. Thử đăng ký/đăng nhập và phân tích; nếu trình duyệt báo CORS, kiểm tra origin thực tế của frontend và allowlist backend.
4. Với lỗi deploy, xem **Events** và **Logs** của đúng dịch vụ trên Render; lỗi thiếu `DATABASE_URL`, `SECRET_KEY`, artifact mô hình hoặc cấu hình email cần được xử lý riêng.

Email OTP cần cấu hình nhà cung cấp (ví dụ `BREVO_API_KEY` và `BREVO_SENDER_EMAIL`, hoặc SMTP) trong biến môi trường backend. Không commit secrets vào repository.
