# DATA-02 — Kiểm toán dấu nguồn và bài trùng

Ngày kiểm tra: 16/10/2026 (Asia/Saigon). Phạm vi: issue #2 của `Kunte172/sic-fake-news-detector`, mã nền `ee259851b177f3d0162abefde314f01dcda4292c`.

## Kết luận

Đã chạy lại quy trình kiểm toán trên 44.898 bài từ hai CSV Kaggle và đối chiếu trực tiếp với checkpoint do người dùng xuất từ Colab. Khôi phục đúng 38.164 bài đã chia train/validation/test. Không phát hiện chồng lấn ID, khóa nội dung chuẩn hóa hoặc nhóm gần trùng đã tìm được giữa các tập. Không huấn luyện, điều chỉnh hay đánh giá lại mô hình trong DATA-02.

Hàm làm sạch khớp **38.583/38.583 bài được lưu trong checkpoint**, gồm ba tập dữ liệu (38.164), bài chờ kiểm tra (417) và nhóm gần trùng cần xác minh nhãn (2). Không có sai khác ở nội dung gốc, tiêu đề, subject, date, label so với CSV Kaggle tại các ID được lưu. Manifest lưu trong checkpoint khớp với các DataFrame.

Kết quả này xác nhận khả năng tái lập quy trình đã lưu, **không chứng minh đã hết sai lệch nguồn hay mô hình xác minh được sự thật**. Notebook trực tiếp trên Drive chưa được lấy về; bằng chứng sử dụng ở đây là checkpoint và gói tích hợp đã tải từ Colab, cộng hai CSV tải lại từ Kaggle.

## Nguồn và phiên bản

- Dataset: [Fake and Real News Dataset](https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset), hai file `Fake.csv`/`True.csv` tải lại từ nguồn công khai.
- Checkpoint: `sic_ai_step10.joblib` do người dùng tạo; SHA-256 `0be39063e78cb3a13d5614a7c6494e336ec49a9188e19efd24391c2149ffc6bf`.
- Hàm làm sạch: `preprocessing.py` trong `sic_ai_integration_bundle.zip`, sao chép nguyên văn vào `backend/app/colab_preprocessing.py`; SHA-256 `78188fa2daa2bc04fbf5c0522d40a9891a136a9951ccf956fa8e9a479d8fad88`.
- Nhãn Colab trong báo cáo: **0 = Fake, 1 = Real**; dữ liệu đầu vào của mô hình Colab là thân bài đã làm sạch.
- Checksum CSV và phiên bản thư viện nằm trong `docs/reports/data02_verified.json`. Lần chạy cục bộ dùng Python 3.12.14, scikit-learn 1.6.1, pandas 2.3.3, NumPy 2.1.3, SciPy 1.16.3, joblib 1.6.0, datasketch 2.0.0. Checkpoint ghi pandas 2.2.3; các phép đối chiếu thực tế đều đạt trên phiên bản 2.3.3.

## Bảo toàn số dòng và xử lý nhãn

| Bước | Số bài loại/giữ riêng | Còn lại |
|---|---:|---:|
| Dữ liệu gốc | — | 44.898 |
| Rỗng/whitespace trước làm sạch | 631 | 44.267 |
| Cùng khóa gốc nhưng mâu thuẫn nhãn | 0 | 44.267 |
| Bản sao dư theo khóa gốc | 5.630 | 38.637 |
| Rỗng sau làm sạch | 53 | 38.584 |
| Tạm giữ để kiểm tra | 417 | 38.167 |
| Cùng khóa sạch nhưng mâu thuẫn nhãn | 0 | 38.167 |
| Bản sao dư sau làm sạch | 1 | 38.166 |
| Nhóm gần trùng chứa cả hai nhãn | 2 | **38.164** |

Các nguyên nhân giữ riêng có thể chồng lấp: dưới 20 từ (318 bài), còn dấu nguồn ảnh theo mẫu mở rộng (97 bài), mất hơn 30% ký tự và còn nội dung (17 bài). Hợp các nguyên nhân là 417 bài, gồm **413 Fake và 4 Real**. Chưa coi các bài này là lỗi nhãn, chưa tự động gán nhãn lại. CSV chứa nội dung gốc và nguyên nhân được giữ cục bộ để người phụ trách kiểm tra.

