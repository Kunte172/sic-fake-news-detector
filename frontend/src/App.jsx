import { useState } from 'react'

const apiBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export default function App() {
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function analyze(event) {
    event.preventDefault()
    setLoading(true)
    setResult(null)
    setError('')
    try {
      const response = await fetch(`${apiBase}/api/v1/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (response.status === 503) throw new Error('Chưa có mô hình. Hãy huấn luyện baseline và cấu hình MODEL_PATH theo README.')
      if (response.status === 422) throw new Error('Vui lòng nhập bài báo tiếng Anh từ 80 đến 50.000 ký tự.')
      if (!response.ok) throw new Error('Không thể phân tích. Hãy kiểm tra API và thử lại.')
      setResult(await response.json())
    } catch (cause) {
      setError(cause instanceof TypeError ? 'Không kết nối được API. Hãy khởi chạy backend.' : cause.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="shell">
      <header className="header"><span className="brand">SIC / FAKE NEWS LENS</span><span className="tag">Đồ án nhóm · v0</span></header>
      <section className="hero">
        <p className="eyebrow">XỬ LÝ NGÔN NGỮ TỰ NHIÊN</p>
        <h1>Sàng lọc dấu hiệu đáng ngờ trong bài báo.</h1>
        <p className="lead">Dán nội dung bài báo tiếng Anh để xem điểm dự đoán của mô hình. Kết quả chỉ hỗ trợ lựa chọn thông tin cần kiểm tra thêm.</p>
      </section>
      <form className="panel" onSubmit={analyze}>
        <label htmlFor="article">Nội dung bài báo</label>
        <textarea id="article" value={text} onChange={(event) => setText(event.target.value)}
          minLength={80} maxLength={50000} required placeholder="Paste an English news article here..." />
        <div className="form-footer"><span>{text.length.toLocaleString('vi-VN')} / 50.000 ký tự</span><button disabled={loading || text.length < 80}>{loading ? 'Đang phân tích...' : 'Phân tích văn bản'}</button></div>
      </form>
      {error && <div className="notice error" role="alert">{error}</div>}
      {result && <section className="panel result" aria-live="polite">
        <p className="eyebrow">KẾT QUẢ MÔ HÌNH · {result.model_version}</p>
        <h2>{result.label === 'SUSPICIOUS' ? 'Cần kiểm tra thêm' : 'Ít dấu hiệu đáng ngờ hơn'}</h2>
        <p className="score">{Math.round(result.score * 100)}% <small>điểm lớp “fake” trên bộ dữ liệu huấn luyện</small></p>
        <p>Điểm này không phải xác suất bài báo sai sự thật. Hãy đối chiếu tác giả, nguồn, thời điểm và bằng chứng độc lập.</p>
      </section>}
      <footer>Phạm vi v0: bài báo tiếng Anh · Chưa hỗ trợ URL, tài khoản và LIME · Không dùng để đưa ra kết luận tự động</footer>
    </main>
  )
}
