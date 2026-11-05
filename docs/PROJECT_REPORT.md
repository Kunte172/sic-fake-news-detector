# DOC-01 — Báo cáo tổng hợp phương pháp, kết quả và trách nhiệm sử dụng

**Ngày tổng hợp:** 05/11/2026. **Mốc mã nguồn:** `8879e0a` trên main.
Tài liệu tổng hợp bằng chứng đã lưu trong repo, không phải một lần chạy lại dataset/model.
Các PR #31 (tích hợp giải thích), #32 (dashboard) và #33 (URL) còn mở tại thời điểm viết; không coi tính năng trong các PR đó là đã triển khai trên cloud.
DATA-03/LIAR đã được bỏ khỏi phạm vi theo quyết định của nhóm.

## 1. Mục tiêu và cách hiểu kết quả

Xây dựng công cụ hỗ trợ sàng lọc bài báo tiếng Anh dựa trên văn bản: EDA, giảm dấu nguồn và bài trùng, so sánh mô hình truyền thống với LSTM, kiểm tra theo cụm chủ đề, giải thích dự đoán và hỗ trợ nhiều tài khoản.
Đầu ra là sự tương đồng với các lớp của dataset, không phải xác minh sự thật của từng sự kiện.
Không dùng điểm mô hình làm căn cứ duy nhất để kết luận, kiểm duyệt hay xử lý tác giả.

## 2. Nguồn dữ liệu và EDA

Nguồn: [Fake and Real News Dataset — Clément Bisaillon, Kaggle](https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset).
Repo sử dụng hai CSV Fake.csv và True.csv, gồm title, text, subject, date.
Theo [DATA-01](EDA_FINDINGS.md): 44.898 bài, gồm 23.481 Fake và 21.417 Real; trung vị nội dung 375 và 367 từ tương ứng.

Các dấu hiệu cần chú ý:

- 8/8 giá trị subject chỉ xuất hiện ở một lớp, bao phủ toàn bộ dữ liệu. Không dùng subject làm đặc trưng hoặc trực tiếp coi nó là chủ đề chung.
- Tỷ lệ bài có từ Reuters: 1,3% Fake và 99,8% Real; regex dateline trong 220 ký tự đầu phát hiện 99,2% Real.
- video, image, featured và getty xuất hiện nhiều hơn ở Fake, có thể phản ánh phần template/credit thay vì sự thật của nội dung.
- Độ dài và phong cách bề mặt là đặc trưng mô tả tập này; không phải quy luật phổ quát về tin giả.

Nguồn và phạm vi phép đo được ghi trong EDA_FINDINGS.md. Không phân phối CSV hoặc nguyên văn bài trong repo; cần kiểm tra quyền sử dụng của nguồn khi chia sẻ dữ liệu/artifact.

## 3. Tiền xử lý, nhãn và chia tập

Theo [DATA-02](DATA02_REPORT.md), 44.898 bài gốc còn 38.164 bài sau lọc rỗng, bản sao và cách ly ca cần kiểm tra.
417 bài được giữ riêng theo các quy tắc rà soát (413 Fake, 4 Real); thêm nhóm gần trùng hai bài khác nhãn bị cách ly.
Cách ly không đồng nghĩa nhãn sai. Quy tắc này có tác động không cân bằng giữa hai lớp và có thể làm thay đổi phân phối.

Khóa trùng chính xác: Unicode NFKC, gộp khoảng trắng và casefold.
Gần trùng: shingle 5 từ, MinHash 128 permutations, seed 42; LSH truy hồi ở ngưỡng 0,70, chỉ nối cặp được xác nhận Jaccard ≥0,85.
Giữ cả thành phần liên thông trong một tập. Không phát hiện chồng lấn ID/khóa nội dung/nhóm đã tìm được giữa các tập; LSH vẫn có thể bỏ sót bản diễn đạt lại hoặc cùng sự kiện.

| Tập | Tổng | Fake | Real |
|---|---:|---:|---:|
| Train | 30.537 | 13.590 | 16.947 |
| Validation | 3.824 | 1.698 | 2.126 |
| Test | 3.803 | 1.692 | 2.111 |

