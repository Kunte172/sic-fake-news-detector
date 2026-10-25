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
          Pháº£n há»“i cá»§a báº¡n: {existingFeedback.agree ? 'Äá»“ng Ã½ vá»›i mÃ´ hÃ¬nh' : 'KhÃ´ng Ä‘á»“ng Ã½'}
        </span>
        {existingFeedback.comment && (
          <p style={{ margin: '8px 0 0', fontSize: '13px', color: '#a9bec6' }}>
            Ghi chÃº: â€œ{existingFeedback.comment}â€
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
        onUnauthorized('PhiÃªn Ä‘Äƒng nháº­p Ä‘Ã£ háº¿t háº¡n. Vui lÃ²ng Ä‘Äƒng nháº­p láº¡i.')
        return
      }
      if (response.status === 404) throw new Error('KhÃ´ng tÃ¬m tháº¥y lÆ°á»£t phÃ¢n tÃ­ch thuá»™c tÃ i khoáº£n cá»§a báº¡n.')
      if (response.status === 409) throw new Error('LÆ°á»£t phÃ¢n tÃ­ch nÃ y Ä‘Ã£ Ä‘Æ°á»£c gá»­i pháº£n há»“i trÆ°á»›c Ä‘Ã³.')
      if (response.status === 422) throw new Error('Nháº­n xÃ©t khÃ´ng Ä‘Æ°á»£c vÆ°á»£t quÃ¡ 1.000 kÃ½ tá»±.')
      if (!response.ok) throw new Error('KhÃ´ng thá»ƒ gá»­i pháº£n há»“i.')

      const fbData = await response.json()
      setComment('')
      onFeedbackSaved(analysisId, fbData)
    } catch (cause) {
      setError(cause instanceof TypeError ? 'Lá»—i káº¿t ná»‘i API.' : cause.message)
    } finally {
      setSubmitting(false)
    }
  }

  const inputId = `comment-${scope}-${analysisId}`

  return (
    <div className="feedback-box">
      <label htmlFor={inputId}>ÄÃ¡nh giÃ¡ káº¿t quáº£ phÃ¢n tÃ­ch nÃ y (tÃ¹y chá»n ghi chÃº)</label>
      <input
        id={inputId}
        type="text"
        maxLength={1000}
        placeholder="Nháº­p lÃ½ do Ä‘á»“ng Ã½ hoáº·c pháº£n Ä‘á»‘i (tá»‘i Ä‘a 1.000 kÃ½ tá»±)..."
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        disabled={submitting}
      />
      <div className="feedback-actions">
        <button type="button" className="small" disabled={submitting} onClick={() => handleSubmit(true)}>
          {submitting ? 'Äang gá»­i...' : 'ðŸ‘ Äá»“ng Ã½'}
        </button>
        <button type="button" className="small secondary" disabled={submitting} onClick={() => handleSubmit(false)}>
          {submitting ? 'Äang gá»­i...' : 'ðŸ‘Ž KhÃ´ng Ä‘á»“ng Ã½'}
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
      <section className="panel" aria-label="TÃ i khoáº£n ngÆ°á»i dÃ¹ng">
        <div className="user-bar">
          <div>
            <p className="eyebrow">TÃ€I KHOáº¢N ÄANG ÄÄ‚NG NHáº¬P</p>
            <strong>{user.email}</strong>
            <span className="badge">{user.role}</span>
          </div>
          <button type="button" className="danger small" onClick={() => onLogout()}>
            ÄÄƒng xuáº¥t
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
        if (regRes.status === 400) throw new Error('Email nÃ y Ä‘Ã£ Ä‘Æ°á»£c Ä‘Äƒng kÃ½.')
        if (regRes.status === 422) throw new Error('Email khÃ´ng há»£p lá»‡ hoáº·c máº­t kháº©u khÃ´ng Ä‘Ãºng chuáº©n (6â€“72 kÃ½ tá»±).')
        if (!regRes.ok) throw new Error('ÄÄƒng kÃ½ tháº¥t báº¡i. Vui lÃ²ng thá»­ láº¡i.')
        setSuccessMsg('ÄÄƒng kÃ½ thÃ nh cÃ´ng! Äang tá»± Ä‘á»™ng Ä‘Äƒng nháº­p...')
      }

      const loginRes = await fetch(`${apiBase}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      })
      if (loginRes.status === 401) throw new Error('Sai email hoáº·c máº­t kháº©u.')
      if (loginRes.status === 422) throw new Error('Vui lÃ²ng nháº­p Ä‘Ãºng Ä‘á»‹nh dáº¡ng email vÃ  máº­t kháº©u.')
      if (!loginRes.ok) throw new Error('ÄÄƒng nháº­p tháº¥t báº¡i. Vui lÃ²ng thá»­ láº¡i.')

      const loginData = await loginRes.json()
      setPassword('')
      setSuccessMsg('')
      onLoginSuccess(loginData.access_token)
    } catch (cause) {
      setAuthError(cause instanceof TypeError ? 'KhÃ´ng káº¿t ná»‘i Ä‘Æ°á»£c API. HÃ£y khá»Ÿi cháº¡y backend.' : cause.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="panel" aria-label="TÃ i khoáº£n ngÆ°á»i dÃ¹ng">
      <div className="auth-header">
        <div>
          <p className="eyebrow">XÃC THá»°C NGÆ¯á»œI DÃ™NG</p>
          <h2 style={{ margin: 0 }}>{authMode === 'login' ? 'ÄÄƒng nháº­p' : 'ÄÄƒng kÃ½ tÃ i khoáº£n má»›i'}</h2>
        </div>
        <div className="auth-tabs">
          <button
            type="button"
            className={`small ${authMode === 'login' ? '' : 'secondary'}`}
            onClick={() => { setAuthMode('login'); setAuthError(''); setSuccessMsg('') }}
          >
            ÄÄƒng nháº­p
          </button>
          <button
            type="button"
            className={`small ${authMode === 'register' ? '' : 'secondary'}`}
            onClick={() => { setAuthMode('register'); setAuthError(''); setSuccessMsg('') }}
          >
            ÄÄƒng kÃ½
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
          <label htmlFor="auth-password">Máº­t kháº©u (tá»‘i thiá»ƒu 6 kÃ½ tá»±)</label>
          <input
            id="auth-password"
            type="password"
            required
            minLength={6}
            maxLength={72}
            placeholder="â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Äang xá»­ lÃ½...' : authMode === 'login' ? 'ÄÄƒng nháº­p' : 'Táº¡o tÃ i khoáº£n'}
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
      // Náº¿u trong lÃºc Ä‘á»£i máº¡ng, ngÆ°á»i dÃ¹ng Ä‘Ã£ Ä‘Äƒng xuáº¥t hoáº·c Ä‘á»•i sang token khÃ¡c -> bá» qua káº¿t quáº£ cÅ©
      if (activeTokenRef.current !== requestToken) return

      if (response.status === 401) {
        clearSession('PhiÃªn Ä‘Äƒng nháº­p khÃ´ng há»£p lá»‡ hoáº·c Ä‘Ã£ háº¿t háº¡n.')
        return
      }
      if (!response.ok) throw new Error('KhÃ´ng thá»ƒ táº£i lá»‹ch sá»­ phÃ¢n tÃ­ch.')
      const data = await response.json()
      if (activeTokenRef.current !== requestToken) return

      setHistory(data.items || [])
      setHistoryTotal(data.total || 0)
      setHistoryOffset(data.offset || 0)
    } catch (cause) {
      if (cause.name === 'AbortError' || activeTokenRef.current !== requestToken) return
      setHistoryError(cause instanceof TypeError ? 'KhÃ´ng káº¿t ná»‘i Ä‘Æ°á»£c API.' : cause.message)
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
          clearSession('PhiÃªn Ä‘Äƒng nháº­p Ä‘Ã£ háº¿t háº¡n. Vui lÃ²ng Ä‘Äƒng nháº­p láº¡i.')
          return
        }
        if (!meRes.ok) throw new Error('KhÃ´ng thá»ƒ táº£i thÃ´ng tin tÃ i khoáº£n.')
        const meData = await meRes.json()
        if (activeTokenRef.current !== currentToken) return

        setUser(meData)
        await fetchHistory(currentToken, 0, controller.signal)
      } catch (cause) {
        if (cause.name === 'AbortError' || activeTokenRef.current !== currentToken) return
        setAuthError(cause instanceof TypeError ? 'KhÃ´ng káº¿t ná»‘i Ä‘Æ°á»£c API.' : cause.message)
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
        clearSession('PhiÃªn Ä‘Äƒng nháº­p Ä‘Ã£ háº¿t háº¡n. Vui lÃ²ng Ä‘Äƒng nháº­p láº¡i.')
        throw new Error('PhiÃªn Ä‘Äƒng nháº­p khÃ´ng há»£p lá»‡ hoáº·c Ä‘Ã£ háº¿t háº¡n (401).')
      }
      if (response.status === 503) throw new Error('ChÆ°a cÃ³ mÃ´ hÃ¬nh. HÃ£y huáº¥n luyá»‡n baseline vÃ  cáº¥u hÃ¬nh MODEL_PATH theo README.')
      if (response.status === 422) throw new Error('Vui lÃ²ng nháº­p bÃ i bÃ¡o tiáº¿ng Anh tá»« 80 Ä‘áº¿n 50.000 kÃ½ tá»±.')
      if (!response.ok) throw new Error('KhÃ´ng thá»ƒ phÃ¢n tÃ­ch. HÃ£y kiá»ƒm tra API vÃ  thá»­ láº¡i.')

      const data = await response.json()
      if (activeTokenRef.current !== requestToken) return

      setResult({ ...data, feedback: null })
      if (requestToken && data.id) {
        await fetchHistory(requestToken, 0)
      }
    } catch (cause) {
      setError(cause instanceof TypeError ? 'KhÃ´ng káº¿t ná»‘i Ä‘Æ°á»£c API. HÃ£y khá»Ÿi cháº¡y backend.' : cause.message)
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
        <span className="tag">Äá»“ Ã¡n nhÃ³m Â· v0</span>
      </header>

      <section className="hero">
        <p className="eyebrow">Xá»¬ LÃ NGÃ”N NGá»® Tá»° NHIÃŠN</p>
        <h1>SÃ ng lá»c dáº¥u hiá»‡u Ä‘Ã¡ng ngá» trong bÃ i bÃ¡o.</h1>
        <p className="lead">
          DÃ¡n ná»™i dung bÃ i bÃ¡o tiáº¿ng Anh Ä‘á»ƒ xem Ä‘iá»ƒm dá»± Ä‘oÃ¡n cá»§a mÃ´ hÃ¬nh. Káº¿t quáº£ chá»‰ há»— trá»£ lá»±a chá»n thÃ´ng tin cáº§n kiá»ƒm tra thÃªm.
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
        <label htmlFor="article">Ná»™i dung bÃ i bÃ¡o</label>
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
            {text.length.toLocaleString('vi-VN')} / 50.000 kÃ½ tá»±
            {!user && ' Â· (ChÆ°a Ä‘Äƒng nháº­p: káº¿t quáº£ khÃ´ng lÆ°u vÃ o lá»‹ch sá»­)'}
          </span>
          <button disabled={loading || text.length < 80}>
            {loading ? 'Äang phÃ¢n tÃ­ch...' : 'PhÃ¢n tÃ­ch vÄƒn báº£n'}
          </button>
        </div>
      </form>

      {error && <div className="notice error" role="alert">{error}</div>}

      {result && (
        <section className="panel result" aria-live="polite">
          <p className="eyebrow">Káº¾T QUáº¢ MÃ” HÃŒNH Â· {result.model_version}</p>
          <h2>{result.label === 'SUSPICIOUS' ? 'Cáº§n kiá»ƒm tra thÃªm' : 'Ãt dáº¥u hiá»‡u Ä‘Ã¡ng ngá» hÆ¡n'}</h2>
          <p className="score">
            {Math.round(result.score * 100)}% <small>Ä‘iá»ƒm lá»›p â€œfakeâ€ trÃªn bá»™ dá»¯ liá»‡u huáº¥n luyá»‡n</small>
          </p>
          <p>
            Äiá»ƒm nÃ y khÃ´ng pháº£i xÃ¡c suáº¥t bÃ i bÃ¡o sai sá»± tháº­t. HÃ£y Ä‘á»‘i chiáº¿u tÃ¡c giáº£, nguá»“n, thá»i Ä‘iá»ƒm vÃ  báº±ng chá»©ng Ä‘á»™c láº­p.
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
        <section className="panel" aria-label="Lá»‹ch sá»­ phÃ¢n tÃ­ch cÃ¡ nhÃ¢n">
          <div className="auth-header">
            <div>
              <p className="eyebrow">Dá»® LIá»†U CÃ NHÃ‚N ({user.email})</p>
              <h2 style={{ margin: 0 }}>Lá»‹ch sá»­ phÃ¢n tÃ­ch ({historyTotal})</h2>
            </div>
            <button
              type="button"
              className="secondary small"
              disabled={historyLoading}
              onClick={() => fetchHistory(token, historyOffset)}
            >
              {historyLoading ? 'Äang táº£i...' : 'LÃ m má»›i'}
            </button>
          </div>

          {historyError && <div className="notice error" role="alert">{historyError}</div>}

          {historyLoading && history.length === 0 ? (
            <p style={{ color: '#9fb4bd' }}>Äang táº£i lá»‹ch sá»­ phÃ¢n tÃ­ch...</p>
          ) : history.length === 0 ? (
            <p style={{ color: '#9fb4bd' }}>
              TÃ i khoáº£n cá»§a báº¡n chÆ°a cÃ³ lÆ°á»£t phÃ¢n tÃ­ch nÃ o.
            </p>
          ) : (
            <div className="history-list">
              {history.map((item) => (
                <article key={item.id} className="history-item">
                  <div className="history-meta">
                    <span>
                      <strong>#{item.id}</strong> Â· {new Date(item.created_at).toLocaleString('vi-VN')} Â·{' '}
                      <code>{item.model_version}</code>
                    </span>
                    <span className={`badge ${item.label === 'SUSPICIOUS' ? 'suspicious' : 'likely'}`}>
                      {item.label} ({Math.round(item.score * 100)}%)
                    </span>
                  </div>
                  <p className="history-preview">â€œ{item.content_preview}â€</p>
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
                Hiá»ƒn thá»‹ {historyOffset + 1}â€“{Math.min(historyOffset + history.length, historyTotal)} / {historyTotal}
              </span>
              <div className="auth-tabs">
                <button
                  type="button"
                  className="secondary small"
                  disabled={historyLoading || historyOffset === 0}
                  onClick={() => fetchHistory(token, Math.max(0, historyOffset - PAGE_LIMIT))}
                >
                  â† Trang trÆ°á»›c
                </button>
                <button
                  type="button"
                  className="secondary small"
                  disabled={historyLoading || historyOffset + PAGE_LIMIT >= historyTotal}
                  onClick={() => fetchHistory(token, historyOffset + PAGE_LIMIT)}
                >
                  Trang sau â†’
                </button>
              </div>
            </div>
          )}
        </section>
      )}

      <footer>
        Pháº¡m vi v0: bÃ i bÃ¡o tiáº¿ng Anh Â· ÄÃ£ há»— trá»£ tÃ i khoáº£n, lá»‹ch sá»­ vÃ  pháº£n há»“i; chÆ°a há»— trá»£ URL vÃ  LIME Â· KhÃ´ng dÃ¹ng Ä‘á»ƒ Ä‘Æ°a ra káº¿t luáº­n tá»± Ä‘á»™ng
      </footer>
    </main>
  )
}
