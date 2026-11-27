// Pengaturan > Akun AI: the person's own AI accounts. One row per provider, one clear next step.
// Nothing here calls a model directly: the screen only stores, tests, and removes keys, and the tier picker in the
// Atur dialog reads the same list through OWN_SLUGS.

import { useEffect, useRef, useState } from 'react'
import { AI_KEY_PROVIDERS, api, errText } from './bff'
import type { AiProvider, AiProviderId, AiUnavailable } from './bff'
import { useAdminMode } from './adminMode'
import { useData } from './data'
import { ErrorLine } from './ui'
import { CapChip, Loading } from './ui-extra'
import './ai-accounts.css'

type KeyProvider = (typeof AI_KEY_PROVIDERS)[number]

// Fixed order and exact wording for the five key providers. The link opens in a new tab; the hint never names a
// technical detail that a business owner would have to look up.
const PROVIDERS: { id: KeyProvider; name: string; hint: string; where: string }[] = [
  { id: 'anthropic', name: 'Anthropic (Claude)', hint: 'Kunci akses dari akun Anthropic Anda. Untuk memakai Claude.', where: 'https://console.anthropic.com/settings/keys' },
  { id: 'openai', name: 'OpenAI (GPT)', hint: 'Kunci akses dari akun OpenAI Anda. Untuk memakai GPT.', where: 'https://platform.openai.com/api-keys' },
  { id: 'gemini', name: 'Google Gemini', hint: 'Kunci akses dari Google AI Studio. Untuk memakai Gemini.', where: 'https://aistudio.google.com/app/apikey' },
  { id: 'opencode-zen', name: 'OpenCode Zen', hint: 'Kunci akses OpenCode Zen. Bayar sesuai pemakaian.', where: 'https://opencode.ai' },
  { id: 'opencode-go', name: 'OpenCode Go', hint: 'Kunci akses langganan OpenCode Go.', where: 'https://opencode.ai' },
]

const NAMES: Record<string, string> = {
  openrouter: 'OpenRouter',
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  gemini: 'Google Gemini',
  'opencode-zen': 'OpenCode Zen',
  'opencode-go': 'OpenCode Go',
}

// Ways of signing in that the providers do not allow through another app. The reason always says the way that works.
const OFF_FALLBACK: Record<string, { title: string; reason: string }> = {
  'claude-subscription': {
    title: 'Langganan Claude (Pro/Max)',
    reason: 'Anthropic tidak mengizinkan langganan pribadi dipakai di aplikasi lain. Pakai kunci akses Anthropic di atas.',
  },
  'chatgpt-subscription': {
    title: 'Login ChatGPT',
    reason: 'OpenAI mensyaratkan login ChatGPT disimpan di perangkat Anda sendiri, bukan di server aplikasi. Pakai kunci akses OpenAI di atas.',
  },
  copilot: { title: 'GitHub Copilot', reason: 'GitHub Copilot belum menyediakan sambungan untuk aplikasi lain.' },
}
const OFF_ORDER = Object.keys(OFF_FALLBACK)

const CONNECT_KEY = 'pa.ai-connecting'
const NOT_CONNECTED = 'OpenRouter belum tersambung. Coba lagi; jika terus gagal, hubungi admin Anda.'

type Notice = { kind: 'ok' | 'bad'; text: string }
type Return = 'ok' | 'error' | 'unknown'

// Returning from OpenRouter: the BFF redirects to #/pengaturan/akun-ai, and (once it does) may append ?connect=ok|error.
// The URL is the only durable signal; a marker covers the time between "leave" and "come back". Both are consumed once
// so a refresh never repeats an old message.
function takeReturn(): Return | null {
  const hint = new URLSearchParams(location.hash.split('?')[1] ?? '').get('connect')
  let marker = ''
  try {
    marker = sessionStorage.getItem(CONNECT_KEY) ?? ''
    if (marker) sessionStorage.removeItem(CONNECT_KEY)
  } catch {
    /* private mode: the URL is still the only signal */
  }
  const back = hint === 'ok' || hint === 'error' ? hint : marker ? 'unknown' : null
  if (back)
    try {
      history.replaceState(null, '', `${location.pathname}${location.search}#/pengaturan/akun-ai`)
    } catch {
      /* the message still shows; only the URL keeps its query */
    }
  return back
}

