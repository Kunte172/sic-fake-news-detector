import { useEffect, useMemo, useState } from 'react'
import { api } from './api'
import { Brand, Icon, LanguageButton, ThemeButton } from './components/Theme'

const PAGE_SIZE_OPTIONS = [10, 25, 50]

export default function AdminDashboard({ token, theme, language, onLogout, onOpenAnalyze }) {
  const en = language.language === 'en'
  const [summary, setSummary] = useState(null)
  const [items, setItems] = useState([])
  const [pageSize, setPageSize] = useState(10)
  const [page, setPage] = useState(0)
  const [filter, setFilter] = useState('')
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState('')

  async function loadDashboard(signal) {
    setBusy(true)
    setError('')
    try {
      const [nextSummary, disputed] = await Promise.all([
        api('/admin/summary', { token, signal }),
        api('/admin/disputed?limit=50&offset=0', { token, signal }),
      ])
      if (signal?.aborted) return
      setSummary(nextSummary)
      setItems(disputed.items || [])
      setPage(0)
    } catch (cause) {
      if (signal?.aborted) return
      if (cause.status === 401) onLogout(en ? 'Your session has expired.' : 'Phiên đăng nhập đã hết hạn.')
      else if (cause.status === 403) setError(en ? 'You do not have administrator access.' : 'Tài khoản không có quyền quản trị.')
      else setError(en ? 'Could not load the admin dashboard.' : 'Không thể tải dữ liệu quản trị.')
    } finally {
      if (!signal?.aborted) setBusy(false)
    }
  }

  useEffect(() => {
    const controller = new AbortController()
    loadDashboard(controller.signal)
    return () => controller.abort()
  }, [token])

  const filteredItems = useMemo(() => {
    const query = filter.trim().toLowerCase()
    if (!query) return items
    return items.filter((item) => [item.content_preview, item.comment, item.label, item.model_version]
      .filter(Boolean).some((value) => String(value).toLowerCase().includes(query)))
  }, [items, filter])
  const pageCount = Math.max(1, Math.ceil(filteredItems.length / pageSize))
  const currentPage = Math.min(page, pageCount - 1)
  const visibleItems = filteredItems.slice(currentPage * pageSize, (currentPage + 1) * pageSize)

  function changePageSize(event) {
    setPageSize(Number(event.target.value))
    setPage(0)
  }

  const cards = [
    ['total_users', en ? 'Users' : 'Người dùng', 'user'],
    ['total_analyses', en ? 'Analyses' : 'Lượt phân tích', 'scan'],
    ['total_feedbacks', en ? 'Feedback' : 'Phản hồi', 'check'],
    ['disputed_feedbacks', en ? 'Disagreed' : 'Không đồng ý', 'warning'],
  ]

  return <main className="admin-page">
    <header className="topbar"><div className="topbar-inner">
      <Brand />
      <div className="admin-top-actions">
        <button type="button" className="secondary small" onClick={onOpenAnalyze}>{en ? 'Analysis' : 'Phân tích'}</button>
        <LanguageButton {...language} /><ThemeButton {...theme} />
        <button type="button" className="secondary small" onClick={() => onLogout()}>{en ? 'Sign out' : 'Đăng xuất'}</button>
      </div>
    </div></header>
    <section className="admin-content" aria-labelledby="admin-title">
      <div className="admin-heading">
        <div><p className="eyebrow">{en ? 'ADMINISTRATION' : 'QUẢN TRỊ HỆ THỐNG'}</p><h1 id="admin-title">{en ? 'Admin dashboard' : 'Bảng điều khiển quản trị'}</h1>
          <p className="muted">{en ? 'Monitor platform activity and review disputed predictions.' : 'Theo dõi hoạt động hệ thống và các dự đoán bị phản hồi.'}</p></div>
        <button className="secondary" type="button" disabled={busy} onClick={() => loadDashboard()}><Icon name="refresh" size={16} /> {en ? 'Refresh' : 'Làm mới'}</button>
      </div>
      {error && <div className="notice error" role="alert">{error}</div>}
      <div className="admin-stats" aria-live="polite">
        {cards.map(([key, label, icon]) => <article className="admin-stat" key={key}>
          <span className="tile"><Icon name={icon} /></span><div><strong>{busy && !summary ? '—' : (summary?.[key] ?? 0).toLocaleString('vi-VN')}</strong><span>{label}</span></div>
        </article>)}
      </div>
      <section className="card admin-disputed" aria-labelledby="disputed-title">
        <div className="admin-list-heading"><div><h2 id="disputed-title">{en ? 'Disputed cases' : 'Ca bị phản hồi không đồng ý'}</h2><p className="muted">{en ? 'Review feedback marked as incorrect by users.' : 'Xem các kết quả được người dùng đánh giá là chưa đúng.'}</p></div>
          <div className="admin-controls"><input aria-label={en ? 'Filter cases' : 'Lọc ca phản hồi'} value={filter} onChange={(event) => { setFilter(event.target.value); setPage(0) }} placeholder={en ? 'Filter…' : 'Lọc…'} />
            <select aria-label={en ? 'Rows per page' : 'Số dòng mỗi trang'} value={pageSize} onChange={changePageSize}>{PAGE_SIZE_OPTIONS.map((size) => <option key={size} value={size}>{size} / trang</option>)}</select></div></div>
        {busy && <p className="admin-state" role="status">{en ? 'Loading cases…' : 'Đang tải dữ liệu…'}</p>}
        {!busy && !error && !visibleItems.length && <p className="admin-state">{filter ? (en ? 'No matching cases.' : 'Không có ca phù hợp.') : (en ? 'No disputed cases yet.' : 'Chưa có ca bị phản hồi.')}</p>}
        {!busy && visibleItems.length > 0 && <div className="admin-case-list">{visibleItems.map((item) => <article className="admin-case" key={item.feedback_id}>
          <div className="admin-case-meta"><span>#{item.analysis_id}</span><span>{new Date(item.created_at).toLocaleString('vi-VN')}</span><span className="verdict risky">{item.label}</span></div>
          <p>{item.content_preview}</p><small>{item.comment || (en ? 'No comment' : 'Không có ghi chú')} · {item.model_version} · {Math.round((item.label === 'LESS_SUSPICIOUS' ? 1 - item.score : item.score) * 10000) / 100}% {item.label === 'LESS_SUSPICIOUS' ? 'tin thật' : 'nghi ngờ tin giả'}</small>
        </article>)}</div>}
        {filteredItems.length > pageSize && <div className="admin-pagination"><span className="muted">{currentPage + 1} / {pageCount}</span><div className="actions">
          <button className="secondary small" disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>{en ? 'Previous' : 'Trang trước'}</button>
          <button className="secondary small" disabled={currentPage >= pageCount - 1} onClick={() => setPage(currentPage + 1)}>{en ? 'Next' : 'Trang sau'}</button>
        </div></div>}
      </section>
    </section>
  </main>
}
