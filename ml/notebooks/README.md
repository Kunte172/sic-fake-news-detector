# Notebook nghiên cứu

## Chạy EDA (issue #1)

1. Tải và giải nén hai **file** `Fake.csv`, `True.csv` từ [Kaggle](https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset) vào `ml/data/raw/` tại máy cá nhân. Kiểm tra chúng là file, không phải thư mục tên `.csv`.
2. Trong thư mục gốc repository, dùng môi trường Python của dự án:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r ml\requirements-eda.txt
   .\.venv\Scripts\python.exe -m ipykernel install --user --name sic-fake-news --display-name "Python (SIC Fake News)"
   ```

   Nếu chưa có `.venv`, tạo bằng `python -m venv .venv`. Trên macOS/Linux dùng `.venv/bin/python` và dấu `/` trong đường dẫn.
3. Mở `ml/notebooks/01_eda.ipynb` trong VS Code hoặc JupyterLab, chọn kernel **Python (SIC Fake News)** và **Run All**. Có thể đặt biến môi trường `SIC_DATA_DIR` tới một thư mục khác chứa cả hai CSV trước khi khởi động Jupyter/VS Code.
4. Notebook hiển thị bảng số liệu tổng hợp và lưu biểu đồ PNG trong `ml/artifacts/eda/` (thư mục được Git bỏ qua). Chép số liệu và nhận xét đã kiểm tra vào báo cáo; **không commit CSV, ảnh chứa nội dung bài báo hay output notebook**. Trước khi commit, dùng **Clear All Outputs** và lưu notebook.

Notebook phân tích **văn bản thô** để nhìn thấy dấu nguồn và khác biệt giữa các nhãn. Nó không phải pipeline huấn luyện, không tạo phép chia train/test và không chứng minh bài báo nào đúng/sai. `subject` và `date` trong CSV có thể phản ánh nguồn thu thập; issue #2 kiểm toán và quyết định cách loại rò rỉ trước khi so sánh mô hình.

Các notebook tiếp theo theo kế hoạch: `02_leakage_audit.ipynb`, `03_model_comparison.ipynb`, `04_topic_evaluation.ipynb`. Khi logic xử lý ổn định, chuyển hàm dùng chung sang `ml/src/` và gọi lại từ notebook để tránh train/inference khác nhau.
