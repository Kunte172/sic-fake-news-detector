# ML-02 — Đánh giá theo chủ đề chung

Issue liên quan: #4. Phụ thuộc DATA-02. Fake=0, Real=1. Số liệu lấy từ một lần chạy `python -m ml.src.topic_cv` (k=10, seed 42); báo cáo máy đọc nằm ở `docs/reports/ml02_20261025.json`.

## Mục tiêu

Kiểm tra mô hình có còn phân biệt Fake/Real khi gặp một chủ đề mà nó chưa từng học. Cột `subject` gốc không dùng được vì mỗi giá trị chỉ thuộc một nhãn (xem `EDA_FINDINGS.md`), nên chủ đề được tạo từ nội dung bài.

## Dữ liệu và phương pháp

- Dữ liệu: toàn bộ 38,164 bài đã qua DATA-02 (train + validation + test gộp lại; 16,980 Fake, 21,184 Real). `prepared_splits.csv` có SHA-256 `64f296e51ae407e73261674b9cd4ebb368971bb9942fa9bd9377a9d22ea06666`. `split_origin` là `restored_colab_unchanged`: dữ liệu được khôi phục nguyên vẹn từ checkpoint của nhóm.
- Chủ đề: TF-IDF trên `text_clean` → TruncatedSVD → KMeans (k=10, seed 42). Không dùng nhãn, `subject`, `date`, tiêu đề hay ID. Mỗi nhóm gần trùng (`group_id`) nằm trọn trong một chủ đề.
- Điều kiện hợp lệ: chủ đề được đánh giá khi có ít nhất 100 bài Fake và 100 bài Real. Chủ đề thiếu một nhãn được báo là không đánh giá, không báo điểm một lớp.
- Đánh giá: với mỗi chủ đề hợp lệ, huấn luyện trên mọi bài ngoài chủ đề đó rồi kiểm tra trên chủ đề bị giữ lại (leave-one-topic-out). Mô hình là TF-IDF + Linear SVM đúng cấu hình ML-01, không tinh chỉnh. Mã kiểm tra không có `_row_id`, `group_id` hoặc `_clean_key` trùng giữa phần train và phần giữ lại.
- Đối chiếu: cùng mô hình, chia ngẫu nhiên theo nhóm (GroupKFold, 9 fold), chấm trên đúng 35,165 bài thuộc 9 chủ đề được đánh giá.
- Môi trường: scikit-learn 1.9.1, pandas 2.3.3 (checkpoint Colab lưu bằng scikit-learn 1.6.1; checkpoint chỉ dùng để khôi phục dữ liệu, không dùng để dự đoán).

## Kết quả

| Chủ đề | Từ khóa nổi bật | Fake | Real | Accuracy | F1 (Fake) | Macro F1 |
|---|---|---:|---:|---:|---:|---:|
| 0 | al syria iran military islamic forces | 353 | 3,973 | 0.9928 | 0.9555 | 0.9758 |
| 1 | states united administration china obama | 1,852 | 4,539 | 0.9836 | 0.9716 | 0.9800 |
| 2 | russia intelligence fbi investigation comey | 1,308 | 1,690 | 0.9880 | 0.9862 | 0.9878 |
| 3 | just people like donald know don | 7,660 | 179 | 0.9949 | 0.9974 | 0.9388 |
| 4 | court supreme judge justice case federal | 769 | 1,652 | 0.9818 | 0.9714 | 0.9790 |
| 5 | minister eu european party britain brexit | 93 | 2,906 | không đánh giá | | |
| 6 | police officers man arrested black gun | 1,727 | 1,029 | 0.9848 | 0.9877 | 0.9838 |
| 7 | korea north nuclear missile pyongyang | 109 | 1,199 | 0.9901 | 0.9378 | 0.9662 |
| 8 | senate house tax republican obamacare | 579 | 2,364 | 0.9949 | 0.9870 | 0.9919 |
| 9 | clinton hillary presidential campaign | 2,530 | 1,653 | 0.9861 | 0.9886 | 0.9855 |

Chủ đề 5 bị loại vì chỉ có 93 bài Fake (dưới 100).

Gộp dự đoán của 9 chủ đề được đánh giá, so với chia ngẫu nhiên theo nhóm trên cùng 35,165 bài:

| Cách chia | Accuracy | F1 (Fake) | Macro F1 | Số bài dự đoán sai |
|---|---:|---:|---:|---:|
| Giấu từng chủ đề | 0.9891 | 0.9886 | 0.9891 | 384 |
| Chia ngẫu nhiên theo nhóm | 0.9918 | 0.9915 | 0.9918 | 287 |

Trung bình theo fold: Accuracy 0.9886, Macro F1 0.9765. Chủ đề kém nhất theo Macro F1 là chủ đề 3 (0.9388).

