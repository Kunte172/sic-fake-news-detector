import { useRef } from 'react'
import { Icon } from './Theme'

const topics = [
  {
    icon: 'warning',
    title: 'Tin giả là gì?',
    text: 'Tin giả là thông tin sai lệch hoặc bị bóp méo, thường được chia sẻ như tin thật để gây chú ý, tạo hoang mang hoặc dẫn dắt người đọc.',
  },
  {
    icon: 'scan',
    title: 'Dấu hiệu nhận biết',
    text: 'Cẩn thận với tiêu đề giật gân, lời khẳng định tuyệt đối, hình ảnh thiếu nguồn, lỗi chính tả bất thường và nội dung cố kích động cảm xúc.',
  },
  {
    icon: 'check',
    title: 'Kiểm chứng thông tin',
    text: 'Đọc toàn bộ bài viết, kiểm tra tác giả và ngày đăng, đối chiếu với nhiều nguồn uy tín, đồng thời tìm nguồn gốc của hình ảnh hoặc trích dẫn.',
  },
  {
    icon: 'shield',
    title: 'Cách phòng tránh',
    text: 'Không vội chia sẻ khi chưa kiểm chứng. Hãy xem kỹ đường dẫn, kiểm tra tài khoản đăng tin, bật bảo mật tài khoản và báo cáo nội dung đáng ngờ.',
  },
  {
    icon: 'info',
    title: 'Khi gặp tin đáng ngờ',
    text: 'Dừng lại, lưu lại bằng chứng, kiểm tra thông tin từ nguồn chính thức và dùng chức năng báo cáo của nền tảng thay vì tranh luận hoặc lan truyền thêm.',
  },
]

export default function LearnMore() {
  const dialog = useRef(null)
  return <>
    <button type="button" className="learn-more-button" onClick={() => dialog.current.showModal()}>
      Tìm hiểu thêm <Icon name="arrow" size={16} />
    </button>
    <dialog ref={dialog} className="learn-dialog" aria-labelledby="learn-title">
      <div className="support-header">
        <div><p className="eyebrow">KIẾN THỨC KIỂM CHỨNG</p><h2 id="learn-title">Tìm hiểu thêm</h2></div>
        <button className="icon-button" type="button" aria-label="Đóng tìm hiểu thêm" onClick={() => dialog.current.close()}>
          <Icon name="close" />
        </button>
      </div>
      <p className="learn-intro">Một vài nguyên tắc đơn giản giúp bạn đọc tin tỉnh táo và hạn chế chia sẻ thông tin sai lệch.</p>
      <div className="learn-grid">
        {topics.map((topic) => <article className="learn-card" key={topic.title}>
          <span className="tile"><Icon name={topic.icon} /></span>
          <div><h3>{topic.title}</h3><p>{topic.text}</p></div>
        </article>)}
      </div>
      <p className="notice">Công cụ AI chỉ mang tính hỗ trợ. Hãy luôn đối chiếu với nguồn tin chính thức trước khi đưa ra kết luận.</p>
    </dialog>
  </>
}
