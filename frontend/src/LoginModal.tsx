import { useState } from 'react'
import { api, errText } from './bff'
import type { AuthUser } from './bff'

interface LoginModalProps {
  onSuccess: (user: AuthUser) => void
}

export function LoginModal({ onSuccess }: LoginModalProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('admin@pegawai.ai')
  const [password, setPassword] = useState('Admin1234!')
  const [name, setName] = useState('')
  const [company, setCompany] = useState('Colorbox')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const quickLogin = (qEmail: string, qPass: string) => {
    setEmail(qEmail)
    setPassword(qPass)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      if (mode === 'login') {
        const res = await api.auth.login(email, password)
        localStorage.setItem('pegawai_ai_token', res.token)
        localStorage.setItem('pegawai_ai_user', JSON.stringify(res.user))
        onSuccess(res.user)
      } else {
        const res = await api.auth.register(name, email, password, company)
        localStorage.setItem('pegawai_ai_token', res.token)
        localStorage.setItem('pegawai_ai_user', JSON.stringify(res.user))
        onSuccess(res.user)
      }
    } catch (err) {
      setError(errText(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-overlay">
      <div className="login-card">
        <div className="login-header">
          <div className="login-brand">
            <svg viewBox="0 0 32 32" width="36" height="36" aria-hidden="true">
              <path d="M16 3 28 9.500 16 16 4 9.500z" fill="#000" />
              <path d="M4 9.500 16 16v13L4 22.500z" fill="#333" />
              <path d="M28 9.500 16 16v13l12-6.500z" fill="#2563eb" />
            </svg>
            <h2>Pegawai AI</h2>
          </div>
          <p className="login-subtitle">
            {mode === 'login' ? 'Platform Agen Multi-AI untuk Brand Fashion' : 'Daftar Akun Baru Pegawai AI'}
          </p>
        </div>

        <div className="login-tabs">
          <button
            type="button"
            className={`login-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setError(null) }}
          >
            Masuk
          </button>
          <button
            type="button"
            className={`login-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => { setMode('register'); setError(null) }}
          >
            Daftar Akun
          </button>
        </div>

        {error && (
          <div className="login-error-banner" role="alert">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          {mode === 'register' && (
            <>
              <div className="form-group">
                <label htmlFor="reg-name">Nama Lengkap</label>
                <input
                  id="reg-name"
                  type="text"
                  required
                  placeholder="Misal: Kevin Anugerah"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="reg-company">Nama Perusahaan / Brand</label>
                <input
                  id="reg-company"
                  type="text"
                  placeholder="Misal: Colorbox"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                />
              </div>
            </>
          )}

          <div className="form-group">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              required
              placeholder="nama@perusahaan.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="login-password">Kata Sandi</label>
            <input
              id="login-password"
              type="password"
              required
              placeholder="Minimal 6 karakter"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button type="submit" className="login-btn-primary" disabled={loading}>
            {loading ? 'Memproses…' : (mode === 'login' ? 'Masuk ke Platform' : 'Daftar & Masuk')}
          </button>
        </form>

        {mode === 'login' && (
          <div className="quick-login-section">
            <p className="quick-login-title">Akun Demo Cepat (1-Klik):</p>
            <div className="quick-login-chips">
              <button
                type="button"
                className="chip-btn"
                onClick={() => quickLogin('owner@colorbox.co.id', 'Admin1234!')}
              >
                👑 Owner
              </button>
              <button
                type="button"
                className="chip-btn"
                onClick={() => quickLogin('cs@colorbox.co.id', 'Admin1234!')}
              >
                🎧 CS Lead
              </button>
              <button
                type="button"
                className="chip-btn"
                onClick={() => quickLogin('marketing@colorbox.co.id', 'Admin1234!')}
              >
                📊 Marketing
              </button>
              <button
                type="button"
                className="chip-btn"
                onClick={() => quickLogin('admin@pegawai.ai', 'Admin1234!')}
              >
                ⚡ Super Admin
              </button>
            </div>
          </div>
        )}
      </div>

      <style>{`
        .login-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(15, 23, 42, 0.85);
          backdrop-filter: blur(8px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 9999;
          padding: 16px;
        }
        .login-card {
          background: #ffffff;
          border-radius: 16px;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
          width: 100%;
          max-width: 440px;
          padding: 32px;
          color: #0f172a;
          font-family: inherit;
        }
        .login-header {
          text-align: center;
          margin-bottom: 24px;
        }
        .login-brand {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          margin-bottom: 8px;
        }
        .login-brand h2 {
          font-size: 24px;
          font-weight: 700;
          margin: 0;
          color: #0f172a;
        }
        .login-subtitle {
          font-size: 13px;
          color: #64748b;
          margin: 0;
        }
        .login-tabs {
          display: flex;
          background: #f1f5f9;
          padding: 4px;
          border-radius: 8px;
          margin-bottom: 20px;
        }
        .login-tab {
          flex: 1;
          padding: 8px 12px;
          font-size: 13px;
          font-weight: 600;
          border: none;
          background: transparent;
          color: #64748b;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .login-tab.active {
          background: #ffffff;
          color: #0f172a;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .login-error-banner {
          background: #fef2f2;
          border: 1px solid #fecaca;
          color: #b91c1c;
          padding: 10px 14px;
          border-radius: 8px;
          font-size: 13px;
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 16px;
        }
        .login-form {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
          text-align: left;
        }
        .form-group label {
          font-size: 12px;
          font-weight: 600;
          color: #334155;
        }
        .form-group input {
          padding: 10px 14px;
          border: 1px solid #cbd5e1;
          border-radius: 8px;
          font-size: 14px;
          color: #0f172a;
          outline: none;
          transition: border-color 0.2s;
        }
        .form-group input:focus {
          border-color: #2563eb;
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        .login-btn-primary {
          background: #0f172a;
          color: #ffffff;
          border: none;
          border-radius: 8px;
          padding: 12px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          margin-top: 8px;
          transition: background 0.2s;
        }
        .login-btn-primary:hover:not(:disabled) {
          background: #1e293b;
        }
        .login-btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        .quick-login-section {
          margin-top: 24px;
          padding-top: 18px;
          border-top: 1px dashed #e2e8f0;
          text-align: center;
        }
        .quick-login-title {
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          color: #94a3b8;
          letter-spacing: 0.5px;
          margin-bottom: 10px;
        }
        .quick-login-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          justify-content: center;
        }
        .chip-btn {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 20px;
          padding: 6px 12px;
          font-size: 12px;
          font-weight: 500;
          color: #475569;
          cursor: pointer;
          transition: all 0.15s;
        }
        .chip-btn:hover {
          background: #e2e8f0;
          color: #0f172a;
        }
      `}</style>
    </div>
  )
}
