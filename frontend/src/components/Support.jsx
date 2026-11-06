import { useRef } from 'react'
import { Icon } from './Theme'

export default function Support() {
  const dialog = useRef(null)
  return <>
    <button type="button" className="support-launch" aria-label="Mở hỗ trợ" aria-haspopup="dialog"
      onClick={() => dialog.current.showModal()}>?</button>
    <dialog ref={dialog} className="support" aria-labelledby="support-title">
      <div className="support-header">
        <div><p className="eyebrow">TRUNG TÂM HỖ TRỢ</p><h2 id="support-title">Hướng dẫn sử dụng</h2></div>
        <button className="icon-button" type="button" aria-label="Đóng hỗ trợ" onClick={() => dialog.current.close()}>
          <Icon name="close" />
        </button>
      </div>
      <ol className="steps">
        <li>Dán nội dung bài báo tiếng Anh, tối đa 50.000 ký tự.</li>
        <li>Bấm <strong>Phân tích</strong> và đợi mô hình trả điểm.</li>
        <li>Đọc điểm và đối chiếu với nguồn tin, tác giả và bằng chứng.</li>
      </ol>
      <h3>Cách đọc điểm dự đoán</h3>
      <p>Thanh phần trăm chỉ hiển thị tín hiệu của mô hình, không phải xác suất bài báo là giả. Điểm cao chỉ cho biết bài viết cần được kiểm chứng kỹ hơn bằng nguồn độc lập.</p>
      <h3>Câu hỏi thường gặp</h3>
      <details><summary>Tôi có thể dán đường dẫn bài báo không?</summary><p>Hãy sao chép văn bản từ bài báo và dán vào ô nhập. Phiên bản này phân tích nội dung tiếng Anh.</p></details>
      <details><summary>Tôi xem lại kết quả ở đâu?</summary><p>Kết quả phân tích thành công được lưu trong mục Lịch sử của tài khoản.</p></details>
      <details><summary>Tại sao máy chủ báo mô hình chưa sẵn sàng?</summary><p>Dịch vụ phân tích cần được nạp mô hình trước khi trả điểm. Bạn có thể báo lỗi cho nhóm qua liên kết bên dưới.</p></details>
      <a className="support-link" href="https://github.com/Kunte172/sic-fake-news-detector/issues" target="_blank" rel="noreferrer">Liên hệ nhóm qua GitHub <Icon name="arrow" size={16} /></a>
    </dialog>
  </>
}
