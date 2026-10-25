import { useEffect, useRef, useState } from 'react'

const apiBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const TOKEN_KEY = 'sic_access_token'
const PAGE_LIMIT = 5

function FeedbackBox({ scope, analysisId, existingFeedback, token, onFeedbackSaved, onUnauthorized }) {
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  if (!analysisId) return null

  if (existingFeedback) {
    return (
      <div className="feedback-box">
        <span className={`badge ${existingFeedback.agree ? 'likely' : 'suspicious'}`} style={{ marginLeft: 0 }}>
          Phản hồi của bạn: {existingFeedback.agree ? 'Đồng ý với mô hình' : 'Không đồng ý'}
        </span>
        {existingFeedback.comment && (
          <p style={{ margin: '8px 0 0', fontSize: '13px', color: '#a9bec6' }}>
            Ghi chú: “{existingFeedback.comment}”
          </p>
        )}
      </div>
    )
  }

  async function handleSubmit(agree) {
    setSubmitting(true)
    setError('')
    const trimmed = comment.trim()
    const payload = { agree, ...(trimmed ? { comment: trimmed } : {}) }

    try {
      const response = await fetch(`${apiBase}/api/v1/analyses/${analysisId}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      if (response.status === 401) {
        onUnauthorized('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
        return
      }
      if (response.status === 404) throw new Error('Không tìm thấy lượt phân tích thuộc tài khoản của bạn.')
      if (response.status === 409) throw new Error('Lượt phân tích này đã được gửi phản hồi trước đó.')
      if (response.status === 422) throw new Error('Nhận xét không được vượt quá 1.000 ký tự.')
      if (!response.ok) throw new Error('Không thể gửi phản hồi.')

      const fbData = await response.json()
      setComment('')
      onFeedbackSaved(analysisId, fbData)
    } catch (cause) {
      setError(cause instanceof TypeError ? 'Lỗi kết nối API.' : cause.message)
    } finally {
      setSubmitting(false)
    }
  }

  const inputId = `comment-${scope}-${analysisId}`

  return (
    <div className="feedback-box">
      <label htmlFor={inputId}>Đánh giá kết quả phân tích này (tùy chọn ghi chú)</label>
      <input
        id={inputId}
        type="text"
        maxLength={1000}
        placeholder="Nhập lý do đồng ý hoặc phản đối (tối đa 1.000 ký tự)..."
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        disabled={submitting}
      />
      <div className="feedback-actions">
        <button type="button" className="small" disabled={submitting} onClick={() => handleSubmit(true)}>
          {submitting ? 'Đang gửi...' : '👍 Đồng ý'}
        </button>
        <button type="button" className="small secondary" disabled={submitting} onClick={() => handleSubmit(false)}>
          {submitting ? 'Đang gửi...' : '👎 Không đồng ý'}
        </button>
      </div>
      {error && <div className="notice error" style={{ marginTop: '10px', marginBottom: 0 }}>{error}</div>}
    </div>
  )
}

function AuthPanel({ user, onLoginSuccess, onLogout, authError, setAuthError }) {
  const [authMode, setAuthMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')

  if (user) {
    return (
      <section className="panel" aria-label="Tài khoản người dùng">
        <div className="user-bar">
          <div>
            <p className="eyebrow">TÀI KHOẢN ĐANG ĐĂNG NHẬP</p>
            <strong>{user.email}</strong>
            <span className="badge">{user.role}</span>
          </div>
          <button type="button" className="danger small" onClick={() => onLogout()}>
            Đăng xuất
          </button>
        </div>
      </section>
    )
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setAuthError('')
    setSuccessMsg('')

    try {
      if (authMode === 'register') {
        const regRes = await fetch(`${apiBase}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: email.trim(), password }),
        })
        if (regRes.status === 400) throw new Error('Email này đã được đăng ký.')
        if (regRes.status === 422) throw new Error('Email không hợp lệ hoặc mật khẩu không đúng chuẩn (6–72 ký tự).')
        if (!regRes.ok) throw new Error('Đăng ký thất bại. Vui lòng thử lại.')
        setSuccessMsg('Đăng ký thành công! Đang tự động đăng nhập...')
      }

      const loginRes = await fetch(`${apiBase}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      })
      if (loginRes.status === 401) throw new Error('Sai email hoặc mật khẩu.')
      if (loginRes.status === 422) throw new Error('Vui lòng nhập đúng định dạng email và mật khẩu.')
      if (!loginRes.ok) throw new Error('Đăng nhập thất bại. Vui lòng thử lại.')

      const loginData = await loginRes.json()
      setPassword('')
      setSuccessMsg('')
      onLoginSuccess(loginData.access_token)
    } catch (cause) {
      setAuthError(cause instanceof TypeError ? 'Không kết nối được API. Hãy khởi chạy backend.' : cause.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="panel" aria-label="Tài khoản người dùng">
      <div className="auth-header">
        <div>
          <p className="eyebrow">XÁC THỰC NGƯỜI DÙNG</p>
          <h2 style={{ margin: 0 }}>{authMode === 'login' ? 'Đăng nhập' : 'Đăng ký tài khoản mới'}</h2>
        </div>
        <div className="auth-tabs">
          <button
            type="button"
            className={`small ${authMode === 'login' ? '' : 'secondary'}`}
            onClick={() => { setAuthMode('login'); setAuthError(''); setSuccessMsg('') }}
          >
            Đăng nhập
          </button>
          <button
            type="button"
            className={`small ${authMode === 'register' ? '' : 'secondary'}`}
            onClick={() => { setAuthMode('register'); setAuthError(''); setSuccessMsg('') }}
          >
            Đăng ký
          </button>
        </div>
      </div>

      {authError && <div className="notice error" role="alert">{authError}</div>}
      {successMsg && <div className="notice success" role="status">{successMsg}</div>}

      <form className="auth-grid" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="auth-email">Email</label>
          <input
            id="auth-email"
            type="email"
            required
            placeholder="user@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
          />
        </div>
        <div>
          <label htmlFor="auth-password">Mật khẩu (tối thiểu 6 ký tự)</label>
          <input
            id="auth-password"
            type="password"
            required
            minLength={6}
            maxLength={72}
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Đang xử lý...' : authMode === 'login' ? 'Đăng nhập' : 'Tạo tài khoản'}
        </button>
      </form>
    </section>
  )
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '')
  const [user, setUser] = useState(null)
  const [authError, setAuthError] = useState('')

  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const [history, setHistory] = useState([])
  const [historyTotal, setHistoryTotal] = useState(0)
  const [historyOffset, setHistoryOffset] = useState(0)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState('')

  const activeTokenRef = useRef(token)
  activeTokenRef.current = token

  function clearSession(message = '') {
    localStorage.removeItem(TOKEN_KEY)
    activeTokenRef.current = ''
    setToken('')
    setUser(null)
    setHistory([])
    setHistoryTotal(0)
    setHistoryOffset(0)
    setResult(null)
    if (message) setAuthError(message)
  }

  function handleLoginSuccess(newToken) {
    setResult(null)
    setHistory([])
    setHistoryTotal(0)
    setHistoryOffset(0)
    localStorage.setItem(TOKEN_KEY, newToken)
    activeTokenRef.current = newToken
    setToken(newToken)
  }

  async function fetchHistory(requestToken = token, nextOffset = 0, signal) {
    if (!requestToken) return
    setHistoryLoading(true)
    setHistoryError('')
    try {
      const response = await fetch(
        `${apiBase}/api/v1/analyses?limit=${PAGE_LIMIT}&offset=${nextOffset}`,
        { headers: { Authorization: `Bearer ${requestToken}` }, signal }
      )
      if (activeTokenRef.current !== requestToken) return

      if (response.status === 401) {
        clearSession('Phiên đăng nhập không hợp lệ hoặc đã hết hạn.')
        return
      }
      if (!response.ok) throw new Error('Không thể tải lịch sử phân tích.')
      const data = await response.json()
      if (activeTokenRef.current !== requestToken) return

      setHistory(data.items || [])
      setHistoryTotal(data.total || 0)
      setHistoryOffset(data.offset || 0)
    } catch (cause) {
      if (cause.name === 'AbortError' || activeTokenRef.current !== requestToken) return
      setHistoryError(cause instanceof TypeError ? 'Không kết nối được API.' : cause.message)
    } finally {
      if (activeTokenRef.current === requestToken) {
        setHistoryLoading(false)
      }
    }
  }

  useEffect(() => {
    if (!token) {
      setUser(null)
      setHistory([])
      setHistoryTotal(0)
      return
    }

    const controller = new AbortController()
    const currentToken = token

    async function loadProfileAndHistory() {
      try {
        const meRes = await fetch(`${apiBase}/api/v1/auth/me`, {
          headers: { Authorization: `Bearer ${currentToken}` },
          signal: controller.signal,
        })
        if (activeTokenRef.current !== currentToken) return

        if (meRes.status === 401) {
          clearSession('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
          return
        }
        if (!meRes.ok) throw new Error('Không thể tải thông tin tài khoản.')
        const meData = await meRes.json()
        if (activeTokenRef.current !== currentToken) return

        setUser(meData)
        await fetchHistory(currentToken, 0, controller.signal)
      } catch (cause) {
        if (cause.name === 'AbortError' || activeTokenRef.current !== currentToken) return
        setAuthError(cause instanceof TypeError ? 'Không kết nối được API.' : cause.message)
      }
    }

    loadProfileAndHistory()
    return () => controller.abort()
  }, [token])

  async function analyze(event) {
    event.preventDefault()
    setLoading(true)
    setResult(null)
    setError('')
    const requestToken = token
    try {
      const headers = { 'Content-Type': 'application/json' }
      if (requestToken) headers.Authorization = `Bearer ${requestToken}`

      const response = await fetch(`${apiBase}/api/v1/analyze`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ text }),
      })
      if (response.status === 401) {
        clearSession('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
        throw new Error('Phiên đăng nhập không hợp lệ hoặc đã hết hạn (401).')
      }
      if (response.status === 503) throw new Error('Chưa có mô hình. Hãy huấn luyện baseline và cấu hình MODEL_PATH theo README.')
      if (response.status === 422) throw new Error('Vui lòng nhập bài báo tiếng Anh từ 80 đến 50.000 ký tự.')
      if (!response.ok) throw new Error('Không thể phân tích. Hãy kiểm tra API và thử lại.')

      const data = await response.json()
      if (activeTokenRef.current !== requestToken) return

      setResult({ ...data, feedback: null })
      if (requestToken && data.id) {
        await fetchHistory(requestToken, 0)
      }
    } catch (cause) {
      setError(cause instanceof TypeError ? 'Không kết nối được API. Hãy khởi chạy backend.' : cause.message)
    } finally {
      setLoading(false)
    }
  }

  function handleFeedbackSaved(analysisId, fbData) {
    setResult((prev) => (prev && prev.id === analysisId ? { ...prev, feedback: fbData } : prev))
    setHistory((prev) => prev.map((item) => (item.id === analysisId ? { ...item, feedback: fbData } : item)))
  }

  return (
    <main className="shell">
      <header className="header">
        <span className="brand">SIC / FAKE NEWS LENS</span>
        <span className="tag">Đồ án nhóm · v0</span>
      </header>

      <section className="hero">
        <p className="eyebrow">XỬ LÝ NGÔN NGỮ TỰ NHIÊN</p>
        <h1>Sàng lọc dấu hiệu đáng ngờ trong bài báo.</h1>
        <p className="lead">
          Dán nội dung bài báo tiếng Anh để xem điểm dự đoán của mô hình. Kết quả chỉ hỗ trợ lựa chọn thông tin cần kiểm tra thêm.
        </p>
      </section>

      <AuthPanel
        user={user}
        onLoginSuccess={handleLoginSuccess}
        onLogout={() => clearSession()}
        authError={authError}
        setAuthError={setAuthError}
      />

      <form className="panel" onSubmit={analyze}>
        <label htmlFor="article">Nội dung bài báo</label>
        <textarea
          id="article"
          value={text}
          onChange={(event) => setText(event.target.value)}
          minLength={80}
          maxLength={50000}
          required
          placeholder="Paste an English news article here..."
        />
        <div className="form-footer">
          <span>
            {text.length.toLocaleString('vi-VN')} / 50.000 ký tự
            {!user && ' · (Chưa đăng nhập: kết quả không lưu vào lịch sử)'}
          </span>
          <button disabled={loading || text.length < 80}>
            {loading ? 'Đang phân tích...' : 'Phân tích văn bản'}
          </button>
        </div>
      </form>

      {error && <div className="notice error" role="alert">{error}</div>}

      {result && (
        <section className="panel result" aria-live="polite">
          <p className="eyebrow">KẾT QUẢ MÔ HÌNH · {result.model_version}</p>
          <h2>{result.label === 'SUSPICIOUS' ? 'Cần kiểm tra thêm' : 'Ít dấu hiệu đáng ngờ hơn'}</h2>
          <p className="score">
            {Math.round(result.score * 100)}% <small>điểm lớp “fake” trên bộ dữ liệu huấn luyện</small>
          </p>
          <p>
            Điểm này không phải xác suất bài báo sai sự thật. Hãy đối chiếu tác giả, nguồn, thời điểm và bằng chứng độc lập.
          </p>
          {user && result.id && (
            <FeedbackBox
              scope="result"
              analysisId={result.id}
              existingFeedback={result.feedback}
              token={token}
              onFeedbackSaved={handleFeedbackSaved}
              onUnauthorized={clearSession}
            />
          )}
        </section>
      )}

      {user && (
        <section className="panel" aria-label="Lịch sử phân tích cá nhân">
          <div className="auth-header">
            <div>
              <p className="eyebrow">DỮ LIỆU CÁ NHÂN ({user.email})</p>
              <h2 style={{ margin: 0 }}>Lịch sử phân tích ({historyTotal})</h2>
            </div>
            <button
              type="button"
              className="secondary small"
              disabled={historyLoading}
              onClick={() => fetchHistory(token, historyOffset)}
            >
              {historyLoading ? 'Đang tải...' : 'Làm mới'}
            </button>
          </div>

          {historyError && <div className="notice error" role="alert">{historyError}</div>}

          {historyLoading && history.length === 0 ? (
            <p style={{ color: '#9fb4bd' }}>Đang tải lịch sử phân tích...</p>
          ) : history.length === 0 ? (
            <p style={{ color: '#9fb4bd' }}>
              Tài khoản của bạn chưa có lượt phân tích nào.
            </p>
          ) : (
            <div className="history-list">
              {history.map((item) => (
                <article key={item.id} className="history-item">
                  <div className="history-meta">
                    <span>
                      <strong>#{item.id}</strong> · {new Date(item.created_at).toLocaleString('vi-VN')} ·{' '}
                      <code>{item.model_version}</code>
                    </span>
                    <span className={`badge ${item.label === 'SUSPICIOUS' ? 'suspicious' : 'likely'}`}>
                      {item.label} ({Math.round(item.score * 100)}%)
                    </span>
                  </div>
                  <p className="history-preview">“{item.content_preview}”</p>
                  <FeedbackBox
                    scope="history"
                    analysisId={item.id}
                    existingFeedback={item.feedback}
                    token={token}
                    onFeedbackSaved={handleFeedbackSaved}
                    onUnauthorized={clearSession}
                  />
                </article>
              ))}
            </div>
          )}

          {historyTotal > PAGE_LIMIT && (
            <div className="pagination">
              <span>
                Hiển thị {historyOffset + 1}–{Math.min(historyOffset + history.length, historyTotal)} / {historyTotal}
              </span>
              <div className="auth-tabs">
                <button
                  type="button"
                  className="secondary small"
                  disabled={historyLoading || historyOffset === 0}
                  onClick={() => fetchHistory(token, Math.max(0, historyOffset - PAGE_LIMIT))}
                >
                  ← Trang trước
                </button>
                <button
                  type="button"
                  className="secondary small"
                  disabled={historyLoading || historyOffset + PAGE_LIMIT >= historyTotal}
                  onClick={() => fetchHistory(token, historyOffset + PAGE_LIMIT)}
                >
                  Trang sau →
                </button>
              </div>
            </div>
          )}
        </section>
      )}

      <footer>
        Phạm vi v0: bài báo tiếng Anh · Đã hỗ trợ tài khoản, lịch sử và phản hồi; chưa hỗ trợ URL và LIME · Không dùng để đưa ra kết luận tự động
      </footer>
    </main>
  )
}