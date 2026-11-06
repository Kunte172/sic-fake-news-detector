import { useRef } from 'react'
import { Icon } from './Theme'

export default function About() {
  const dialog = useRef(null)
  return <>
    <button type="button" className="learn-more-button secondary-learn" onClick={() => dialog.current.showModal()}>
      Giới thiệu <Icon name="arrow" size={16} />
    </button>
    <dialog ref={dialog} className="about-dialog" aria-labelledby="about-title">
      <div className="support-header">
        <div><p className="eyebrow">VỀ FNL / FAKE NEWS LENS</p><h2 id="about-title">Giới thiệu về chúng tôi</h2></div>
        <button className="icon-button" type="button" aria-label="Đóng giới thiệu" onClick={() => dialog.current.close()}>
          <Icon name="close" />
        </button>
      </div>
      <div className="about-lead">
        <span className="about-symbol"><Icon name="scan" size={34} /></span>
        <div>
          <h3>Cùng đọc tin tỉnh táo hơn</h3>
          <p>FNL / Fake News Lens là công cụ hỗ trợ sàng lọc dấu hiệu đáng ngờ trong các bài báo tiếng Anh.</p>
        </div>
      </div>
      <p>Internet và mạng xã hội giúp thông tin được chia sẻ nhanh chóng, nhưng cũng khiến tin sai lệch lan truyền dễ hơn. Chúng tôi xây dựng công cụ này để giúp người đọc có thêm một bước kiểm tra trước khi tin hoặc chia sẻ nội dung.</p>
      <h3>Ứng dụng hoạt động như thế nào?</h3>
      <p>Bạn có thể dán nội dung bài báo vào hệ thống. Mô hình sẽ phân tích và trả về điểm dự đoán cùng nhãn kết quả để bạn biết nội dung nào cần kiểm chứng kỹ hơn.</p>
      <div className="about-points">
        <div><span className="tile"><Icon name="scan" /></span><strong>Phân tích nhanh</strong><small>Hỗ trợ sàng lọc nội dung trong vài bước.</small></div>
        <div><span className="tile"><Icon name="check" /></span><strong>Đọc có kiểm chứng</strong><small>Khuyến khích đối chiếu với nguồn chính thức.</small></div>
        <div><span className="tile"><Icon name="shield" /></span><strong>Đặt người dùng làm trung tâm</strong><small>Minh bạch về giới hạn của kết quả AI.</small></div>
      </div>
      <p className="notice">Kết quả của công cụ chỉ mang tính hỗ trợ, không khẳng định một bài viết là thật hay giả. Hãy kiểm tra thêm tác giả, thời gian, nguồn gốc và các nguồn độc lập.</p>
    </dialog>
  </>
}
