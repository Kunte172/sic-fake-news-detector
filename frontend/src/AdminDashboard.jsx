import { useEffect, useMemo, useState } from 'react'

const apiBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const PAGE_SIZES = [10, 25, 50]
const COMMENT_PREVIEW_CHARS = 200
const LABEL_OPTIONS = [
  { value: 'ALL', text: 'Tất cả nhãn' },
  { value: 'SUSPICIOUS', text: 'SUSPICIOUS (cần kiểm tra thêm)' },
  { value: 'LESS_SUSPICIOUS', text: 'LESS_SUSPICIOUS (ít dấu hiệu đáng ngờ hơn)' },
]

export function percent(part, whole) {
  if (!Number.isFinite(part) || !Number.isFinite(whole) || whole <= 0) return null
  return Math.round((part / whole) * 1000) / 10
}

export function formatPercent(value) {
  return value === null ? '—' : `${value.toLocaleString('vi-VN', { maximumFractionDigits: 1 })}%`
}

export function formatNumber(value) {
  return Number.isFinite(value) ? value.toLocaleString('vi-VN') : '—'
}

export function formatDate(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? String(value ?? '') : date.toLocaleString('vi-VN')
}

// Bộ lọc chỉ chạy trên các dòng đã tải của trang hiện tại: API admin chưa có tham số lọc.
export function filterCases(items, { label = 'ALL', model = 'ALL', query = '' }) {
  const needle = query.trim().toLowerCase()
  return items.filter((item) => {
    if (label !== 'ALL' && item.label !== label) return false
    if (model !== 'ALL' && item.model_version !== model) return false
    if (!needle) return true
    return (
      String(item.content_preview ?? '').toLowerCase().includes(needle) ||
      String(item.comment ?? '').toLowerCase().includes(needle)
    )
  })
}

// Gọi một endpoint admin. Token đã đổi hoặc phiên đã bị xóa thì bỏ qua kết quả trả về muộn.
function useAdminData(path, { token, onUnauthorized, isSessionCurrent }) {
  const [state, setState] = useState({ status: 'loading', data: null, message: '' })
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setState((previous) => ({ ...previous, status: 'loading', message: '' }))

    async function load() {
      try {
        const response = await fetch(`${apiBase}${path}`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        })
        if (!isSessionCurrent()) return
        if (response.status === 401) {
          onUnauthorized('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
          return
        }
        if (response.status === 403) {
          setState({ status: 'forbidden', data: null, message: 'Tài khoản này không có quyền ADMIN.' })
          return
        }
        if (!response.ok) throw new Error(`Máy chủ trả về lỗi ${response.status}.`)
        const data = await response.json()
        if (!isSessionCurrent()) return
        setState({ status: 'ok', data, message: '' })
      } catch (cause) {
        if (cause.name === 'AbortError' || !isSessionCurrent()) return
        setState({
          status: 'error',
          data: null,
          message: cause instanceof TypeError ? 'Không kết nối được API. Hãy khởi chạy backend.' : cause.message,
        })
      }
    }

    load()
    return () => controller.abort()
    // onUnauthorized và isSessionCurrent là hàm mới ở mỗi lần render nên không đưa vào danh sách phụ thuộc.
  }, [path, token, nonce])

  return { ...state, reload: () => setNonce((value) => value + 1) }
}

export function ViewTabs({ view, onChange }) {
  return (
    <nav className="view-tabs" aria-label="Chuyển màn hình">
      <button
        type="button"
        className={`small ${view === 'analyze' ? '' : 'secondary'}`}
        aria-pressed={view === 'analyze'}
        onClick={() => onChange('analyze')}
      >
        Phân tích
      </button>
      <button
        type="button"
        className={`small ${view === 'admin' ? '' : 'secondary'}`}
        aria-pressed={view === 'admin'}
        onClick={() => onChange('admin')}
      >
        Quản trị
      </button>
    </nav>
  )
}