Checkpoint tin cậy của nhóm được khôi phục theo DATA02_HANDOFF.md; không tạo phép chia mới rồi gắn điểm Colab cũ vào.
Luồng audit/ML-01 dùng **0=Fake, 1=Real**; baseline-v0 có quy ước ngược.
Chỉ text_clean là đặc trưng; title, subject, date, ID, nhóm và cột audit không đưa vào bộ phân loại.
Vectorizer/tokenizer chỉ fit/adapt trên train, chọn mô hình trên validation.

### Dấu vết phiên bản chưa thống nhất hoàn toàn

ML01_RESULTS.md ghi SHA256 prepared_splits.csv là `05d9736daedb95cd97732f0d0368937b4ba424ebb1f88031f72d8c127f4c1760`.
ML02_REPORT.md ghi `64f296e51ae407e73261674b9cd4ebb368971bb9942fa9bd9377a9d22ea06666`.
Khác hash file có thể do thứ tự dòng/cách xuất hoặc dữ liệu khác; **chưa đủ bằng chứng trong repo để xác định nguyên nhân**.
Khi tái lập, phải đối chiếu manifest theo ID, text_clean, group_id, label và split; cùng số dòng không chứng minh cùng phép chia/nội dung.

## 4. Mô hình và kết quả theo từng lần chạy

TF-IDF unigram/bigram: min_df=2, max_df=0,95, max_features=100.000, sublinear_tf=True.
ML-01 chọn mô hình theo validation macro F1, dùng F1(Fake) phá hòa; seed 42 cho LR/SVM.
Accuracy là tỷ lệ dự đoán đúng; F1(Fake) coi Fake là lớp dương; macro F1 là trung bình F1 hai lớp.

### 4.1 ML-01 — số liệu chính thức của so sánh cổ điển

Nguồn: [ML01_RESULTS.md](ML01_RESULTS.md).

| Mô hình | Validation macro F1 | Test Accuracy | Test F1(Fake) | Test macro F1 |
|---|---:|---:|---:|---:|
| Logistic Regression | 0,983546 | 0,982908 | 0,980706 | 0,982683 |
| Multinomial Naive Bayes | 0,954412 | 0,949251 | 0,942781 | 0,948593 |
| Linear SVM | 0,991785 | 0,992637 | 0,991716 | 0,992545 |

Mô hình được chọn: Linear SVM. Test confusion matrix theo hàng thật/cột dự đoán, thứ tự Fake/Real: [[1676,16],[12,2099]], tức 28 lỗi.

### 4.2 ML-03 — LSTM và mốc đối chiếu trong lần chạy riêng

Nguồn: [ML03_REPORT.md](ML03_REPORT.md), [báo cáo máy đọc](reports/ml03_20261022.json).
Embedding 128, LSTM 64, Dropout 0,5, Dense 32 ReLU rồi sigmoid hướng Real; vocab 20.000, chuỗi dài 400.
Adam 0,001, batch 64, seed 42; tối đa 15 epoch, early stopping val_loss patience=2.
Dừng epoch 3 và khôi phục epoch 1.

| Mô hình trong lần chạy ML-03 | Test Accuracy | Test macro F1 | F1(Fake) | Lỗi |
|---|---:|---:|---:|---:|
| Logistic Regression | 98,29% | 98,27% | 98,07% | 65 |
| Linear SVM | 99,32% | 99,31% | 99,23% | 26 |
| Multinomial Naive Bayes | 95,14% | 95,08% | 94,53% | 185 |
| LSTM | 97,74% | 97,71% | 97,45% | 86 |

Không thay điểm ML-01 bằng các mốc ML-03: SVM có 26 lỗi ở ML-03 nhưng 28 ở ML-01; NB cũng khác.
Đây là các lần chạy được báo cáo riêng; chưa xác định nguyên nhân chênh lệch trong tài liệu tổng hợp này.
Không kết luận chúng là một lần chạy đồng nhất hoặc quy toàn bộ chênh lệch cho phần cứng.

LSTM chưa vượt mốc SVM trong lần chạy ML-03; không thay mô hình đã chọn theo validation vì kết quả test.
Đo batch 1: SVM 1,485 ms, LSTM 27,853 ms; LSTM dùng runtime GPU T4, SVM dùng CPU.
Các phép đo không gồm tải model, làm sạch, mạng/UI; không phải benchmark cùng phần cứng hay tải nhiều người dùng.

