import { useState } from 'react'
import { ApiError, api, errText } from './bff'
import type { AuthUser } from './bff'

interface LoginModalProps {
  onSuccess: (user: AuthUser, token: string) => void
  /** A calm explanation shown above the form, e.g. an expired session. */
  notice?: string
}

type Mode = 'login' | 'register'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function LoginModal({ onSuccess, notice }: LoginModalProps) {
  const [mode, setMode] = useState<Mode>('login')
  const [name, setName] = useState('')
  const [company, setCompany] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [reveal, setReveal] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function switchMode(next: Mode) {
    setMode(next)
    setPassword('')
    setReveal(false)
    setError('')
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (loading) return
    const mail = email.trim()
    if (mode === 'register' && !name.trim()) {
      setError('Isi nama lengkap Anda.')
      return
    }
    if (!mail) {
      setError('Isi email Anda.')
      return
    }
    if (!EMAIL_RE.test(mail)) {
      setError('Format email belum benar. Contoh: nama@perusahaan.com.')
      return
    }
    if (!password) {
      setError('Isi kata sandi Anda.')
      return
    }
    if (mode === 'register' && password.length < 6) {
      setError('Kata sandi minimal 6 karakter.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res =
        mode === 'login'
          ? await api.auth.login(mail, password)
          : await api.auth.register(name.trim(), mail, password, company.trim() || undefined)
      onSuccess(res.user, res.token)
    } catch (err) {
      setError(err instanceof ApiError && err.status === 401 ? 'Email atau kata sandi salah.' : errText(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-overlay">
      <div className="login-card" role="region" aria-label="Masuk ke Pegawai AI">
        <div className="login-header">
          <div className="login-brand">
            <svg className="mark" viewBox="0 0 32 32" width={32} height={32} aria-hidden="true">
              <path d="M16 3 28 9.500 16 16 4 9.500z" fill="var(--control)" />
              <path d="M4 9.500 16 16v13L4 22.500z" fill="var(--text)" />
              <path d="M28 9.500 16 16v13l12-6.500z" fill="var(--accent)" />
            </svg>
            <h1>Pegawai AI</h1>
          </div>
          <p className="login-subtitle">Pegawai AI untuk bisnis Anda.</p>
        </div>

        <div className="login-tabs" role="group" aria-label="Pilih masuk atau daftar">
          <button type="button" className="login-tab" aria-pressed={mode === 'login'} onClick={() => switchMode('login')}>
            Masuk
          </button>
          <button type="button" className="login-tab" aria-pressed={mode === 'register'} onClick={() => switchMode('register')}>
            Daftar
          </button>
        </div>

        {notice && !error && (
          <p className="login-banner notice" role="status">
            <span className="login-banner-icon" aria-hidden="true">
              !
            </span>
            <span>{notice}</span>
          </p>
        )}
        {error && (
          <p className="login-banner error" role="alert">
            <span className="login-banner-icon" aria-hidden="true">
              !
            </span>
            <span>{error}</span>
          </p>
        )}

        <form className="login-form" onSubmit={submit} noValidate>
          {mode === 'register' && (
            <>
              <div className="login-field">
                <label className="login-label" htmlFor="login-name">
                  Nama lengkap
                </label>
                <input
                  id="login-name"
                  type="text"
                  autoComplete="name"
                  placeholder="Nama Anda"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="login-field">
                <label className="login-label" htmlFor="login-company">
                  Perusahaan atau brand <span className="login-optional">(opsional)</span>
                </label>
                <input
                  id="login-company"
                  type="text"
                  autoComplete="organization"
                  placeholder="Nama usaha Anda"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                />
              </div>
            </>
          )}

          <div className="login-field">
            <label className="login-label" htmlFor="login-email">
              Email
            </label>
            <input
              id="login-email"
              type="email"
              inputMode="email"
              autoComplete="email"
              placeholder="nama@perusahaan.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="login-field">
            <label className="login-label" htmlFor="login-password">
              Kata sandi
            </label>
            <div className="login-password">
              <input
                id="login-password"
                type={reveal ? 'text' : 'password'}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                placeholder={mode === 'register' ? 'Minimal 6 karakter' : 'Kata sandi Anda'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="login-eye"
                aria-label={reveal ? 'Sembunyikan kata sandi' : 'Tampilkan kata sandi'}
                aria-pressed={reveal}
                onClick={() => setReveal(!reveal)}
              >
                {reveal ? 'Sembunyikan' : 'Lihat'}
              </button>
            </div>
            {mode === 'register' && <small className="login-hint">Minimal 6 karakter.</small>}
          </div>

          <button type="submit" className="btn primary login-submit" disabled={loading}>
            {loading && <span className="login-spinner" aria-hidden="true" />}
            {loading ? 'Memeriksa…' : mode === 'login' ? 'Masuk' : 'Daftar dan masuk'}
          </button>
        </form>

        <p className="login-foot">
          {mode === 'login' ? 'Lupa kata sandi? Hubungi admin tim Anda.' : 'Akun baru langsung aktif setelah didaftarkan.'}
        </p>
      </div>

      <style>{`
        .login-overlay {
          position: fixed;
          inset: 0;
          z-index: 9999;
          display: flex;
          align-items: flex-start;
          justify-content: center;
          padding: var(--s-4);
          background: var(--ground);
          overflow-y: auto;
        }
        .login-card {
          width: 100%;
          max-width: 420px;
          align-self: flex-start;
          margin: clamp(48px, 12vh, 120px) auto 0;
          padding: var(--s-6);
          background: var(--surface);
          color: var(--text);
          border: 1px solid var(--border);
          border-radius: 16px;
          box-shadow: 0 24px 48px -20px rgba(0, 0, 0, 0.35);
        }
        .login-header {
          margin-bottom: var(--s-5);
          text-align: center;
        }
        .login-brand {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          margin-bottom: 6px;
        }
        .login-brand h1 {
          font-size: 22px;
          font-weight: 600;
          letter-spacing: -0.01em;
        }
        .login-subtitle {
          font-size: var(--t-small);
          color: var(--muted);
        }
        .login-tabs {
          display: flex;
          gap: 4px;
          margin-bottom: var(--s-4);
          padding: 3px;
          background: var(--raised);
          border: 1px solid var(--rule);
          border-radius: var(--radius-control);
        }
        .login-tab {
          flex: 1;
          height: 32px;
          border: 0;
          border-radius: 4px;
          background: transparent;
          color: var(--muted);
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: background-color var(--m-in) var(--ease), color var(--m-in) var(--ease);
        }
        .login-tab:hover {
          color: var(--text);
        }
        .login-tab[aria-pressed="true"] {
          background: var(--surface);
          color: var(--text);
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
        .login-banner {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          margin-bottom: var(--s-4);
          padding: 10px 12px;
          border-radius: var(--radius-control);
          font-size: 13px;
          line-height: 1.45;
        }
        .login-banner.error {
          background: var(--bad-bg);
          color: var(--bad-ink);
        }
        .login-banner.notice {
          background: var(--warn-bg);
          color: var(--warn-ink);
        }
        .login-banner-icon {
          flex: none;
          display: inline-grid;
          place-items: center;
          width: 18px;
          height: 18px;
          margin-top: 1px;
          border: 1px solid currentColor;
          border-radius: 50%;
          font-size: 11px;
          font-weight: 700;
          line-height: 1;
        }
        .login-form {
          display: flex;
          flex-direction: column;
          gap: var(--s-4);
        }
        .login-field {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .login-label {
          font-size: 13px;
          font-weight: 500;
        }
        .login-optional,
        .login-hint {
          color: var(--muted);
          font-weight: 400;
        }
        .login-hint {
          font-size: 12px;
        }
        .login-field input {
          width: 100%;
          height: 44px;
          padding: 0 12px;
          font-size: var(--t-body);
        }
        .login-password {
          position: relative;
        }
        .login-password input {
          padding-right: 92px;
        }
        .login-eye {
          position: absolute;
          top: 50%;
          right: 4px;
          height: 34px;
          padding: 0 10px;
          border: 0;
          border-radius: var(--radius-control);
          background: transparent;
          color: var(--link);
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          transform: translateY(-50%);
        }
        .login-eye:hover {
          background: var(--raised);
          color: var(--text);
        }
        .login-submit {
          width: 100%;
          height: 44px;
          margin-top: var(--s-1);
          font-size: var(--t-body);
        }
        .login-spinner {
          width: 14px;
          height: 14px;
          border: 2px solid color-mix(in srgb, var(--on-primary) 35%, transparent);
          border-top-color: var(--on-primary);
          border-radius: 50%;
          animation: login-spin 0.7s linear infinite;
        }
        @keyframes login-spin {
          to {
            transform: rotate(360deg);
          }
        }
        .login-foot {
          margin-top: var(--s-4);
          text-align: center;
          font-size: 12px;
          line-height: 1.5;
          color: var(--muted);
        }
        @media (max-width: 640px) {
          .login-tab {
            height: 40px;
          }
        }
        @media (max-width: 420px) {
          .login-overlay {
            align-items: stretch;
            padding: 0;
          }
          .login-card {
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            max-width: none;
            min-height: 100svh;
            margin: 0;
            padding: var(--s-5) var(--s-4);
            border: 0;
            border-radius: 0;
            box-shadow: none;
          }
          .login-field input {
            font-size: 16px; /* iOS does not zoom the page when a field is at least 16 px */
          }
        }
      `}</style>
    </div>
  )
}