Các chủ đề có một nhãn rất ít bài, nơi ước lượng kém chắc nhất (khoảng tin cậy Wilson 95%):

| Chủ đề | Nhãn ít bài | Số bài | Recall | Khoảng tin cậy |
|---|---|---:|---:|---|
| 3 | Real | 179 | 0.821 | 0.759–0.870 |
| 7 | Fake | 109 | 0.899 | 0.828–0.943 |
| 0 | Fake | 353 | 0.943 | 0.914–0.963 |

## Nhận xét

1. Không thấy mô hình sụt điểm mạnh khi đổi chủ đề. Accuracy gộp thấp hơn chia ngẫu nhiên khoảng 0.28 điểm phần trăm (0.9891 so với 0.9918), nhưng số bài dự đoán sai tăng từ 287 lên 384, tức khoảng 34%.
2. Điểm thấp nhất nằm ở các chủ đề có một nhãn rất ít bài (3, 7, 0). Ở chủ đề 3, mô hình bỏ sót 32 trong 179 bài Real; ở chủ đề 7, bỏ sót 11 trong 109 bài Fake. Accuracy các chủ đề này vẫn cao vì nhãn đông bài gần như đúng hết, nên cần đọc Macro F1 và recall từng nhãn.
3. Nhiều chủ đề lệch nhãn mạnh: chủ đề 3 có 97.7% Fake, chủ đề 5 có 96.9% Real, chủ đề 0 và 7 có khoảng 92% Real. Từ khóa của chủ đề 3 là từ ngữ hội thoại (`just`, `people`, `like`, `know`) hơn là một đề tài, nên cụm này có thể phản ánh văn phong và nguồn, không chỉ nội dung. Vì vậy các chủ đề ở đây không thuần là chủ đề ngữ nghĩa.
4. Kết quả cho thấy mô hình không phụ thuộc vào việc đã gặp cùng chủ đề. Kết quả này không chứng minh mô hình nhận ra tin giả: DATA-02 đã ghi rằng bỏ dấu nguồn không loại bỏ thiên lệch nguồn, văn phong và chủ đề, và các thiên lệch đó có thể đi xuyên qua các chủ đề.

## Giới hạn

- Một lần chạy với một giá trị k (10), một seed (42) và một ngưỡng 100 bài mỗi nhãn. Độ nhạy theo k và theo ngưỡng chưa được kiểm tra.
- Không có khoảng tin cậy cho chênh lệch 0.28 điểm phần trăm giữa hai cách chia; chưa lặp lại với nhiều seed.
- Chủ đề 5 không được đánh giá; nhãn thiểu số ở chủ đề 3 và 7 chỉ có 179 và 109 bài.
- Chủ đề là cụm không giám sát của văn bản đã làm sạch, không phải chuyên mục biên tập. TF-IDF, SVD và KMeans dùng để định nghĩa chủ đề được fit trên toàn bộ bài nhưng không dùng nhãn; bộ phân loại không thấy chủ đề bị giữ lại.
- Tập dữ liệu chỉ gồm tin tiếng Anh; không khái quát sang mạng xã hội hay tiếng Việt và không xác minh sự thật của bài báo. Tập test cũ đã được xem trong ML-01 và ML-03; đây là thí nghiệm mới, không tinh chỉnh theo kết quả.

## Hướng kiểm thử ngoài (đề xuất, chưa thực hiện)

Để tách tác động của nguồn và văn phong khỏi khả năng nhận ra nội dung sai, cần một tập kiểm thử ngoài bộ dữ liệu hiện tại:

- Nguồn: bài tiếng Anh không có trong bộ dữ liệu Kaggle, từ nhiều nguồn cho mỗi nhãn; ưu tiên nguồn xuất hiện ở cả hai nhãn để nhãn không trùng với nguồn.
- Gán nhãn: theo từng bài dựa trên kiểm chứng công khai, do hai người gán độc lập; đo mức đồng thuận và loại bài bất đồng.
- Quy mô: vài trăm bài mỗi nhãn trở lên để khoảng tin cậy của recall hẹp; báo cáo theo nguồn.
- Quy trình: dùng đúng tiền xử lý của `backend/app/preprocessing.py`, chỉ dùng để đánh giá, không dùng để tinh chỉnh; lưu URL và nhãn thay vì sao chép toàn văn nếu giấy phép không cho phép.

## Cách tái lập

```
python -m ml.src.audit_data --data-dir ml/data/raw --output-dir ml/artifacts/data02 --checkpoint <đường dẫn checkpoint> --trust-local-checkpoint
python -m ml.src.topic_cv
```

Lệnh thứ hai ghi `ml/artifacts/ml02/ml02_report.json` và `ml02_topics.csv` (thư mục `ml/artifacts` không được commit). Tùy chọn: `--topics`, `--min-per-label`, `--skip-random-baseline`.