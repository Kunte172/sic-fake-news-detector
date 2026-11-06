import { useEffect, useRef, useState } from 'react'
import { Icon } from './Theme'

const HISTORY_SETTING = 'sic_save_history'

export default function Settings({ user, language, onLogout }) {
  const dialog = useRef(null)
  const menu = useRef(null)
  const [section, setSection] = useState('account')
  const [historyEnabled, setHistoryEnabled] = useState(() => localStorage.getItem(HISTORY_SETTING) !== 'false')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    localStorage.setItem(HISTORY_SETTING, String(historyEnabled))
  }, [historyEnabled])

  function openSection(nextSection) {
    setSection(nextSection)
    menu.current?.setAttribute('hidden', '')
    dialog.current?.showModal()
  }

  const titles = {
    account: 'Thông tin tài khoản',
    data: 'Dữ liệu',
    language: 'Ngôn ngữ',
    support: 'Hỗ trợ',
  }

  return <>
    <div className="settings-menu-wrap">
      <button type="button" className="icon-button settings-trigger" aria-label="Mở menu tài khoản"
        aria-haspopup="menu" onClick={() => menu.current?.toggleAttribute('hidden')}>
        <Icon name="settings" />
      </button>
      <div ref={menu} className="settings-menu" role="menu" hidden>
        <div className="settings-menu-user"><span className="avatar"><Icon name="user" size={17} /></span><span><strong>Tài khoản</strong><small>{user.email}</small></span></div>
        <button type="button" role="menuitem" onClick={() => openSection('account')}><Icon name="user" size={19} /><span>Thông tin tài khoản</span></button>
        <div className="settings-menu-divider" />
        <button type="button" role="menuitem" onClick={() => openSection('data')}><Icon name="shield" size={19} /><span>Dữ liệu</span><b>›</b></button>
        <button type="button" role="menuitem" onClick={() => openSection('language')}><Icon name="info" size={19} /><span>Ngôn ngữ</span><b>›</b></button>
        <button type="button" role="menuitem" onClick={() => openSection('support')}><Icon name="info" size={19} /><span>Hỗ trợ</span><b>›</b></button>
        <div className="settings-menu-divider" />
        <button type="button" className="settings-menu-logout" role="menuitem" onClick={onLogout}>Đăng xuất</button>
      </div>
    </div>
    <dialog ref={dialog} className="settings-dialog" aria-labelledby="settings-title">
      <div className="support-header">
        <div><p className="eyebrow">TÀI KHOẢN VÀ TRỢ GIÚP</p><h2 id="settings-title">{titles[section]}</h2></div>
        <button className="icon-button" type="button" aria-label="Đóng cài đặt" onClick={() => dialog.current.close()}>
          <Icon name="close" />
        </button>
      </div>

      {section === 'account' && <section className="settings-section">
        <div className="settings-heading"><span className="tile"><Icon name="user" /></span><div><h3>Tài khoản</h3><p className="muted">Thông tin phiên đăng nhập hiện tại</p></div></div>
        <div className="settings-row"><span>Email</span><strong>{user.email}</strong></div>
        <button type="button" className="secondary full" disabled title="Chức năng cần API backend">Đổi mật khẩu</button>
        <p className="field-hint">Đổi mật khẩu sẽ được bổ sung khi API tài khoản hỗ trợ.</p>
      </section>}

      {section === 'data' && <section className="settings-section">
        <div className="settings-heading"><span className="tile"><Icon name="shield" /></span><div><h3>Dữ liệu cá nhân</h3><p className="muted">Kiểm soát lịch sử phân tích</p></div></div>
        <div className="theme-options" role="group" aria-label="Chọn giao diện">
          <button type="button" className="secondary" aria-pressed={historyEnabled} onClick={() => setHistoryEnabled(true)}>Lưu lịch sử</button>
          <button type="button" className="secondary" aria-pressed={!historyEnabled} onClick={() => setHistoryEnabled(false)}>Không lưu</button>
        </div>
        <label className="switch-row"><span><strong>Lưu lịch sử phân tích</strong><small>Cho phép lưu kết quả vào tài khoản</small></span>
          <input type="checkbox" checked={historyEnabled} onChange={(event) => setHistoryEnabled(event.target.checked)} />
        </label>
        <button type="button" className="secondary full" disabled title="Chức năng cần API backend">Xóa lịch sử</button>
        <p className="field-hint">Xóa dữ liệu trên máy chủ cần được xác nhận qua API backend.</p>
        {notice && <p className="notice" role="status">{notice}</p>}
      </section>}

      {section === 'language' && <section className="settings-section">
        <div className="settings-heading"><span className="tile"><Icon name="info" /></span><div><h3>Ngôn ngữ hiển thị</h3><p className="muted">Chọn ngôn ngữ cho giao diện</p></div></div>
        <div className="theme-options" role="group" aria-label="Chọn ngôn ngữ">
          <button type="button" className="secondary" aria-pressed={language?.language !== 'en'} onClick={() => language?.language === 'en' && language.toggleLanguage()}>Tiếng Việt</button>
          <button type="button" className="secondary" aria-pressed={language?.language === 'en'} onClick={() => language?.language !== 'en' && language.toggleLanguage()}>English</button>
        </div>
      </section>}

      {section === 'support' && <section className="settings-section">
        <div className="settings-heading"><span className="tile"><Icon name="info" /></span><div><h3>Trung tâm hỗ trợ</h3><p className="muted">Các thông tin cần thiết khi sử dụng</p></div></div>
        <div className="settings-note"><strong>Cách sử dụng</strong><br />Chọn Văn bản để dán nội dung bài báo, sau đó bấm Phân tích để nhận kết quả.</div>
        <div className="settings-note"><strong>Liên hệ hỗ trợ</strong><br />Gửi phản hồi hoặc lỗi qua email hỗ trợ của ứng dụng.</div>
        <a className="secondary full" href="mailto:support@sic-fake-news.local">Gửi email hỗ trợ</a>
      </section>}

    </dialog>
  </>
}
