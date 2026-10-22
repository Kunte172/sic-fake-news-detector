# ML-01 — So sánh mô hình TF-IDF trên dữ liệu đã kiểm toán

## Phạm vi và dữ liệu

So sánh Logistic Regression, Multinomial Naive Bayes và Linear SVM trên cùng file `ml/artifacts/data02/prepared_splits.csv` do chương trình DATA-02 tạo ở máy local. Mã chỉ dùng `text_clean` làm đặc trưng, `label` làm nhãn; **0 = Fake, 1 = Real**. Cột `subject`, `date`, ID và nhóm bài không được đưa vào mô hình.

| Tập | Số bài |
|---|---:|
| Train | 30.537 |
| Validation | 3.824 |
| Test | 3.803 |

SHA-256 của file đầu vào: `05d9736daedb95cd97732f0d0368937b4ba424ebb1f88031f72d8c127f4c1760`. Chương trình kiểm tra không có ID, khóa nội dung hoặc nhóm bài trùng giữa các tập, nhưng **không tự xác minh nguồn gốc phép chia**. Người chạy cần đối chiếu `ml/artifacts/data02/audit_summary.json`: `split_origin=restored_colab_unchanged` nếu đã khôi phục checkpoint tin cậy, hoặc `new_experiment` nếu tạo split mới. Không gắn điểm Colab cũ với split mới.

## Phương pháp

Mỗi mô hình là một `Pipeline` gồm `TfidfVectorizer` (unigram/bigram, `min_df=2`, `max_df=0.95`, tối đa 100.000 đặc trưng, `sublinear_tf=True`) và bộ phân loại. Cả vectorizer và bộ phân loại chỉ fit trên train. Cấu hình mô hình được định nghĩa trong `ml/src/train_classic_models.py`; seed của Logistic Regression và Linear SVM là 42.

Chọn mô hình theo **macro F1 trên validation**; F1(Fake) dùng khi hòa. Test chỉ dùng để báo cáo kết quả sau lựa chọn. Chương trình có xuất điểm test của cả ba mô hình để so sánh, không dùng chúng để thay lựa chọn. Artifact local `ml/artifacts/ml01/ml01_selected.joblib` và báo cáo JSON local nằm trong thư mục Git bỏ qua.

## Kết quả

| Mô hình | Val accuracy | Val F1(Fake) | Val macro F1 | Test accuracy | Test F1(Fake) | Test macro F1 |
|---|---:|---:|---:|---:|---:|---:|
| Logistic Regression | 0,983787 | 0,981559 | 0,983546 | 0,982908 | 0,980706 | 0,982683 |
| Multinomial Naive Bayes | 0,955021 | 0,949143 | 0,954412 | 0,949251 | 0,942781 | 0,948593 |
| Linear SVM | **0,991893** | **0,990842** | **0,991785** | **0,992637** | **0,991716** | **0,992545** |

**Mô hình được chọn:** Linear SVM. Ma trận nhầm lẫn trên test có hàng là nhãn thật, cột là nhãn dự đoán, thứ tự cả hai trục là `[Fake, Real]`:

| Mô hình | Fake → Fake | Fake → Real | Real → Fake | Real → Real |
|---|---:|---:|---:|---:|
| Logistic Regression | 1.652 | 40 | 25 | 2.086 |
| Multinomial Naive Bayes | 1.590 | 102 | 91 | 2.020 |
| Linear SVM | 1.676 | 16 | 12 | 2.099 |

Phiên bản trong lần chạy: scikit-learn 1.6.1, pandas 2.3.3.

## Tái chạy

Từ thư mục gốc repo, trước tiên tạo `prepared_splits.csv` theo [hướng dẫn DATA-02](DATA02_HANDOFF.md). Sau đó:

```powershell
.\.venv\Scripts\python.exe -m ml.src.train_classic_models
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests
.\.venv\Scripts\python.exe -m compileall -q backend ml
```

Lần chạy local đã báo 39 kiểm thử backend đạt trước khi thêm kiểm thử ML-01 trong PR. CI kiểm tra mã và test với dữ liệu giả lập; dataset thật và artifact không nằm trong repo.

## Giới hạn

Điểm số chỉ mô tả tập Kaggle đã xử lý. Việc xóa các chuỗi nguồn không loại bỏ hoàn toàn thiên lệch văn phong, chủ đề hoặc nguồn thu thập; điểm cao không xác minh sự thật của một bài báo. Kiểm thử theo chủ đề chung thuộc ML-02. `decision_function` của Linear SVM là khoảng cách đến ranh giới phân loại, **không phải xác suất**. API hiện vẫn dùng baseline-v0 với quy ước nhãn khác; chưa được chuyển sang artifact ML-01.
