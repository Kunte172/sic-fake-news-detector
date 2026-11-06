import { useEffect, useRef, useState } from 'react'
import AdminDashboard, { ViewTabs } from './AdminDashboard.jsx'

const TOKEN_KEY = 'sic_access_token'
const GUEST_KEY = 'sic_guest_mode'

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(GUEST_KEY) === '1' ? '' : localStorage.getItem(TOKEN_KEY) || '')
  const [user, setUser] = useState(null)
  const [authError, setAuthError] = useState('')
  const [view, setView] = useState('analyze')

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
  const theme = useTheme()
  const language = useLanguage()

  function clearSession(message = '') {
    activeTokenRef.current = ''
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(GUEST_KEY)
    setSessionMessage(message)
    setUser(null)
    setHistory([])
    setHistoryTotal(0)
    setHistoryOffset(0)
    setResult(null)
    setView('analyze')
    if (message) setAuthError(message)
  }

  function startSession(nextToken) {
    activeTokenRef.current = nextToken
    localStorage.setItem(TOKEN_KEY, nextToken)
    localStorage.removeItem(GUEST_KEY)
    setSessionMessage('')
    setGuest(false)
    setScreen('analyze')
    setToken(nextToken)
  }

  function startGuest() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.setItem(GUEST_KEY, '1')
    setSessionMessage('')
    setUser(null)
    setProfileError('')
    activeTokenRef.current = ''
    setToken('')
    setGuest(true)
    window.history.replaceState(null, '', '/analyze')
  }

  useEffect(() => {
    if (!token || guest) return
    activeTokenRef.current = token
    const controller = new AbortController()
    let timedOut = false
    const timeout = window.setTimeout(() => {
      timedOut = true
      controller.abort()
    }, 8000)
    api('/auth/me', { token, signal: controller.signal }).then((profile) => {
      if (!controller.signal.aborted && activeTokenRef.current === token) setUser(profile)
    }).catch((error) => {
      if (activeTokenRef.current !== token) return
      if (timedOut) {
        setProfileError('Không thể kiểm tra phiên đăng nhập. Vui lòng thử lại.')
        return
      }
      if (controller.signal.aborted) return
      if (error.status === 401) clearSession('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
      else setProfileError('Chưa tải được thông tin tài khoản. Vui lòng thử lại.')
    }).finally(() => {
      window.clearTimeout(timeout)
    })
    return () => {
      window.clearTimeout(timeout)
      controller.abort()
    }
  }, [token, guest, attempt])

  // Hai trang có đích đến cố định theo phiên đã xác thực.
  const destination = (user && token) || guest ? '/analyze' : token ? null : '/auth'
  useEffect(() => {
    function syncRoute() {
      if (destination && location.pathname !== destination) history.replaceState(null, '', destination)
    }
    syncRoute()
    window.addEventListener('popstate', syncRoute)
    return () => window.removeEventListener('popstate', syncRoute)
  }, [destination])

  if (!token && !guest) return <AuthPage onLogin={startSession} onGuest={startGuest} sessionMessage={sessionMessage} theme={theme} language={language} />
  if (guest) return <AnalyzePage key="guest" user={null} token="" theme={theme} language={language} onLogout={clearSession} onOpenAdmin={() => setScreen('admin')} />
  if (!user) return <main className="session-screen">
    <div className="card session-card">
      <Brand />
      <p role="status">{profileError || 'Đang kiểm tra phiên đăng nhập…'}</p>
      {profileError && <div className="actions">
        <button className="primary" onClick={() => { setProfileError(''); setAttempt(attempt + 1) }}>Thử lại</button>
        <button className="secondary" onClick={() => clearSession()}>Về trang đăng nhập</button>
      </div>}
    </div>
  </main>
  if (screen === 'admin' && user.role === 'ADMIN') {
    return <AdminDashboard token={token} theme={theme} language={language} onLogout={clearSession} onOpenAnalyze={() => setScreen('analyze')} />
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
          {result.explanation && (
            <div className="explanation">
              <h3>Lý do mô hình dự đoán</h3>
              <p>{result.explanation.disclaimer}</p>
              <p>Đóng góp vào margin tuyến tính, không phải phần trăm hay bằng chứng sự thật. Dương: về Fake; âm: về Real.</p>
              <ul>{result.explanation.terms.map((item) => (
                <li key={item.term}><strong>{item.term}</strong>: {item.value.toFixed(4)}</li>
              ))}</ul>
              <small>Margin Fake: {result.explanation.fake_margin.toFixed(4)} · hệ số chặn: {result.explanation.intercept.toFixed(4)} · phần còn lại: {result.explanation.other_contribution.toFixed(4)}</small>
              {result.explanation.lime && (
                <div>
                  <h4>LIME (xấp xỉ cục bộ)</h4>
                  <p>Fidelity: {String(result.explanation.lime.fidelity)}. {result.explanation.lime.fidelity == null || result.explanation.lime.fidelity < 0.5 ? 'Giải thích có độ tin cậy thấp; không nên dựa vào các từ này để kết luận.' : 'Đây vẫn là xấp xỉ hành vi mô hình.'}</p>
                  <ul>{result.explanation.lime.terms.map((item) => <li key={item.term}>{item.term}: {item.weight.toFixed(4)}</li>)}</ul>
                </div>
              )}
            </div>
          )}
          {user && result.id && (
            <FeedbackBox
              scope="result"
              analysisId={result.id}
              existingFeedback={result.feedback}
              token={token}
              onFeedbackSaved={handleFeedbackSaved}
              onUnauthorized={clearSession}
              isSessionCurrent={() => activeTokenRef.current === token}
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
              isSessionCurrent={() => activeTokenRef.current === token}
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
