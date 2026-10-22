# ML-03 — Huấn luyện Embedding + LSTM

Issue liên quan: #5. Phụ thuộc DATA-02. Run: `20261022T152137686036Z`, ngày 22/10/2026.

## Mục tiêu và dữ liệu

So sánh Embedding + LSTM với các mô hình truyền thống trên cùng phép chia. Fake=0, Real=1. Dùng thân bài đã làm sạch (`text_clean`), không dùng subject/date làm đầu vào mô hình.

Manifest được đối chiếu với DATA-02 trên máy và khớp toàn bộ ID, nhóm, nhãn, tập. Train: 30.537 bài (13.590 Fake, 16.947 Real); validation: 3.824 (1.698 Fake, 2.126 Real); test: 3.803 (1.692 Fake, 2.111 Real). Các nhóm bài gần trùng đã phát hiện không đi qua ranh giới các tập. Phương pháp phát hiện gần trùng có tính xấp xỉ.

## Cấu hình và huấn luyện

TextVectorization chỉ adapt trên train, tối đa 20.000 mục từ vựng, chuỗi dài 400. Embedding 128 chiều với mask_zero; LSTM 64 units; Dropout 0,5; Dense 32 ReLU; Dense 1 sigmoid hướng Real. Ngưỡng nhãn Real là 0,5; điểm không được diễn giải là xác suất sự thật đã hiệu chỉnh.

Adam learning rate 0,001, clipnorm 1, binary cross-entropy, batch size 64, seed 42. Tối đa 15 epoch, EarlyStopping theo val_loss với patience=2. Log xác nhận dừng ở epoch 3 và khôi phục epoch 1. ModelCheckpoint lưu mô hình tốt nhất, sau đó nạp lại trước đánh giá. Tổng thời gian fit khoảng 41,46 giây trên môi trường có Tesla T4.

## Kết quả

| Mô hình | Test Accuracy | Test F1-macro | F1-Fake | Bài sai |
|---|---:|---:|---:|---:|
| Logistic Regression | 98,29% | 98,27% | 98,07% | 65 |
| Linear SVM | 99,32% | 99,31% | 99,23% | 26 |
| Multinomial Naive Bayes | 95,14% | 95,08% | 94,53% | 185 |
| LSTM | 97,74% | 97,71% | 97,45% | 86 |

LSTM validation Accuracy 98,25%, F1-macro 98,22%. Epoch 1 val_loss=0,0698543; epoch 2=0,1031652; epoch 3=0,0718115. Train accuracy tăng trong khi validation loss không cải thiện so với epoch 1; dừng sớm giúp giữ checkpoint tốt nhất theo tiêu chí này.

SVM vẫn là mô hình triển khai đã chọn từ validation. LSTM phục vụ thí nghiệm so sánh; không yêu cầu LSTM phải vượt SVM và không thay mô hình dựa vào test. Không dùng điểm LSTM 98,50% của thí nghiệm cũ để mô tả lần chạy mới.

## Thời gian suy luận

Trung vị 5 lần đo sau 2 lần warm-up. Batch 1 sử dụng một bài validation cố định, batch 64 sử dụng 64 bài validation đầu tiên. Đây là đo mẫu nhỏ, không đại diện cho mọi độ dài bài hay tải nhiều người dùng.

| Mô hình | Batch 1 (ms/yêu cầu) | Batch 64 (ms/cả lô) |
|---|---:|---:|
| Linear SVM | 1,485 | 36,917 |
| LSTM | 27,853 | 36,206 |

Bao gồm vectorization và dự đoán từ text_clean; không gồm đọc file, tải mô hình, làm sạch dấu nguồn, mạng hay UI. LSTM được chạy trong runtime có GPU T4, SVM dùng CPU; đây là cấu hình triển khai thử nghiệm, không phải so sánh công bằng trên cùng bộ xử lý. Thời gian bình quân mỗi bài trong lô không phải độ trễ một yêu cầu đơn.

## Bằng chứng và giới hạn

Notebook trích riêng các cell ML-03 giữ nguyên code và output đã chạy. JSON đi kèm chứa log, metric và thời gian gốc. Kiểm tra cục bộ đã đối chiếu hash checkpoint/model/manifest, tính lại metric từ dự đoán đã lưu, kiểm tra median thời gian; chưa chạy lại suy luận mô hình độc lập trên máy người kiểm tra.

Tập test đã từng được xem: lần này là tái chạy/bổ sung bằng chứng, không phải đánh giá độc lập mới. Không tinh chỉnh theo test. Mô hình chỉ được đánh giá trên dữ liệu tin tiếng Anh; không khẳng định khái quát cho tiếng Việt, dữ liệu hiện tại hoặc kiểm chứng sự thật. Chưa đo độ ổn định qua nhiều seed. Chưa loại hết thiên lệch nguồn/phong cách. Phần đánh giá subject và LIME thuộc các mục khác, không được dùng để khẳng định ML-03 đã giải quyết chúng.

Kết luận: bằng chứng hiện có đáp ứng các nội dung kỹ thuật ML-03 trong issue #5; việc nghiệm thu/merge thuộc review của nhóm.