## 5. Kiểm thử theo cụm chủ đề — ML-02

Nguồn: [ML02_REPORT.md](ML02_REPORT.md), [JSON](reports/ml02_20261025.json).
TF-IDF → SVD → KMeans k=10, seed 42 trên toàn bộ 38.164 bài; nhóm gần trùng giữ trong một cụm.
Bộ định nghĩa cụm fit trên toàn bộ văn bản không dùng nhãn: đây là thiết kế phân cụm mang tính transductive, không phải phép kiểm tra quy trình học chủ đề trên train rồi áp dụng test hoàn toàn mới.
Bộ phân loại của từng fold chỉ học các bài ngoài cụm bị giữ lại. Đây là thí nghiệm riêng, không giữ test khóa cũ làm test của ML-01.

Chỉ chấm cụm có ít nhất 100 bài mỗi lớp; 9/10 cụm đủ điều kiện, phủ 35.165 bài.
Cụm 5 thiếu Fake (93 bài) nên không được chấm.

| Thiết kế | Accuracy gộp | F1(Fake) | Macro F1 | Lỗi |
|---|---:|---:|---:|---:|
| Giữ lại từng cụm | 0,9891 | 0,9886 | 0,9891 | 384 |
| GroupKFold đối chiếu trên cùng phần bài được chấm | 0,9918 | 0,9915 | 0,9918 | 287 |

Macro F1 trung bình fold: 0,9765; thấp nhất cụm 3: 0,9388.
Cụm 3 chỉ có 179 Real và bỏ sót 32 bài Real; Accuracy cao che khuất lỗi ở lớp ít mẫu.
Cụm này có từ hội thoại như just/people/like, nên có thể phản ánh văn phong/nguồn hơn là chủ đề.
Chưa có nhiều seed, độ nhạy theo k/ngưỡng hoặc khoảng tin cậy cho chênh lệch hai thiết kế.
Không diễn giải điểm cao như bằng chứng mô hình bất biến với mọi chủ đề/nguồn.

## 6. Trước/sau xử lý rò rỉ: điều đã đo và còn thiếu

DATA-02 có đo dấu nguồn và số bài trước/sau; trên tập cuối, các mẫu Reuters/dateline/URL/credit được kiểm tra không còn khớp.
Đây là kiểm tra regex, không phải đo mức cải thiện phân loại hay chứng minh không còn rò rỉ.

| Hạng mục | Trạng thái bằng chứng |
|---|---|
| EDA dấu nguồn trên văn bản thô | Có — DATA-01 |
| Tần suất regex và tác động loại/cách ly | Có — DATA-02 |
| Accuracy/F1 trên văn bản đã audit | Có — ML-01/03 |
| Accuracy/F1 nguyên bản vs loại dấu nguồn, cùng ID/split | **Chưa có thí nghiệm đối chứng** |
| Đánh giá ngoài nguồn/mạng xã hội/tiếng Việt | **Chưa thực hiện** |

Không lấy điểm baseline-v0 có split/quy trình khác để suy ra tác động nhân quả của làm sạch.
Để hoàn thành phần ablation của DOC-01: khóa cùng manifest, giữ nguyên ID/nhãn/nhóm ở hai nhánh; fit hai pipeline cùng cấu hình/seed chỉ trên train, một nhánh dùng text gốc và nhánh kia text_clean.
Báo Accuracy, macro F1, F1(Fake), support và confusion matrix; chỉ chọn cấu hình bằng validation.
Giữ nguyên các điểm lịch sử và ghi thí nghiệm mới; không tinh chỉnh quy tắc sau khi xem test.
Muốn chạy cần CSV gốc và manifest/snapshot đã audit; chúng không được commit trong repo.

## 7. Giải thích mô hình và nguy cơ diễn giải sai