function StatCard({ label, value, sub }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

export function SummaryCards({ status, data, message, onRetry }) {
  if (status === 'forbidden') return null
  if (status === 'error') {
    return (
      <div className="notice error" role="alert">
        Không tải được thống kê. {message}{' '}
        <button type="button" className="small secondary" onClick={onRetry}>Thử lại</button>
      </div>
    )
  }

  const hasData = Boolean(data)
  const value = (field) => (hasData ? formatNumber(data[field]) : '…')
  const disputedRate = hasData ? percent(data.disputed_feedbacks, data.total_feedbacks) : null
  const feedbackRate = hasData ? percent(data.total_feedbacks, data.total_analyses) : null

  return (
    <div className="stats-grid" aria-busy={status === 'loading'}>
      <StatCard label="Người dùng" value={value('total_users')} />
      <StatCard label="Lượt phân tích" value={value('total_analyses')} />
      <StatCard
        label="Phản hồi"
        value={value('total_feedbacks')}
        sub={hasData ? `${formatPercent(feedbackRate)} số lượt phân tích có phản hồi` : undefined}
      />
      <StatCard
        label="Không đồng ý"
        value={value('disputed_feedbacks')}
        sub={
          hasData
            ? disputedRate === null
              ? 'Chưa có phản hồi nào'
              : `${formatPercent(disputedRate)} số phản hồi`
            : undefined
        }
      />
    </div>
  )
}

function CaseComment({ comment }) {
  const [expanded, setExpanded] = useState(false)
  if (!comment) return <p className="case-comment muted">Người dùng không ghi lý do.</p>

  const isLong = comment.length > COMMENT_PREVIEW_CHARS
  const shown = expanded || !isLong ? comment : `${comment.slice(0, COMMENT_PREVIEW_CHARS)}…`
  return (
    <p className="case-comment">
      <strong>Lý do người dùng ghi:</strong> “{shown}”{' '}
      {isLong && (
        <button type="button" className="link" onClick={() => setExpanded((value) => !value)}>
          {expanded ? 'Thu gọn' : 'Xem thêm'}
        </button>
      )}
    </p>
  )
}

function isHttpUrl(value) {
  return /^https?:\/\/\S+$/i.test(String(value ?? '').trim())
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    // Trình duyệt chặn Clipboard API: dùng cách dự phòng.
    try {
      const area = document.createElement('textarea')
      area.value = text
      area.setAttribute('readonly', '')
      area.style.position = 'fixed'
      area.style.opacity = '0'
      document.body.appendChild(area)
      area.select()
      const ok = document.execCommand('copy')
      document.body.removeChild(area)
      return ok
    } catch {
      return false
    }
  }
}

function LinkActions({ url }) {
  const [copyState, setCopyState] = useState('idle') // idle | done | failed

  async function handleCopy() {
    const ok = await copyText(url)
    setCopyState(ok ? 'done' : 'failed')
    window.setTimeout(() => setCopyState('idle'), 2000)
  }

  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', margin: '8px 0' }}>
      <button type="button" className="secondary small" onClick={handleCopy}>
        {copyState === 'done' ? 'Đã sao chép ✓' : copyState === 'failed' ? 'Không sao chép được' : 'Sao chép đường link'}
      </button>
      <a className="secondary small" href={url} target="_blank" rel="noopener noreferrer">
        Mở link trong tab mới
      </a>
    </div>
  )
}

export function CaseList({ items }) {
  return (
    <div className="history-list">
      {items.map((item) => (
        <article key={item.feedback_id} className="history-item">
          <div className="history-meta">
            <span>
              <strong>Phản hồi #{item.feedback_id}</strong> · Lượt phân tích #{item.analysis_id} ·{' '}
              {formatDate(item.created_at)} · <code>{item.model_version}</code>
            </span>
            <span className={`badge ${item.label === 'SUSPICIOUS' ? 'suspicious' : 'likely'}`}>
              {item.label} ({Math.round(item.score * 100)}%)
            </span>
          </div>
          <p className="history-preview">“{item.content_preview}”</p>
          {isHttpUrl(item.content_preview) && <LinkActions url={item.content_preview.trim()} />}
          <CaseComment comment={item.comment} />
        </article>
      ))}
    </div>
  )
}

