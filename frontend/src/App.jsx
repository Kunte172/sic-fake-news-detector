import { useEffect, useRef, useState } from 'react'
import AdminDashboard from './AdminDashboard.jsx'
import AuthPage from './pages/AuthPage.jsx'
import AnalyzePage from './pages/AnalyzePage.jsx'
import { Brand, useTheme, useLanguage } from './components/Theme.jsx'
import { api } from './api.js'

const TOKEN_KEY = 'sic_access_token'
const GUEST_KEY = 'sic_guest_mode'
export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(GUEST_KEY) === '1' ? '' : localStorage.getItem(TOKEN_KEY) || '')
  const [guest, setGuest] = useState(() => localStorage.getItem(GUEST_KEY) === '1')
  const [user, setUser] = useState(null)
  const [screen, setScreen] = useState('analyze')
  const [sessionMessage, setSessionMessage] = useState('')
  const [profileError, setProfileError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const activeTokenRef = useRef(token)
  const theme = useTheme()
  const language = useLanguage()

  const isSessionCurrent = () => activeTokenRef.current === token && Boolean(token)

  function clearSession(message = '') {
    activeTokenRef.current = ''
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(GUEST_KEY)
    setSessionMessage(typeof message === 'string' ? message : '')
    setToken('')
    setGuest(false)
    setUser(null)
    setProfileError('')
    setScreen('analyze')
  }
  function startSession(nextToken) {
    activeTokenRef.current = nextToken
    localStorage.setItem(TOKEN_KEY, nextToken)
    localStorage.removeItem(GUEST_KEY)
    setSessionMessage('')
    setProfileError('')
    setUser(null)
    setGuest(false)
    setScreen('analyze')
    setToken(nextToken)
  }
  function startGuest() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.setItem(GUEST_KEY, '1')
    setSessionMessage('')
    setProfileError('')
    setUser(null)
    activeTokenRef.current = ''
    setToken('')
    setGuest(true)
    setScreen('analyze')
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
      if (destination && location.pathname !== destination) window.history.replaceState(null, '', destination)
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
    return (
      <AdminDashboard
        token={token}
        onUnauthorized={(message) => clearSession(message)}
        isSessionCurrent={isSessionCurrent}
        theme={theme}
        language={language}
        onLogout={() => clearSession()}
        onOpenAnalyze={() => setScreen('analyze')}
      />
    )
  }

  return <AnalyzePage key={token} user={user} token={token} theme={theme} language={language}
    onLogout={clearSession} onOpenAdmin={() => setScreen('admin')} />
}