// Initial in a soft circle (same pattern as connections.tsx); the hue comes from the name, so it never changes.
function Initial({ name }: { name: string }) {
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) % 360
  return (
    <span className="app-initial" style={{ ['--hue' as string]: h }} aria-hidden="true">
      {name.charAt(0).toUpperCase()}
    </span>
  )
}

const checkedText = (sec: number) => new Date(sec * 1000).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })

export function AiAccounts() {
  const admin = useAdminMode()
  const { flash } = useData()
  const [rows, setRows] = useState<AiProvider[]>([])
  const [off, setOff] = useState<AiUnavailable[]>([])
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [notice, setNotice] = useState<Notice | null>(null)
  const [retryN, setRetryN] = useState(0)
  const [busy, setBusy] = useState('')
  const [formFor, setFormFor] = useState<AiProviderId | null>(null)
  const [key, setKey] = useState('')
  const [keyErr, setKeyErr] = useState('')
  const [asking, setAsking] = useState<AiProviderId | null>(null)
  const input = useRef<HTMLInputElement>(null)
  const refocus = useRef(false)
  const back = useRef<Return | null | undefined>(undefined)
  const checked = useRef(false)

  const retry = () => {
    setState('loading')
    setRetryN((x) => x + 1)
  }

  // First load, and every retry. The return from OpenRouter is read once per mount and announced after the fresh list
  // arrives, so the message matches what the rows show.
  useEffect(() => {
    if (!checked.current) {
      checked.current = true
      back.current = takeReturn()
    }
    let live = true
    api.aiAccounts().then(
      (a) => {
        if (!live) return
        setRows(a.providers)
        setOff(a.unavailable)
        setState('ok')
        const r = back.current
        back.current = null
        if (r) {
          const or = a.providers.find((p) => p.id === 'openrouter')
          setNotice(r !== 'error' && or?.connected ? { kind: 'ok', text: 'OpenRouter tersambung.' } : { kind: 'bad', text: NOT_CONNECTED })
        }
      },
      () => {
        if (!live) return
        setState('error')
        if (back.current) {
          back.current = null
          setNotice({ kind: 'bad', text: NOT_CONNECTED })
        }
      },
    )
    return () => {
      live = false
    }
  }, [retryN])

  // The mock (and an OAuth page that returns without a reload) changes only the hash: finish the job without remounting.
  useEffect(() => {
    const onHash = () => {
      const r = takeReturn()
      if (!r) return
      setBusy('openrouter')
      setNotice(null)
      api.aiAccounts().then(
        (a) => {
          setRows(a.providers)
          setOff(a.unavailable)
          setState('ok')
          const or = a.providers.find((p) => p.id === 'openrouter')
          setNotice(r !== 'error' && or?.connected ? { kind: 'ok', text: 'OpenRouter tersambung.' } : { kind: 'bad', text: NOT_CONNECTED })
        },
        () => setNotice({ kind: 'bad', text: NOT_CONNECTED }),
      ).finally(() => setBusy(''))
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  // Opening a key form moves the caret into it; the row itself stays readable.
  useEffect(() => {
    if (formFor) input.current?.focus()
  }, [formFor])

  // A rejected key keeps the form open and empty with the caret back in the field, but only once the field is
  // enabled again (a disabled input cannot take focus).
  useEffect(() => {
    if (!refocus.current || !formFor || busy === formFor) return
    refocus.current = false
    input.current?.focus()
  }, [formFor, busy, keyErr])

  const patch = (id: AiProviderId, p: Partial<AiProvider>) => setRows((xs) => xs.map((x) => (x.id === id ? { ...x, ...p } : x)))

  async function connect() {
    setBusy('openrouter')
    setNotice(null)
    try {
      const { url } = await api.openrouterStart()
      try {
        sessionStorage.setItem(CONNECT_KEY, 'openrouter')
      } catch {
        /* the URL hint, when the BFF sends one, is enough */
      }
      window.location.assign(url)
    } catch (e) {
      setNotice({ kind: 'bad', text: errText(e) })
      setBusy('')
    }
  }

  async function test(id: AiProviderId) {
    const name = NAMES[id] ?? id
    setBusy(id)
    setNotice(null)
    try {
      const r = await api.testAiAccount(id)
      patch(id, { status: r.status, connected: true })
      if (r.status === 'ok') flash(`${name}: koneksi baik`)
      else setNotice({ kind: 'bad', text: `${name} tidak menerima kunci ini. ${id === 'openrouter' ? 'Sambungkan ulang akun Anda.' : 'Ganti kuncinya.'}` })
    } catch (e) {
      setNotice({ kind: 'bad', text: errText(e) })
    } finally {
      setBusy('')
    }
  }

  function openForm(id: AiProviderId) {
    setFormFor(id)
    setKey('')
    setKeyErr('')
    setAsking(null)
  }

  async function saveKey(id: KeyProvider) {
    const name = NAMES[id] ?? id
    const value = key.trim()
    if (!value || busy) return
    setKey('') // the key never stays in the state after sending
    setKeyErr('')
    setBusy(id)
    try {
      const r = await api.saveAiKey(id, value)
      patch(id, { connected: true, status: 'ok', last4: r.last4, method: 'api_key' })
      setFormFor(null)
      flash(`${name} tersambung`)
      setNotice({ kind: 'ok', text: `${name} tersambung` })
    } catch (e) {
      setKeyErr(errText(e))
      refocus.current = true
    } finally {
      setBusy('')
    }
  }

  async function remove(id: AiProviderId) {
    setBusy(id)
    setNotice(null)
    try {
      await api.removeAiAccount(id)
      setAsking(null)
      const a = await api.aiAccounts()
      setRows(a.providers)
      setOff(a.unavailable)
      setState('ok')
    } catch (e) {
      setNotice({ kind: 'bad', text: errText(e) })
    } finally {
      setBusy('')
    }
  }

  if (state === 'loading')
    return (
      <div className="set-sec">
        <h2 className="set-h">Akun AI</h2>
        <Loading text="Memuat akun AI..." shape="ledger" rows={4} />
      </div>
    )

  if (state === 'error')
    return (
      <div className="set-sec">
        <h2 className="set-h">Akun AI</h2>
        <ErrorLine text="Akun AI belum bisa dimuat. Coba lagi sebentar." onRetry={retry} />
      </div>
    )

  const or = rows.find((p) => p.id === 'openrouter')
  const invalid = rows.filter((p) => p.connected && p.status === 'invalid')
  const invalidText =
    invalid.length === 1
      ? `Satu akun perlu diperiksa: ${NAMES[invalid[0].id] ?? invalid[0].id}. Pegawai yang memakainya sementara memakai pilihan bawaan.`
      : invalid.length > 1
        ? `Beberapa akun perlu diperiksa: ${invalid.map((p) => NAMES[p.id] ?? p.id).join(', ')}. Pegawai yang memakainya sementara memakai pilihan bawaan.`
        : ''
  const extraOff = off.filter((u) => !OFF_ORDER.includes(u.id))

  const confirm = (id: AiProviderId, name: string) => (
    <span className="confirm-actions" role="alert">
      <span className="ai-ask">
        Putuskan {name}? Pegawai yang memakai akun ini kembali ke pilihan bawaan.
      </span>
      <button type="button" className="btn danger" disabled={busy === id} onClick={() => void remove(id)}>
        Putuskan
      </button>
      <button type="button" className="btn quiet-btn" onClick={() => setAsking(null)}>
        Batal
      </button>
    </span>
  )

  return (
    <div className="set-sec">
      <h2 className="set-h">Akun AI</h2>
      <p className="quiet">Pakai akun AI milik Anda sendiri. Biaya pemakaian ditagih langsung oleh penyedianya kepada Anda, bukan lewat paket Pegawai AI.</p>
      {notice &&
        (notice.kind === 'ok' ? (
          <p className="note-box connect-ok" role="status">
            {notice.text}
          </p>
        ) : (
          <p className="problem-bar" role="alert">
            {notice.text}
          </p>
        ))}
      {invalidText && <p className="note-box">{invalidText}</p>}

      <section className="ai-sec" aria-labelledby="ai-quick">
        <h3 id="ai-quick">Sambungan cepat</h3>
        <div className="set-row ai-row">
          <div className="set-text">
            <div className="ai-brand">
              <div className="app-mark ai-or">
                <Initial name="OpenRouter" />
              </div>
              <div className="ai-name">
                <b>OpenRouter</b>
                <small className="quiet">Satu akun untuk banyak AI sekaligus, termasuk Claude dan GPT. Klik, masuk, selesai.</small>
              </div>
            </div>
          </div>
          <div className="ai-state">
            {or?.connected &&
              (or.status === 'invalid' ? (
                <>
                  <span className="pill bad">Perlu disambungkan ulang</span>
                  <span>Kunci ini tidak lagi diterima.</span>
                </>
              ) : (
                <>
                  <span className="pill ok">Tersambung</span>
                  {or.last4 && <span className="num">Kunci berakhir …{or.last4}</span>}
                </>
              ))}
          </div>
          <div className="set-ctl ai-act">
            {asking === 'openrouter' ? (
              confirm('openrouter', 'OpenRouter')
            ) : or?.connected ? (
              or.status === 'invalid' ? (
                <>
                  <button type="button" className="btn primary" disabled={busy === 'openrouter'} onClick={() => void connect()}>
                    {busy === 'openrouter' ? 'Membuka OpenRouter…' : 'Sambungkan ulang'}
                  </button>
                  <button type="button" className="btn link" onClick={() => setAsking('openrouter')}>
                    Putuskan
                  </button>
                </>
              ) : (
                <>
                  <button type="button" className="btn soft" disabled={busy === 'openrouter'} onClick={() => void test('openrouter')}>
                    {busy === 'openrouter' ? 'Memeriksa…' : 'Tes koneksi'}
                  </button>
                  <button type="button" className="btn link" onClick={() => setAsking('openrouter')}>
                    Putuskan
                  </button>
                </>
              )
            ) : (
              <button type="button" className="btn primary" disabled={busy === 'openrouter'} onClick={() => void connect()}>
                {busy === 'openrouter' ? 'Membuka OpenRouter…' : 'Sambungkan OpenRouter'}
              </button>
            )}
          </div>
        </div>
      </section>

      <section className="ai-sec" aria-labelledby="ai-keys">
        <h3 id="ai-keys">Kunci akses</h3>
        {PROVIDERS.map((meta) => {
          const p = rows.find((r) => r.id === meta.id)
          const connected = p?.connected === true
          const bad = connected && p?.status === 'invalid'
          const open = formFor === meta.id
          const inputId = `ai-key-input-${meta.id}`
          const helpId = `ai-key-help-${meta.id}`
          const errId = `ai-key-err-${meta.id}`
          return (
            <div className="set-row ai-row" key={meta.id}>
              <div className="set-text">
                <b>{meta.name}</b>
                <small className="quiet">{meta.hint}</small>
                {admin && (
                  <span className="admin-tag">
                    {meta.id} · {p?.method ?? 'api_key'}
                    {p?.checked_at ? ` · ${checkedText(p.checked_at)}` : ''}
                  </span>
                )}
              </div>
              <div className="ai-state">
                {bad ? (
                  <span className="pill bad">Kunci tidak diterima</span>
                ) : connected ? (
                  <>
                    <span className="pill ok">Tersambung</span>
                    {p?.last4 && <span className="num">Kunci berakhir …{p.last4}</span>}
                  </>
                ) : null}
              </div>
              {!open && (
                <div className="set-ctl ai-act">
                  {asking === meta.id ? (
                    confirm(meta.id, meta.name)
                  ) : bad ? (
                    <>
                      <button type="button" className="btn primary" onClick={() => openForm(meta.id)}>
                        Ganti kunci
                      </button>
                      <button type="button" className="btn soft" disabled={busy === meta.id} onClick={() => void test(meta.id)}>
                        {busy === meta.id ? 'Memeriksa…' : 'Tes koneksi'}
                      </button>
                      <button type="button" className="btn link" onClick={() => setAsking(meta.id)}>
                        Putuskan
                      </button>
                    </>
                  ) : connected ? (
                    <>
                      <button type="button" className="btn soft" disabled={busy === meta.id} onClick={() => void test(meta.id)}>
                        {busy === meta.id ? 'Memeriksa…' : 'Tes koneksi'}
                      </button>
                      <button type="button" className="btn link" onClick={() => openForm(meta.id)}>
                        Ganti kunci
                      </button>
                      <button type="button" className="btn link" onClick={() => setAsking(meta.id)}>
                        Putuskan
                      </button>
                    </>
                  ) : (
                    <button type="button" className="btn soft" aria-expanded={false} aria-controls={`ai-key-${meta.id}`} onClick={() => openForm(meta.id)}>
                      Tambah kunci
                    </button>
                  )}
                </div>
              )}
              <div className="ai-key-wrap" id={`ai-key-${meta.id}`}>
                {open && (
                  <form
                    className="ai-form"
                    noValidate
                    onSubmit={(e) => {
                      e.preventDefault()
                      void saveKey(meta.id)
                    }}
                  >
                  <div className="field">
                    <span id={`ai-key-label-${meta.id}`}>Kunci akses {meta.name}</span>
                    <input
                      id={inputId}
                      ref={input}
                      type="password"
                      value={key}
                      autoComplete="off"
                      spellCheck={false}
                      autoCapitalize="off"
                      data-lpignore="true"
                      name={`ai-key-${meta.id}`}
                      aria-labelledby={`ai-key-label-${meta.id}`}
                      aria-invalid={!!keyErr}
                      aria-describedby={`${helpId}${keyErr ? ` ${errId}` : ''}`}
                      disabled={busy === meta.id}
                      onChange={(e) => setKey(e.target.value)}
                    />
                    <small className="quiet" id={helpId}>
                      Kunci diperiksa dulu sebelum disimpan.
                    </small>
                    {keyErr && (
                      <small className="err" id={errId} role="alert">
                        {keyErr}
                      </small>
                    )}
                  </div>
                  <a className="btn link small" href={meta.where} target="_blank" rel="noopener noreferrer">
                    Di mana mendapatkan kunci?
                  </a>
                  <div className="ai-form-act">
                    <button type="submit" className="btn primary" disabled={busy === meta.id || !key.trim()}>
                      {busy === meta.id ? 'Memeriksa…' : 'Simpan dan tes'}
                    </button>
                    <button type="button" className="btn quiet-btn" disabled={busy === meta.id} onClick={() => setFormFor(null)}>
                      Batal
                    </button>
                  </div>
                  </form>
                )}
              </div>
            </div>
          )
        })}
      </section>

      <section className="ai-sec" aria-labelledby="ai-off">
        <h3 id="ai-off">Belum tersedia</h3>
        {OFF_ORDER.map((id) => {
          const meta = OFF_FALLBACK[id]
          const reason = off.find((u) => u.id === id)?.reason || meta.reason
          return (
            <div className="set-row ai-row" key={id}>
              <div className="set-text">
                <b>{meta.title}</b>
                <small className="quiet">{reason}</small>
              </div>
              <div className="ai-state">
                <CapChip cap="none" label="Belum tersedia" />
              </div>
            </div>
          )
        })}
        {extraOff.map((u) => (
          <div className="set-row ai-row" key={u.id}>
            <div className="set-text">
              <b>{admin ? u.id : 'Layanan lain'}</b>
              <small className="quiet">{u.reason || 'Belum bisa disambungkan saat ini.'}</small>
            </div>
            <div className="ai-state">
              <CapChip cap="none" label="Belum tersedia" />
            </div>
          </div>
        ))}
      </section>

      <p className="quiet small">Kunci disimpan terenkripsi dan tidak pernah ditampilkan lagi. Hanya 4 karakter terakhir yang terlihat.</p>
    </div>
  )
}