export default function AdminDashboard({
  token,
  onUnauthorized,
  isSessionCurrent,
  onOpenAnalyze,
  onLogout,
}) {
  const [pageSize, setPageSize] = useState(PAGE_SIZES[0])
  const [offset, setOffset] = useState(0)
  const [labelFilter, setLabelFilter] = useState('ALL')
  const [modelFilter, setModelFilter] = useState('ALL')
  const [query, setQuery] = useState('')

  const context = { token, onUnauthorized, isSessionCurrent }
  const summary = useAdminData('/api/v1/admin/summary', context)
  const disputed = useAdminData(`/api/v1/admin/disputed?limit=${pageSize}&offset=${offset}`, context)

  const items = disputed.data?.items ?? []
  const total = disputed.data?.total ?? 0

  // Trang hiện tại trống dù vẫn còn dữ liệu (ví dụ dữ liệu vừa giảm): quay về trang đầu.
  useEffect(() => {
    if (disputed.status === 'ok' && items.length === 0 && total > 0 && offset > 0) setOffset(0)
  }, [disputed.status, items.length, total, offset])

  const modelOptions = useMemo(
    () => [...new Set(items.map((item) => item.model_version))].sort(),
    [items]
  )
  const activeModel = modelOptions.includes(modelFilter) ? modelFilter : 'ALL'
  const visible = useMemo(
    () => filterCases(items, { label: labelFilter, model: activeModel, query }),
    [items, labelFilter, activeModel, query]
  )
  const filtersActive = labelFilter !== 'ALL' || activeModel !== 'ALL' || query.trim() !== ''
  const loading = summary.status === 'loading' || disputed.status === 'loading'

  function clearFilters() {
    setLabelFilter('ALL')
    setModelFilter('ALL')
    setQuery('')
  }

  function reloadAll() {
    summary.reload()
    disputed.reload()
  }

  // Nút quay lại: dùng prop từ App.jsx, nếu thiếu thì tải lại trang /analyze.
  function goBack() {
    if (onOpenAnalyze) onOpenAnalyze()
    else window.location.assign('/analyze')
  }

  function logout() {
    if (onLogout) onLogout()
  }

  if (summary.status === 'forbidden' || disputed.status === 'forbidden') {
    return (
      <section className="panel" aria-label="Quản trị">
        <p className="eyebrow">QUẢN TRỊ</p>
        <div className="notice error" role="alert">
          Tài khoản này không có quyền ADMIN nên không xem được trang quản trị.
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <button type="button" className="secondary small" onClick={goBack}>
            ← Quay lại phân tích
          </button>
          <button type="button" className="secondary small" onClick={logout}>
            Đăng xuất
          </button>
        </div>
      </section>
    )
  }

  const from = total === 0 ? 0 : offset + 1
  const to = Math.min(offset + items.length, total)

  return (
    <section className="panel" aria-label="Quản trị: thống kê và ca bị phản hồi không đồng ý">
      <div className="auth-header">
        <div>
          <p className="eyebrow">QUẢN TRỊ</p>
          <h2 style={{ margin: 0 }}>Thống kê và ca bị phản hồi không đồng ý</h2>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button type="button" className="secondary small" onClick={goBack}>
            ← Quay lại phân tích
          </button>
          <button type="button" className="secondary small" disabled={loading} onClick={reloadAll}>
            {loading ? 'Đang tải...' : 'Làm mới'}
          </button>
          <button type="button" className="secondary small" onClick={logout}>
            Đăng xuất
          </button>
        </div>
      </div>

      <SummaryCards
        status={summary.status}
        data={summary.data}
        message={summary.message}
        onRetry={summary.reload}
      />

      <h3 className="section-title">
        Danh sách ca bị phản hồi không đồng ý{disputed.data ? ` (${formatNumber(total)})` : ''}
      </h3>
      <p className="muted small-text">
        Điểm là điểm lớp “fake” của mô hình, không phải xác suất bài báo sai sự thật. Phản hồi “không đồng ý”
        là ý kiến của người dùng, không phải nhãn thật/giả và không được dùng để huấn luyện lại mô hình.
      </p>

      <div className="filter-row">
        <div>
          <label htmlFor="admin-filter-label">Nhãn mô hình</label>
          <select id="admin-filter-label" value={labelFilter} onChange={(event) => setLabelFilter(event.target.value)}>
            {LABEL_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.text}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="admin-filter-model">Phiên bản mô hình</label>
          <select id="admin-filter-model" value={activeModel} onChange={(event) => setModelFilter(event.target.value)}>
            <option value="ALL">Tất cả phiên bản</option>
            {modelOptions.map((model) => (
              <option key={model} value={model}>{model}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="admin-filter-query">Tìm từ khóa</label>
          <input
            id="admin-filter-query"
            type="search"
            maxLength={200}
            placeholder="Trong đoạn trích hoặc lý do..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="admin-page-size">Số dòng mỗi trang</label>
          <select
            id="admin-page-size"
            value={pageSize}
            onChange={(event) => {
              setPageSize(Number(event.target.value))
              setOffset(0)
            }}
          >
            {PAGE_SIZES.map((size) => (
              <option key={size} value={size}>{size}</option>
            ))}
          </select>
        </div>
      </div>
      <p className="muted small-text" aria-live="polite">
        Bộ lọc nhãn, phiên bản và từ khóa chỉ áp dụng cho các dòng của trang đang xem
        {filtersActive && ` (${visible.length}/${items.length} dòng khớp)`}. API chưa hỗ trợ lọc phía máy chủ.{' '}
        {filtersActive && (
          <button type="button" className="link" onClick={clearFilters}>Xóa bộ lọc</button>
        )}
      </p>

      {disputed.status === 'error' && (
        <div className="notice error" role="alert">
          Không tải được danh sách. {disputed.message}{' '}
          <button type="button" className="small secondary" onClick={disputed.reload}>Thử lại</button>
        </div>
      )}

      {disputed.status === 'loading' && items.length === 0 ? (
        <p className="muted" role="status">Đang tải danh sách ca bị phản hồi không đồng ý...</p>
      ) : disputed.status === 'ok' && total === 0 ? (
        <p className="muted">Chưa có phản hồi “không đồng ý” nào.</p>
      ) : visible.length === 0 && items.length > 0 ? (
        <p className="muted">Không có dòng nào của trang này khớp bộ lọc.</p>
      ) : (
        <div aria-busy={disputed.status === 'loading'}>
          <CaseList items={visible} />
        </div>
      )}

      {total > pageSize && (
        <div className="pagination">
          <span>Hiển thị {from}–{to} / {formatNumber(total)}</span>
          <div className="auth-tabs">
            <button
              type="button"
              className="secondary small"
              disabled={disputed.status === 'loading' || offset === 0}
              onClick={() => setOffset(Math.max(0, offset - pageSize))}
            >
              ← Trang trước
            </button>
            <button
              type="button"
              className="secondary small"
              disabled={disputed.status === 'loading' || offset + pageSize >= total}
              onClick={() => setOffset(offset + pageSize)}
            >
              Trang sau →
            </button>
          </div>
        </div>
      )}
    </section>
  )
}
