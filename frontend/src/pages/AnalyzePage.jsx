import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import Feedback from '../components/Feedback'
import HistoryPanel from '../components/HistoryPanel'
import ResultCard from '../components/ResultCard'
import Support from '../components/Support'
import Settings from '../components/Settings'
import LearnMore from '../components/LearnMore'
import About from '../components/About'
import { Brand, Icon, LanguageButton, ThemeButton } from '../components/Theme'

const PAGE_LIMIT = 5

export default function AnalyzePage({ user, token, theme, language, onLogout, onOpenAdmin }) {
  const en = language.language === 'en'
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [inputMode, setInputMode] = useState('text')
  const [modeOpen, setModeOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [historyOpen, setHistoryOpen] = useState(false)
  const [history, setHistory] = useState({ items: [], total: 0, offset: 0, busy: true, error: '' })
  const historyRequest = useRef(null)
  const analysisRequest = useRef(null)
  const activeTokenRef = useRef(token)
  const feedbackById = useRef(new Map())
  const article = useRef(null)
  const length = text.trim().length
  const wordCount = length ? text.trim().split(/\s+/u).length : 0
  const validUrl = text.trim().length <= 2048 && /^https?:\/\/\S+$/i.test(text.trim())
  const valid = inputMode === 'link' ? validUrl : length >= 80 && text.length <= 50000
  const suspiciousCount = history.items.filter((item) => item.label === 'SUSPICIOUS').length
  const safeCount = history.items.filter((item) => item.label === 'LESS_SUSPICIOUS').length
  const suspiciousRate = history.items.length ? Math.round((suspiciousCount / history.items.length) * 100) : 0
  const expire = () => onLogout('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')

  async function loadHistory(offset = 0) {
    if (!token) return
    activeTokenRef.current = token
    historyRequest.current?.abort()
    const controller = new AbortController()
    historyRequest.current = controller
    setHistory((current) => ({ ...current, busy: true, error: '' }))
    try {
      const data = await api('/analyses?limit=' + PAGE_LIMIT + '&offset=' + offset, { token, signal: controller.signal })
      if (controller.signal.aborted || activeTokenRef.current !== token) return
      const items = (data.items || []).map((item) => ({
        ...item, feedback: feedbackById.current.get(item.id) ?? item.feedback,
      }))
      setHistory({ items, total: data.total || 0, offset: data.offset || 0, busy: false, error: '' })
    } catch (cause) {
      if (controller.signal.aborted || activeTokenRef.current !== token) return
      if (cause.status === 401) expire()
      else setHistory((current) => ({ ...current, busy: false, error: 'Chưa tải được lịch sử phân tích.' }))
    }
  }

  useEffect(() => {
    activeTokenRef.current = token
    if (token) loadHistory()
    return () => {
      historyRequest.current?.abort()
      analysisRequest.current?.abort()
    }
  }, [token])

  function replaceText(value) {
    setText(value)
    setResult(null)
    setError('')
  }

  async function analyze(event) {
    event.preventDefault()
    if (!valid || analysisRequest.current) return
    const controller = new AbortController()
    analysisRequest.current = controller
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await api('/analyze', {
        token,
        body: inputMode === 'link' ? { url: text.trim() } : { text },
        signal: controller.signal,
      })
      if (controller.signal.aborted || activeTokenRef.current !== token) return
      setResult({ ...data, feedback: null })
      if (data.id) loadHistory()
    } catch (cause) {
      if (controller.signal.aborted || activeTokenRef.current !== token) return
      if (cause.status === 401) expire()
      else if (cause.status === 503) setError('Mô hình chưa sẵn sàng. Vui lòng thử lại sau hoặc báo cho nhóm phụ trách.')
      else if (cause.status === 422) setError(inputMode === 'link'
        ? 'URL không hợp lệ hoặc không trích xuất được bài báo.'
        : 'Hãy nhập ít nhất 80 ký tự tiếng Anh, tối đa 50.000 ký tự.')
      else if (cause.status === 413) setError('Bài báo vượt quá giới hạn kích thước cho phép.')
      else if (cause.status === 502 || cause.status === 504) setError('Không thể tải bài báo từ URL này. Hãy thử URL khác hoặc dán văn bản.')
      else setError('Chưa nhận được kết quả từ máy chủ. Vui lòng thử lại.')
    } finally {
      analysisRequest.current = null
      if (!controller.signal.aborted) setLoading(false)
    }
  }

  function feedbackSaved(id, feedback) {
    feedbackById.current.set(id, feedback)
    setResult((current) => current?.id === id ? { ...current, feedback } : current)
    setHistory((current) => ({ ...current, items: current.items.map((item) => item.id === id ? { ...item, feedback } : item) }))
  }

  function chooseMode(nextMode) {
    setInputMode(nextMode)
    setModeOpen(false)
    replaceText('')
  }

  function openHistory() {
    if (historyOpen) {
      setHistoryOpen(false)
      return
    }
    setHistoryOpen(true)
    window.requestAnimationFrame(() => document.getElementById('history-title')?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
  }

  return <>
    <a href="#workspace" className="skip-link">Đến nội dung chính</a>
    <header className="topbar"><div className="topbar-inner">
      <Brand />
      <div className="account">
        <LanguageButton {...language} /><ThemeButton {...theme} />
        {user ? <><Settings user={user} language={language} onLogout={onLogout} />
          {user.role === 'ADMIN' && <button type="button" className="secondary small" onClick={onOpenAdmin}>Quản trị</button>}
          <span className="avatar" aria-hidden="true">{user.email?.[0]?.toUpperCase() || 'S'}</span>
          <span className="account-email" title={user.email}>{user.email}</span>
          <button type="button" className="secondary small" onClick={() => onLogout()}>{en ? 'Sign out' : 'Đăng xuất'}</button></>
          : <button type="button" className="secondary small" onClick={() => onLogout()}>{en ? 'Sign in' : 'Đăng nhập'}</button>}
      </div>
    </div></header>
    <main className="workspace" id="workspace" tabIndex={-1}>
      <section className="hero">
        <div className="hero-illustration" aria-hidden="true">
          <div className="cyber-orbit cyber-orbit-one" />
          <div className="cyber-orbit cyber-orbit-two" />
          <div className="cyber-paper">
            <span className="cyber-paper-head" />
            <span className="cyber-paper-title" />
            <span className="cyber-paper-line" />
            <span className="cyber-paper-line short" />
            <span className="cyber-paper-line" />
            <span className="cyber-alert">!</span>
          </div>
          <span className="cyber-beam" />
          <div className="cyber-magnifier">
            <span className="cyber-lens"><i /></span>
            <span className="cyber-handle" />
          </div>
        </div>
        <p className="eyebrow">{en ? 'CONTENT CHECK' : 'KIỂM CHỨNG NỘI DUNG'}</p>
        <h1>{en ? 'Analyze an article' : 'Phân tích bài báo'}</h1>
        <p className="muted">{en ? 'Quickly assess suspicious signals in an article with machine learning.' : 'Đánh giá nhanh dấu hiệu đáng ngờ trong bài viết bằng mô hình học máy.'}</p>
      </section>
      <div className="analyze-grid">
        <form className="card editor-card" onSubmit={analyze}>
          <div className="editor-heading">
            <div className="card-title"><span className="tile"><Icon name={inputMode === 'link' ? 'link' : 'file'} /></span>
              <div><h2>{inputMode === 'link' ? (en ? 'Article URL' : 'Đường dẫn bài báo') : (en ? 'Article text' : 'Nội dung bài báo')}</h2><p className="muted">{inputMode === 'link' ? (en ? 'Paste the article URL to check' : 'Dán đường dẫn bài báo cần kiểm tra') : (en ? 'English text · Up to 50,000 characters' : 'Văn bản tiếng Anh · Tối đa 50.000 ký tự')}</p></div>
            </div>
            <div className="input-mode">
              <button type="button" className="mode-trigger" aria-haspopup="listbox" aria-expanded={modeOpen}
                disabled={loading} onClick={() => setModeOpen(!modeOpen)}><span className="mode-label"><Icon name={inputMode === 'link' ? 'link' : 'file'} size={16} /> {inputMode === 'link' ? 'Link' : (en ? 'Text' : 'Văn bản')}</span><span className="mode-chevron" aria-hidden="true" /></button>
              {modeOpen && <div className="mode-menu" role="listbox" aria-label="Chọn loại dữ liệu">
                <button type="button" role="option" aria-selected={inputMode === 'link'} onClick={() => chooseMode('link')}><Icon name="link" size={16} /> Link</button>
                <button type="button" role="option" aria-selected={inputMode === 'text'} onClick={() => chooseMode('text')}><Icon name="file" size={16} /> {en ? 'Text' : 'Văn bản'}</button>
              </div>}
            </div>
          </div>
          <label className="visually-hidden" htmlFor="article">{inputMode === 'link' ? 'Đường dẫn bài báo' : 'Nội dung bài báo'}</label>
          {inputMode === 'link'
            ? <input id="article" className="link-input" type="url" maxLength={2048} required ref={article} value={text} disabled={loading}
                onChange={(e) => replaceText(e.target.value)} placeholder="https://example.com/bai-bao" />
            : <textarea id="article" ref={article} value={text} maxLength={50000} disabled={loading}
                onChange={(e) => replaceText(e.target.value)} aria-describedby="article-count article-hint"
                placeholder="Dán nội dung bài báo tiếng Anh vào đây…" />}
          {inputMode === 'text' && <p className="counter" id="article-count">{text.length.toLocaleString('vi-VN')} / 50.000 ký tự · {wordCount.toLocaleString('vi-VN')} từ</p>}
          <p className="field-hint" id="article-hint">{inputMode === 'link' ? 'Nhập URL đầy đủ bắt đầu bằng https://.' : 'Bạn có thể dán nội dung bài báo hoặc viết trực tiếp (tối thiểu 80 ký tự).'}</p>
          <div className="editor-actions">
            <button className="primary" disabled={loading || !valid} type="submit">{loading ? 'Đang phân tích…' : 'Phân tích'} <Icon name="arrow" size={17} /></button>
            <button type="button" className="quiet" disabled={loading || !text}
              onClick={() => { replaceText(''); article.current.focus() }}>Xóa</button>
          </div>
        </form>
        <ResultCard result={result} loading={loading} error={error}>
          {result?.id && <Feedback key={result.id} scope="result" item={result} token={token} onSaved={feedbackSaved} onExpired={expire} />}
        </ResultCard>
      </div>
      <section className="stats-panel" aria-labelledby="stats-title">
        <div className="stats-copy">
          <p className="stats-kicker">{en ? 'ACTIVITY STATISTICS' : 'THỐNG KÊ HOẠT ĐỘNG'}</p>
          <h2 id="stats-title">{en ? 'Your saved checks' : 'NHỮNG LƯỢT KIỂM CHỨNG'}</h2>
          <h3>{en ? 'HELP YOU STAY ALERT...' : 'GIÚP BẠN NHẬN BIẾT...'}</h3>
          <p>{en ? 'Review your analysis history and keep an eye on suspicious signals before trusting an article.' : 'Xem lại lịch sử phân tích và chú ý các dấu hiệu đáng ngờ trước khi tin vào một bài báo.'}</p>
          <button className="stats-action" type="button" aria-expanded={historyOpen} onClick={openHistory}>
            {historyOpen ? (en ? 'Hide history' : 'Ẩn lịch sử') : (en ? 'View history' : 'Xem lịch sử')} <Icon name="arrow" size={16} />
          </button>
        </div>
        <div className="stats-visual">
          <div className="stats-donut" style={{ '--stats-rate': suspiciousRate }} role="img" aria-label={`${suspiciousRate}% kết quả đáng ngờ`}>
            <strong>{history.total.toLocaleString('vi-VN')}</strong>
            <span>{en ? 'saved checks' : 'lượt kiểm chứng'}</span>
          </div>
        </div>
        <div className="stats-bottom">
          <div className="stats-character" aria-hidden="true"><span className="stats-character-screen" /><span className="stats-character-body" /><span className="stats-character-cup" /></div>
          <div className="stats-bottom-copy">
            <strong>{en ? 'STAY INFORMED' : 'LUÔN KIỂM CHỨNG'}</strong>
            <span>{en ? 'Protect yourself from misleading news today.' : 'Chủ động bảo vệ mình trước tin tức sai lệch.'}</span>
            <small>{en ? `${suspiciousCount} suspicious and ${safeCount} lower-risk results in the current page.` : `${suspiciousCount} kết quả đáng ngờ và ${safeCount} kết quả ít đáng ngờ trong trang hiện tại.`}</small>
          </div>
        </div>
      </section>
      {historyOpen && (token ? <HistoryPanel history={history} pageLimit={PAGE_LIMIT} token={token} onPage={loadHistory}
        onSaved={feedbackSaved} onExpired={expire} /> : <section className="card history-panel guest-history">
        <div className="card-title"><span className="tile"><Icon name="file" /></span>
          <div><h2>{en ? 'Personal history' : 'Lịch sử cá nhân'}</h2><p className="muted">{en ? 'Sign in to save and review analyses.' : 'Đăng nhập để lưu và xem lại các lượt phân tích.'}</p></div>
        </div>
      </section>)}
      <footer className="site-footer">
        <div className="footer-main">
          <div className="footer-brand">
            <Brand />
            <p>Công cụ hỗ trợ sàng lọc dấu hiệu đáng ngờ trong bài báo bằng mô hình học máy.</p>
            <div className="footer-links">
              <a className="footer-social" href="https://github.com/Kunte172/sic-fake-news-detector" target="_blank" rel="noreferrer" aria-label="GitHub" title="GitHub"><Icon name="github" size={17} /></a>
              <a className="footer-social" href="mailto:support@sic-fake-news.local" aria-label="Liên hệ" title="Liên hệ"><Icon name="mail" size={17} /></a>
              <a className="footer-social" href="#workspace" aria-label="Hỗ trợ" title="Hỗ trợ"><Icon name="info" size={17} /></a>
            </div>
          </div>
          <div className="footer-info">
            <div className="footer-info-row"><span className="footer-label">DỊCH VỤ</span><strong>Phân tích bài báo tiếng Anh</strong></div>
            <div className="footer-info-row"><span className="footer-label">TÀI KHOẢN</span><strong>Lịch sử phân tích cá nhân</strong></div>
            <div className="footer-info-row"><span className="footer-label">BẢO MẬT</span><strong>Phiên đăng nhập được bảo vệ</strong></div>
          </div>
          <div className="footer-trust">
            <div className="trust-card"><span className="trust-icon"><Icon name="shield" /></span><span><strong>Dữ liệu riêng tư</strong><small>Kiểm soát trong cài đặt</small></span></div>
            <div className="trust-card"><span className="trust-icon"><Icon name="check" /></span><span><strong>Kết quả minh bạch</strong><small>Luôn cần kiểm chứng thêm</small></span></div>
            <div className="trust-card"><span className="trust-icon"><Icon name="info" /></span><span><strong>Hỗ trợ cộng đồng</strong><small>Báo lỗi và góp ý</small></span></div>
          </div>
        </div>
        <div className="footer-resources">
          <div className="footer-resource-actions"><About /><LearnMore /></div>
        </div>
        <div className="footer-bottom">
          <span>Bản quyền © 2026 FNL / Fake News Lens</span>
          <span>Kết quả chỉ mang tính hỗ trợ · Không thay thế kiểm chứng độc lập</span>
        </div>
      </footer>
    </main>
    <Support />
  </>
}