Bộ lọc ảnh hưởng hai nhãn không đều. Do đó kết quả mô hình chỉ mô tả tập đã qua lựa chọn; không được suy rộng thành hiệu năng trên tất cả bài viết ngắn, bài có nguồn ảnh hoặc bài đăng mạng xã hội.

## Tần suất dấu hiệu trước và sau làm sạch

Bảng dưới so sánh **cùng 38.637 bài trước khi cách ly**: mẫu số Fake = 17.448, Real = 21.189. Tất cả tỷ lệ dùng cùng biểu thức dò trước và sau trong chương trình audit.

| Dấu hiệu | Fake trước (%) | Fake sau (%) | Real trước (%) | Real sau (%) |
|---|---:|---:|---:|---:|
| Từ Reuters | 1,1978 | 0 | 99,8254 | 0 |
| Mẫu dateline chứa `(Reuters)` | 0 | 0 | 96,1348 | 0 |
| URL hoặc liên kết rút gọn được dò | 24,5243 | 0 | 0,1935 | 0 |
| Nguồn ảnh, mẫu mở rộng | 47,7419 | 0,5559 | 0 | 0 |
| Tham chiếu miền mạng xã hội | 19,6470 | 0,0229 | 0,0330 | 0,0330 |
| Mở đầu viết hoa theo mẫu | 0,5961 | 0,6018 | 84,9356 | 1,1327 |

Mẫu URL gồm `http(s)://`, `www.`, `pic.twitter.com/`, `youtu.be/`; mẫu nguồn ảnh dò cả `Image credit` khi không có dấu hai chấm. Vì mẫu được định nghĩa rộng hơn một số cell kiểm tra ban đầu, không so trực tiếp các tỷ lệ này với tỷ lệ dùng regex khác trong ảnh Colab cũ. Số bài loại/cách ly và kết quả làm sạch vẫn khớp checkpoint.

Trên 38.164 bài được giữ cuối cùng, Reuters/dateline/URL/nguồn ảnh theo các mẫu này đều bằng 0. Còn 3 bài Fake và 7 bài Real khớp mẫu tham chiếu mạng xã hội; đây là cờ kiểm tra, không tự động coi là mã nhúng hoặc xóa câu chỉ vì nhắc tới nền tảng. Mẫu viết hoa còn 94 Fake và 240 Real, cho thấy định dạng nguồn/phong cách chưa biến mất hoàn toàn. Regex cũng có thể bỏ sót dấu hiệu khác.

## Subject và date là yếu tố gây nhiễu

Toàn bộ tám giá trị `subject` gốc chỉ xuất hiện ở một nhãn:

| Subject | Fake | Real |
|---|---:|---:|
| Government News | 1.570 | 0 |
| Middle-east | 778 | 0 |
| News | 9.050 | 0 |
| US_News | 783 | 0 |
| left-news | 4.459 | 0 |
| politics | 6.841 | 0 |
| politicsNews | 0 | 11.272 |
| worldnews | 0 | 10.145 |

Không dùng `subject` làm đặc trưng. Giữ riêng từng `subject` gốc chỉ là kiểm tra dịch chuyển phân phối; chưa đáp ứng phép kiểm thử theo chủ đề chung có hai nhãn của ML-02.

`date` phân tích được 44.888/44.898 dòng; 10 dòng chưa phân tích được đều thuộc Fake. Khoảng ngày đọc được: Fake 31/03/2015–19/02/2018, Real 13/01/2016–31/12/2017. Có 35 bài Fake ở tháng 02/2018 và không có bài Real cùng tháng. Đây là giá trị từ CSV, chưa xác thực ngày đăng thực tế. Bảng theo tháng được xuất để kiểm tra lệch thời gian. Không dùng ngày làm đặc trưng và không coi phép chia hiện tại là đánh giá dự đoán tin tương lai.

## Trùng/gần trùng và ranh giới phép chia

