# ML-04 — Giải thích mô hình bằng hệ số tuyến tính và LIME

## Phạm vi và dữ liệu

Giải thích mô hình ML-01 được chọn: **Linear SVM**, TF-IDF unigram/bigram, nhãn **0 = Fake, 1 = Real**, bằng (1) hệ số toàn cục và (2) LIME cho từng bài. Mọi kết quả mô tả **lý do mô hình dự đoán**, không phải bằng chứng một bài đúng hay sai về sự thật.

**Phép chia:** khôi phục nguyên vẹn từ checkpoint Colab (`split_origin = restored_colab_unchanged`, SHA-256 checkpoint `0be39063…c6bf`): train 30.537 / validation 3.824 / test 3.803, tổng 38.164 bài. Môi trường chạy: scikit-learn 1.6.1, pandas 2.3.3. Phép chia này trùng với `ML01_RESULTS.md` và ML-03.

**Điểm của mô hình được giải thích (test):** accuracy 0,9926; F1(Fake) 0,9917; macro F1 0,9925; ma trận nhầm lẫn `[[1676, 16], [12, 2099]]` (hàng = nhãn thật, thứ tự `[Fake, Real]`). Số liệu Linear SVM và Logistic Regression tái lập đúng như `ML01_RESULTS.md`.

## Phương pháp

- **Làm sạch:** `clean_source_markers` áp dụng đúng một lần lên văn bản (như lúc huấn luyện).
- **Điểm Fake:** Linear SVM không có xác suất, nên điểm được hiệu chỉnh bằng Platt scaling, **chỉ fit trên validation** (3.824 bài): `slope = −7,499`, `intercept = 0,456`. Trên test: Brier = 0,0057.
- **Từ khóa toàn cục:** hệ số `coef_` của SVM, đảo dấu để dương = nghiêng về Fake.
- **LIME:** `LimeTextExplainer`, 1.000 mẫu nhiễu, 10 từ hiển thị, seed 42, trên hàm điểm đã hiệu chỉnh. `fidelity` là R² của mô hình xấp xỉ cục bộ chỉ dùng 10 từ đó.
- **Ví dụ:** 2 bài mỗi ô (nhãn thật × dự đoán) từ tập test, chọn ngẫu nhiên seed 42, tổng 8 bài.

## Kết quả 1 — Từ khóa toàn cục

| Nhóm | Fake (hệ số dương) | Real (hệ số âm) |
|---|---|---|
| Dấu hiệu trình bày/tổng hợp tin | `via` 6,13; `read more` 4,25; `read` 3,04; `watch` 2,23 | — |
| Động từ tường thuật | — | `said` −6,10; `said on` −3,95; `said in` −2,62; `he said` −1,80; `told` −1,69 |
| Thứ trong tuần, tháng | — | `on tuesday` −3,19; `on wednesday` −3,15; `on thursday` −2,84; `on friday` −2,71; `on monday` −2,55; `nov` −1,85 |
| Cách gọi tên/chức danh | `president trump` 2,54; `sen` 2,60; `rep` 2,09; `mr` 2,25 | `president donald` −3,54; `president barack` −1,69 |
| Từ chung, ngôi thứ hai | `this` 2,55; `just` 2,46; `you` 1,78; `is` 1,89 | `on` −3,02 |
| Thực thể chính trị | `gop`, `obama`, `hillary`, `america`, `us` | `republican` −1,99 |

**Nhận xét.**
- Top 20 không còn `reuters`, URL hay dateline, nên bước làm sạch của DATA-02 có hiệu lực với các mẫu nó nhắm tới. Hàm `leakage_report` chỉ cắm cờ `via`.
- Mô hình dựa mạnh vào **văn phong và quy ước nguồn**: `via`/`read more` là mẫu tổng hợp tin đăng lại; `said`, `on <thứ>`, `president donald` là văn phong bản tin hãng thông tấn; `president trump` đối lập `president donald` là khác biệt quy ước gọi tên giữa các nguồn. Đây là tín hiệu nguồn/văn phong, không phải tín hiệu về tính đúng sai của nội dung, đúng như cảnh báo của DATA-02.
- Kết quả gần như không đổi so với lần chạy trên phép chia riêng (cùng các từ đứng đầu, trọng số lệch dưới 0,2), nên kết luận không phụ thuộc cách chia dữ liệu.

## Kết quả 2 — Ví dụ cục bộ (LIME)

| Dòng (`_row_id`) | Thật → Dự đoán | Điểm Fake | Fidelity | Từ ảnh hưởng nhất (trọng số LIME) |
|---|---|---:|---:|---|
| 8773 | Fake → Fake (đúng) | 1,0000 | 0,004 | `ISIS` 0,0009; `politics`; `country` (gần như nhiễu) |
| 13468 | Fake → Fake (đúng) | 1,0000 | 0,091 | `the`, `Read`, `this`, `Obama` (≈0,01) |
| 1679 | Fake → Real (**sai**) | 0,3154 | 0,529 | `said` −0,34; `Donald` −0,16; `on` −0,12; `that` +0,14 |
| 7436 | Fake → Real (**sai**) | 0,5539 | 0,461 | `percent` −0,15; `tax` −0,14; `year` −0,14; `dollars` +0,11 |
| 40721 | Real → Fake (**sai**) | 0,8660 | 0,423 | `via` +0,17; `the` +0,09; `rs` −0,08; `tmsnrt` −0,04 |
| 40640 | Real → Fake (**sai**) | 0,9832 | 0,314 | `you` +0,04; `now`; `recently`; `is`; `this` |
| 33663 | Real → Real (đúng) | 0,0000 | 0,200 | `said` −0,06; `intend`; `trade`; `former` |
| 34406 | Real → Real (đúng) | 0,0000 | 0,193 | `said` −0,04; `Barack`; `Nov`; `Ipsos` |

