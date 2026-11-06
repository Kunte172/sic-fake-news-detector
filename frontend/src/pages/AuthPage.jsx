import { useEffect, useState } from 'react'
import { api } from '../api'
import { Brand, Icon, LanguageButton, ThemeButton } from '../components/Theme'

function PasswordField({ id, label, value, onChange, register }) {
  const [visible, setVisible] = useState(false)
  return <div className="field">
    <label htmlFor={id}>{label}</label>
    <div className="password-field">
      <input id={id} type={visible ? 'text' : 'password'} value={value} onChange={onChange}
        required minLength={6} maxLength={72} autoComplete={register ? 'new-password' : 'current-password'} />
      <button type="button" className="icon-button" onClick={() => setVisible(!visible)}
        aria-label={visible ? 'Ẩn ' + label.toLowerCase() : 'Hiện ' + label.toLowerCase()}>
        <Icon name={visible ? 'eyeOff' : 'eye'} size={18} />
      </button>
    </div>
  </div>
}

export default function AuthPage({ onLogin, onGuest, sessionMessage, theme, language }) {
  const en = language.language === 'en'
  const [mode, setMode] = useState('login')
  const [authStep, setAuthStep] = useState('form')
  const [code, setCode] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const register = mode === 'register'

  function switchMode(next) {
    if (next === mode) return
    setMode(next)
    setPassword('')
    setConfirmation('')
    setError('')
    setNotice('')
    setAuthStep('form')
    setCode('')
  }

  async function submit(event) {
    event.preventDefault()
    if (busy) return
    setError('')
    setNotice('')
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError('Vui lòng nhập địa chỉ email hợp lệ.')
      return
    }
    const enteringRegistrationCode = register && authStep === 'code'
    if (!enteringRegistrationCode) {
      if (password.length < 6 || new TextEncoder().encode(password).length > 72) {
        setError('Mật khẩu cần ít nhất 6 ký tự và tối đa 72 byte.')
        return
      }
      if ((register || mode === 'reset') && (!/^\p{Lu}/u.test(password) || !/[^\p{L}\p{N}\s]/u.test(password))) {
        setError('Mật khẩu phải bắt đầu bằng chữ hoa và có ít nhất 1 ký tự đặc biệt.')
        return
      }
      if (register && password !== confirmation) {
        setError('Hai mật khẩu phải trùng nhau.')
        return
      }
    } else if (!/^\d{6}$/.test(code)) {
      setError('Vui lòng nhập đủ 6 chữ số trong mã xác minh.')
      return
    }
    setBusy(true)
    const body = { email: email.trim(), password }
    let registering = register
    try {
      if (mode === 'reset') {
        await api('/auth/password-reset/verify', { body: { email: email.trim(), code, password } })
        setMode('login')
        setAuthStep('form')
        setPassword('')
        setCode('')
        setNotice('Đã đổi mật khẩu. Bạn có thể đăng nhập bằng mật khẩu mới.')
        return
      }
      if (register && authStep === 'form') {
        await api('/auth/register/request-code', { body })
        setAuthStep('code')
        setNotice('Mã xác minh đã được gửi đến email của bạn.')
        return
      }
      if (register && authStep === 'code') {
        await api('/auth/register/verify', { body: { ...body, code } })
        const data = await api('/auth/login', { body })
        if (typeof data.access_token !== 'string' || !data.access_token) {
          throw new Error('Máy chủ chưa cấp phiên đăng nhập.')
        }
        onLogin(data.access_token)
        return
      }
      const data = await api('/auth/login', { body })
      if (typeof data.access_token !== 'string' || !data.access_token) {
        throw new Error('Máy chủ chưa cấp phiên đăng nhập.')
      }

      onLogin(data.access_token)
    } catch (cause) {
      setNotice('')
      setError(
        cause instanceof TypeError ? 'Không kết nối được máy chủ. Vui lòng thử lại.'
        : registering && cause.status === 400 && (authStep === 'form' || cause.message.includes('Email')) ? 'Email này đã được đăng ký.'
        : registering && cause.status === 400 ? cause.message || 'Mã xác minh không hợp lệ.'
        : cause.status === 404 ? 'API xác minh email chưa được khởi động lại. Vui lòng khởi động lại backend.'
        : cause.status === 503 ? 'Máy chủ chưa cấu hình SMTP để gửi mã email.'
        : cause.status === 401 ? 'Email hoặc mật khẩu chưa đúng.'
        : cause.status === 422 ? 'Mật khẩu phải bắt đầu bằng chữ hoa và có ít nhất 1 ký tự đặc biệt.'
        : registering ? 'Đăng ký chưa thành công. Vui lòng thử lại.'
        : 'Đăng nhập chưa thành công. Vui lòng thử lại.'
      )
    } finally {
      setBusy(false)
    }

  }

  useEffect(() => {
    if (register && authStep === 'code' && code.length === 6 && !busy) {
      submit({ preventDefault() {} })
    }
  }, [code, authStep, register, busy])

  function showReset() {
    setMode('reset')
    setAuthStep('form')
    setPassword('')
    setConfirmation('')
    setCode('')
    setError('')
    setNotice('')
  }

  return <main className="auth-layout">
    <aside className="auth-intro" aria-labelledby="intro-title">
      <Brand />
      <div className="intro-content">
        <p className="eyebrow">CÔNG CỤ HỖ TRỢ KIỂM CHỨNG</p>
        <h1 id="intro-title">Sàng lọc dấu hiệu đáng ngờ trong bài báo</h1>
        <p>Dùng điểm dự đoán để biết bài viết nào cần kiểm chứng kỹ hơn.</p>
        <ul>
          <li><Icon name="file" /> Phân tích nội dung bài báo tiếng Anh</li>
          <li><Icon name="scan" /> Xem điểm dự đoán và phiên bản mô hình</li>
          <li><Icon name="check" /> Xem lại lịch sử và gửi phản hồi</li>
        </ul>
      </div>
      <span className="intro-foot">FNL / Fake News Lens</span>
    </aside>
    <section className="auth-main" aria-labelledby="auth-title">
      <div className="auth-theme"><LanguageButton {...language} /><ThemeButton {...theme} /></div>
      <div className="auth-card">
        <div className="mobile-brand"><Brand /></div>
        <p className="eyebrow">{en ? 'ACCOUNT' : 'TÀI KHOẢN'}</p>
        <h2 id="auth-title">{mode === 'reset' ? (en ? 'Reset password' : 'Quên mật khẩu') : register ? (authStep === 'code' ? (en ? 'Verify email' : 'Xác minh email') : (en ? 'Create account' : 'Tạo tài khoản')) : (en ? 'Sign in' : 'Đăng nhập')}</h2>
        <p className="muted">{en ? 'Sign in to analyze articles and save results.' : 'Đăng nhập để phân tích bài báo và lưu kết quả.'}</p>
        {mode !== 'reset' && <div className="segments" role="group" aria-label="Chọn đăng nhập hoặc đăng ký">
          <button type="button" aria-pressed={!register} disabled={busy} onClick={() => switchMode('login')}>{en ? 'Sign in' : 'Đăng nhập'}</button>
          <button type="button" aria-pressed={register} disabled={busy} onClick={() => switchMode('register')}>{en ? 'Sign up' : 'Đăng ký'}</button>
        </div>}
        <form onSubmit={submit} noValidate>
          <fieldset disabled={busy}>
            <div className="field"><label htmlFor="email">Email</label>
              <input id="email" type="email" required autoComplete="email" placeholder="nguyenvana@gmail.com"
                value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            {authStep === 'code' && <div className="field"><label htmlFor="code">{en ? 'Verification code' : 'Mã xác minh'}</label><input id="code" inputMode="numeric" pattern="\d{6}" maxLength={6} required value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))} placeholder={en ? 'Enter 6 digits' : 'Nhập 6 chữ số'} /></div>}
            {(mode !== 'reset' && authStep === 'form') || (mode === 'reset' && authStep === 'code') ? <PasswordField key={mode + authStep} id="password" label={mode === 'reset' ? 'Mật khẩu mới' : 'Mật khẩu'} value={password}
              onChange={(e) => setPassword(e.target.value)} register={register} /> : null}
            {register && authStep === 'form' && <>
              <PasswordField id="confirmation" label="Xác nhận mật khẩu" value={confirmation}
                onChange={(e) => setConfirmation(e.target.value)} register /></>}
            {error && <p className="notice error" role="alert">{error}</p>}
            {!error && sessionMessage && !busy && !notice && <p className="notice" role="status">{sessionMessage}</p>}
            {notice && <p className="notice" role="status">{notice}</p>}
            {mode === 'reset' && authStep === 'form' && <button className="primary full" type="button" disabled={busy} onClick={async () => {
              setBusy(true); setError(''); setNotice('')
              try { await api('/auth/password-reset/request-code', { body: { email: email.trim() } }); setAuthStep('code'); setNotice('Mã đặt lại mật khẩu đã được gửi đến email.') }
              catch (cause) { setError(cause.status === 404 ? 'Email chưa được đăng ký.' : 'Không thể gửi mã. Vui lòng thử lại.') }
              finally { setBusy(false) }
            }}>Gửi mã xác minh <Icon name="arrow" size={17} /></button>}
            {(mode !== 'reset' || authStep === 'code') && <button className="primary full" type="submit" disabled={busy}>
              {busy ? 'Đang xử lý…' : mode === 'reset' ? 'Đặt lại mật khẩu' : register && authStep === 'form' ? 'Tiếp tục' : register ? 'Xác minh và tạo tài khoản' : 'Đăng nhập'} <Icon name="arrow" size={17} />
            </button>}
            {mode === 'login' && <button type="button" className="quiet full" onClick={showReset}>Quên mật khẩu?</button>}
            {mode === 'reset' && <button type="button" className="quiet full" onClick={() => switchMode('login')}>Quay lại đăng nhập</button>}
          </fieldset>
        </form>
        <div className="guest-entry">
          <span className="muted">{en ? 'Just want to try it?' : 'Chỉ muốn dùng thử?'}</span>
          <button type="button" className="quiet" onClick={onGuest}>{en ? 'Continue as guest' : 'Tiếp tục không đăng nhập'}</button>
        </div>
      </div>
    </section>
  </main>
}