Khóa trùng chính xác: Unicode NFKC → gộp khoảng trắng → casefold. Chạy trước và sau làm sạch. Nhóm cùng khóa có hai nhãn được cách ly toàn bộ; không chọn nhãn theo đa số.

Gần trùng: tập shingle 5 từ từ `text_clean`, MinHash 128 hoán vị, seed 42, LSH ngưỡng ứng viên 0,70; chỉ nối cặp có **Jaccard chính xác ≥ 0,85**. Thành phần liên thông giữ các cặp liên quan gián tiếp trong cùng nhóm. Nhóm chứa hai nhãn được giữ riêng để xác minh, không tự kết luận bài nào đúng.

Kết quả trên 38.166 bài trước cách ly nhóm nhãn: **345 cặp**, 37.824 nhóm; 337 nhóm có từ hai bài, tổng 679 bài; nhóm lớn nhất ba bài. Có một nhóm hai nhãn gồm hai bài. Số liệu trùng với kết quả Colab.

| Tập giữ nguyên từ Colab | Bài | Nhóm | Fake | Real |
|---|---:|---:|---:|---:|
| Train | 30.537 | 30.258 | 13.590 | 16.947 |
| Validation | 3.824 | 3.783 | 1.698 | 2.126 |
| Test | 3.803 | 3.782 | 1.692 | 2.111 |

Chương trình kiểm tra độc lập cả nhóm lưu trong checkpoint và nhóm được tính lại. Không có nhóm đã phát hiện bắc cầu qua các tập. LSH là bước truy hồi xấp xỉ, nên không có cam kết tìm được mọi cặp gần trùng; cùng sự kiện hoặc cùng ý nghĩa nhưng khác câu chữ vẫn có thể nằm ở hai tập.

## Kiểm thử và giới hạn bàn giao

**29 kiểm thử đạt:** 23 kiểm thử mới cho DATA-02 và 6 kiểm thử cũ. Có các trường hợp bảo toàn câu sau URL, không cắt nguồn ảnh nằm xa cuối bài, cách ly mâu thuẫn nhãn sau làm sạch, nhóm liên thông, chồng lấn nhóm/nội dung/ID, tái lập phép chia và phát hiện sai lệch nội dung checkpoint. Kiểm tra biên dịch Python đạt. Môi trường Windows sandbox chặn thư mục tạm/TestClient; chạy ngoài sandbox cho kết quả trên. Có cảnh báo deprecation từ Starlette/httpx hiện có, không có kiểm thử thất bại.

Các giới hạn cần giữ trong báo cáo đồ án:

- Hàm Colab xóa cả từ Reuters trong thân bài, có thể làm câu mất thành phần. Quy tắc nguồn ảnh gần cuối bài cũng có thể cắt nội dung. DATA-02 giữ nguyên phiên bản đã dùng để tái lập và ghi nhận giới hạn, không âm thầm thay quy tắc sau khi đã xem test.
- Không dùng số lượng dấu hiệu bằng 0 để khẳng định hết rò rỉ nguồn. Mô hình còn có thể học văn phong, từ vựng và chủ đề.
- Các bước EDA/kiểm tra trước đây đã nhìn toàn bộ dữ liệu; DATA-02 không biến test đó thành một tập kiểm thử bên ngoài hoàn toàn độc lập.
- Chưa chạy ablation nguyên bản/loại dấu nguồn, chưa bổ sung tập kiểm thử nguồn khác hoặc mạng xã hội. Không báo cáo kết quả suy đoán cho các thí nghiệm đó.
- Hàm v0, API và chương trình huấn luyện baseline cũ vẫn được giữ. Luồng Colab mới được đưa vào module dùng chung, cần được người làm ML/API lựa chọn rõ khi tích hợp; xem `DATA02_HANDOFF.md` về khác biệt nhãn và điểm SVM.

Gói bàn giao chỉ bao gồm mã DATA-02, kiểm thử, hướng dẫn và báo cáo tổng hợp. Dữ liệu bài báo, checkpoint và mô hình không được đưa vào gói mã nguồn.