**Nhận xét.**
- **Bài Fake bị đoán là Real (1679):** viết theo kiểu bản tin (`said`, `Donald`, `on`), nên văn phong kéo mô hình về Real dù bài thuộc nhãn Fake.
- **Bài Real bị đoán là Fake (40721):** chữ `via` đơn lẻ đẩy mạnh về Fake (+0,17, lớn nhất trong bài). Trong cùng bài, `rs` và `tmsnrt` đẩy về Real; hai token này nhiều khả năng là mảnh của một link rút gọn kiểu `tmsnrt.rs/...` còn sót sau làm sạch (`WEB_LINK` chỉ bắt link có `http`, `www`, `pic.twitter.com/`, `youtu.be/`), nên là một dấu nguồn rò rỉ nhỏ mà DATA-02 chưa loại. Đây là suy đoán từ token, cần kiểm tra bằng cách đọc văn bản gốc.
- **Bài Real bị đoán là Fake (40640):** giọng thân mật, ngôi thứ hai (`you`, `now`, `recently`, `is`) bị đẩy về Fake.
- **Điểm và nhãn có thể lệch nhau (7436):** điểm 0,55 nhưng nhãn là `LESS_SUSPICIOUS`. Lý do: Platt scaling đặt ranh giới của SVM (margin = 0) ở điểm 0,61, và điểm hiệu chỉnh chỉ đạt 0,5 khi margin ≈ 0,061. Vì vậy các bài SVM dự đoán Real với margin rất nhỏ có điểm từ 0,5 đến 0,61. Trên test có **8/3.803 bài (0,21%)** như vậy. Nhãn công bố theo SVM (khớp số liệu ML-01); giao diện và API không được tự suy nhãn từ điểm.
- **Độ tin cậy của LIME thấp ở cả 8 bài:** fidelity cao nhất 0,53, trung bình 0,28; 2/8 dưới 0,15 (8773 gần như nhiễu, trọng số cỡ 0,001, vài từ ngược dấu với `global_weight`), 5/8 dưới 0,4. Hai nguyên nhân: điểm bão hòa (gần 0 hoặc 1) làm hàm điểm gần phẳng quanh bài, và xấp xỉ chỉ dùng 10 từ cho một bài dài hàng trăm từ. Giao diện phải cảnh báo độ tin cậy thấp theo `fidelity`, không trình bày danh sách từ như lý do chắc chắn.
- Từ như `the`, `s`, `of` có `global_weight = null` nhưng vẫn có trọng số LIME, vì xóa chúng phá các cặp từ như `the us` mà mô hình dùng, trong khi LIME chỉ hiện từ đơn.

## Giới hạn và lưu ý đạo đức (cho DOC-01)

- Giải thích mô tả **hành vi của mô hình trên dữ liệu Kaggle này**; điểm cao của ML-01 không nghĩa là mô hình kiểm chứng được sự thật.
- Mô hình nhạy với văn phong và nguồn: bài tin giả viết theo kiểu bản tin có thể bị cho là bình thường; bài thật mang giọng ý kiến, thân mật, hay chỉ chứa một từ như `via`, có thể bị gắn `SUSPICIOUS`. Nguy cơ này đặc biệt đáng kể với nội dung mạng xã hội, bài ý kiến hay nguồn ngoài bộ dữ liệu.
- LIME là xấp xỉ cục bộ, có thể đổi theo seed và số mẫu; trọng số không phải quan hệ nhân quả, và hiển thị theo từ đơn che bớt ảnh hưởng của cặp từ.
- Điểm Fake là điểm đã hiệu chỉnh trên validation của bộ dữ liệu này, không phải xác suất bài sai sự thật.
- `explanation` chỉ chứa từ khóa, không lưu nguyên văn bài.
- Hiển thị cho người dùng cần nói rõ "đây là lý do mô hình dự đoán, không phải bằng chứng sự kiện đúng/sai" và cảnh báo khi `fidelity` thấp.

## Đề xuất tiếp theo (không làm trong ML-04)

- Rà thêm các mảnh link rút gọn (`tmsnrt`, `rs`) và `via` trong quy tắc làm sạch. Mọi thay đổi quy tắc hay mô hình phải ghi là **thí nghiệm mới** (quy tắc 6 của DATA-02), không sửa theo kết quả test.
- Ablation bỏ nhóm từ nghi văn phong/nguồn (`via`, `read more`, thứ trong tuần, `said`) để đo mức mô hình phụ thuộc.
- Kiểm tra theo chủ đề chung (ML-02) và tập nguồn khác.
- Với mô hình tuyến tính, đối chiếu LIME với đóng góp chính xác (giá trị TF-IDF × hệ số) để có giải thích ổn định hơn ở bài điểm bão hòa; tăng số từ hiển thị cũng làm `fidelity` tăng.

## Tái chạy

```bash
python -m ml.src.audit_data --data-dir ml/data/raw --output-dir ml/artifacts/data02 --checkpoint "<đường dẫn>/sic_ai_step10.joblib" --trust-local-checkpoint
python -m ml.src.train_classic_models
python -m ml.src.calibrate_selected
python -m ml.src.explain_examples
python -m unittest backend.tests.test_explain -v
```
Đầu ra cục bộ (Git bỏ qua): `ml/artifacts/ml01/ml01_calibration.json`, `ml/artifacts/explain/global_keywords.json`, `ml/artifacts/explain/examples.json`.