Theo [ML04_RESULTS.md](ML04_RESULTS.md), via/read more nghiêng Fake, said/on tuesday/president donald nghiêng Real.
Đây là dấu văn phong hoặc nguồn tiềm ẩn, không phải bằng chứng sự thật.
LIME trên tám ví dụ có fidelity cao nhất khoảng 0,53, trung bình khoảng 0,28; điểm bão hòa và ảnh hưởng bigram khiến xấp xỉ theo từ đơn kém phù hợp.
Mẫu nhỏ không đại diện cho độ tin cậy trên toàn bộ corpus.
Hệ số toàn cục khác đóng góp cục bộ; TF-IDF × hệ số phân rã margin tuyến tính, không phân rã xác suất đã hiệu chỉnh.

Platt scaling trong ML-04 chỉ fit validation. Điểm hiệu chỉnh và nhãn SVM có thể khác ngưỡng 0,5 (8/3.803 bài test được báo cáo).
UI phải dùng label do server trả, diễn đạt rõ điểm không phải xác suất sự kiện sai và cảnh báo giải thích kém phù hợp.
Không coi kết quả giải thích là suy luận nhân quả.

## 8. Đạo đức và điều kiện sử dụng

- **Thiên lệch nguồn/chính trị:** tập thu thập không đại diện cho báo chí nói chung. Xóa từ nguồn không xóa hết quy ước viết; rủi ro gắn nhãn oan cho nguồn hoặc văn phong khác.
- **Phạm vi ngôn ngữ/miền:** chưa có kiểm chứng cho tiếng Việt, bài mạng xã hội ngắn, châm biếm, bình luận hay tin thời điểm mới. Không công bố độ chính xác cho các miền này.
- **Con người kiểm chứng:** dùng để ưu tiên rà soát, đối chiếu bằng chứng độc lập; không tự động chặn bài hoặc xử lý người viết.
- **Phản hồi:** đồng ý/không đồng ý là phản hồi về kết quả, không tự chuyển thành nhãn train; cần kiểm chứng độc lập trước mọi sử dụng huấn luyện.
- **Riêng tư:** không yêu cầu nhập thông tin nhạy cảm; preview lịch sử vẫn có thể chứa thông tin cá nhân. Trước mở demo rộng phải thống nhất thời hạn lưu, cách xóa và thông báo cho người dùng. Chưa tuyên bố chức năng xóa/retention đã có.
- **Truy cập và quyền sử dụng:** không mặc định bài tải được thì được tái phân phối. Không đưa CSV, toàn văn, credential hoặc artifact không rõ nguồn vào Git.
- **An toàn triển khai:** xác thực/phân quyền phải kiểm tra ở server, kiểm thử hai tài khoản, nạp artifact tin cậy; giải thích không thay thế kiểm định dữ liệu.
- **Truyền thông kết quả:** ghi rõ dataset, phép chia, seed, phiên bản và hạn chế; phân biệt test đơn vị/CI với tái chạy dữ liệu thật và đo cloud.

## 9. Tái lập và kiểm tra nghiệm thu

Thực hiện theo DATA02_HANDOFF.md → ML01_RESULTS.md → ML03_HANDOFF.md; ML-02/04 có lệnh riêng trong báo cáo tương ứng.
Khôi phục checkpoint tin cậy nếu cần phép chia Colab; không có checkpoint thì ghi là thí nghiệm mới.
Đối chiếu checksum CSV/checkpoint/cleaner, manifest, label map, phiên bản thư viện và artifact trước suy luận.
Không mở joblib từ nguồn không tin cậy.

Tình trạng DOC-01:

- [x] Trích nguồn dataset và báo cáo nội bộ.
- [x] Mô tả split, seed, chọn mô hình và kết quả theo cụm chủ đề.
- [x] Tổng hợp mô hình cổ điển/LSTM, phân biệt các lần chạy khác số liệu.
- [x] Thảo luận đạo đức, tiếng Việt/mạng xã hội và ý nghĩa điểm.
- [ ] Thí nghiệm đối chứng Accuracy/F1 trước/sau loại dấu nguồn trên cùng manifest.
- [ ] Đối chiếu khác biệt checksum và mốc SVM/NB giữa các lần chạy bằng artifact thực tế.

**Chưa đóng issue #13 chỉ dựa vào việc viết tài liệu này.** Phần ablation theo tiêu chí issue cần bằng chứng chạy thật, không được điền số suy đoán.
