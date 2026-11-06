import { useEffect, useState } from 'react'

const key = 'sic_theme'
const languageKey = 'sic_language'
const system = () => matchMedia('(prefers-color-scheme: dark)')

export function useTheme() {
  const [choice, setChoice] = useState(() => {
    const saved = localStorage.getItem(key)
    return saved === 'dark' || saved === 'light' ? saved : null
  })
  const [prefersDark, setPrefersDark] = useState(() => system().matches)
  const theme = choice || (prefersDark ? 'dark' : 'light')
  useEffect(() => {
    const query = system()
    const update = (event) => setPrefersDark(event.matches)
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])
  useEffect(() => { document.documentElement.dataset.theme = theme }, [theme])
  return {
    theme,
    toggle() {
      const next = theme === 'dark' ? 'light' : 'dark'
      localStorage.setItem(key, next)
      setChoice(next)
    },
  }
}

export function ThemeButton({ theme, toggle }) {
  return <button type="button" className="icon-button" onClick={toggle}
    aria-label={theme === 'dark' ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}>
    <Icon name={theme === 'dark' ? 'sun' : 'moon'} />
  </button>
}

export function useLanguage() {
  const [language, setLanguage] = useState(() => localStorage.getItem(languageKey) === 'en' ? 'en' : 'vi')
  function toggleLanguage() {
    const next = language === 'vi' ? 'en' : 'vi'
    localStorage.setItem(languageKey, next)
    setLanguage(next)
  }
  return { language, toggleLanguage }
}

export function LanguageButton({ language, toggleLanguage }) {
  const english = language === 'en'
  return <button type="button" className="language-button" onClick={toggleLanguage}
    aria-label={english ? 'Switch to Vietnamese' : 'Chuyển sang tiếng Anh'}>
    <span className={english ? '' : 'active'}>VI</span><span className="language-divider">/</span><span className={english ? 'active' : ''}>EN</span>
  </button>
}

const paths = {
  scan: 'M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3m13-5v3a2 2 0 0 1-2 2h-3M8 12h8m-6 4h4m-4-8h4',
  sun: 'M12 2v2m0 16v2M2 12h2m16 0h2M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z',
  moon: 'M20.8 14.5A9 9 0 0 1 9.5 3.2 9 9 0 1 0 20.8 14.5Z',
  arrow: 'M4 12h15m-6-6 6 6-6 6',
  eye: 'M2 12s4-6 10-6 10 6 10 6-4 6-10 6-10-6-10-6Zm13 0a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z',
  eyeOff: 'M3 3l18 18M10 6c.6-.1 1.3-.2 2-.2 6 0 10 6.2 10 6.2a19 19 0 0 1-3 3.2M6 7.6C3.6 9.4 2 12 2 12s4 6 10 6c1.4 0 2.6-.3 3.7-.8',
  close: 'm6 6 12 12M18 6 6 18',
  check: 'm5 12 4 4L19 6',
  warning: 'M12 8v5m0 4h.01M10.5 4.5 2.8 18a1.3 1.3 0 0 0 1.1 2h16.2a1.3 1.3 0 0 0 1.1-2L13.5 4.5a1.7 1.7 0 0 0-3 0Z',
  file: 'M6 3h8l4 4v14H6V3Zm8 0v5h4M9 12h6m-6 4h6',
  settings: 'M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Zm8.2 3.5c0-.5-.1-1-.2-1.5l2-1.5-2-3.4-2.3.9a8 8 0 0 0-2.6-1.5L14.8 2h-4l-.3 2.5a8 8 0 0 0-2.6 1.5l-2.3-.9-2 3.4 2 1.5A8 8 0 0 0 5.4 12c0 .5.1 1 .2 1.5l-2 1.5 2 3.4 2.3-.9a8 8 0 0 0 2.6 1.5l.3 2.5h4l.3-2.5a8 8 0 0 0 2.6-1.5l2.3.9 2-3.4-2-1.5c.1-.5.2-1 .2-1.5Z',
  user: 'M20 21a8 8 0 0 0-16 0m12-13a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z',
  shield: 'M12 3 20 6v5c0 5-3.4 8.5-8 10-4.6-1.5-8-5-8-10V6l8-3Z',
  info: 'M12 16v-4m0-4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  link: 'M10 13a5 5 0 0 0 7.1.1l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1m3.1 5.9a5 5 0 0 0-7.1-.1l-2 2a5 5 0 0 0 7.1 7.1l1.1-1.1',
  github: 'M15 22v-3.9c0-1.1-.4-1.9-1-2.5 3.3-.4 6.8-1.6 6.8-7.2 0-1.6-.6-2.9-1.6-3.9.2-.4.7-1.9-.2-3.8 0 0-1.3-.4-4.1 1.5a14 14 0 0 0-7.5 0C4.6.4 3.3.8 3.3.8c-.9 1.9-.4 3.4-.2 3.8-1 1-1.6 2.3-1.6 3.9 0 5.6 3.5 6.8 6.8 7.2-.6.5-1 1.3-1 2.5V22m-4.8-3.3c.4.1 1.2.2 2.1.2 1.5 0 2.5-.5 3.1-1.5',
  mail: 'M3 5h18v14H3V5Zm0 1 9 7 9-7',
  refresh: 'M20 11a8 8 0 0 0-14.8-4L3 10m0-5v5h5m-4 3a8 8 0 0 0 14.8 4L21 14m0 5v-5h-5',
}

export function Icon({ name, size = 20 }) {
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round">
    <path d={paths[name]} />
  </svg>
}

export function Brand() {
  return <div className="brand">
    <span className="brand-mark"><Icon name="scan" size={24} /></span>
    <span><strong>FNL / Fake News Lens</strong></span>
  </div>
}
