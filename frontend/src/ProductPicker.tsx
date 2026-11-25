import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { api, isAbort } from './bff'
import type { CatalogProduct } from './bff'
import { CLOSE, I, Icon, PENCIL } from './ui'
import './ProductPicker.css'

// The catalog holds 1,206 colour rows; the number is stated once, here, and reused by Kemampuan.
export const CATALOG_TOTAL = 1206
const MIN_CHARS = 3
const DEBOUNCE_MS = 250
const LIMIT = 20
const nf = new Intl.NumberFormat('id-ID')
const rupiah = (n: number) => `Rp ${nf.format(n)}`

interface ProductLike {
  name: string
  price: number
  price_original?: number | null
  colors: string[]
  category: string
}

// The 12 suggestions that used to be chips, now in the shape the listbox renders.
const POPULAR: ProductLike[] = [
  { name: 'Oversize Long Sleeve Checks Blazer', price: 299900, colors: ['DUSTY OLIVE'], category: 'Outerwear & Jackets' },
  { name: 'Double Breasted Crop Jacket', price: 329900, colors: ['LT. GREY'], category: 'Outerwear & Jackets' },
  { name: 'Contrast Detail Denim Jacket', price: 359900, colors: ['DARK BROWN'], category: 'Outerwear & Jackets' },
  { name: 'Oversize Collared Leather Jacket', price: 599900, colors: ['DARK RED'], category: 'Outerwear & Jackets' },
  { name: 'Bubble Hem Long Sleeve Hoodie', price: 299900, colors: ['ECRU'], category: 'Outerwear & Jackets' },
  { name: 'Suede Mini Skirt', price: 249900, colors: ['NAVY'], category: 'Bottoms (Celana & Rok)' },
  { name: 'Jeans with Overlap Micro Skirt Details', price: 237528, colors: ['DARK NAVY'], category: 'Denim' },
  { name: 'Wide Leg Drawstring Pants', price: 199900, colors: ['NAVY'], category: 'Bottoms (Celana & Rok)' },
  { name: 'Denim Sling Bag', price: 129900, colors: ['DENIM'], category: 'Aksesoris & Tas' },
  { name: 'Lace Sneakers', price: 299900, colors: ['NAVY'], category: 'Aksesoris & Tas' },
  { name: 'Contrast Stitch Chambray Shirt', price: 140900, colors: ['DARK BLUE'], category: 'Tops (Atasan)' },
  { name: 'High Waist Barrel Denim Pants', price: 329900, colors: ['BLACK'], category: 'Denim' },
]

type Picked = { kind: 'catalog' | 'custom'; label: string; sub?: string }

const FORMATTED = /^(.+?) \(Rp ([\d.]+)(?:, harga normal Rp ([\d.]+))? - (.+)\)$/
// A value set from outside (the Colorbox sample, a reset) is shown honestly as our own text, never as catalog-checked.
function derive(v: string): Picked {
  const m = v.match(FORMATTED)
  if (m) return { kind: 'custom', label: m[1], sub: `${m[4]} · Rp ${m[2]}` }
  return { kind: 'custom', label: v }
}

const briefValue = (p: ProductLike) =>
  `${p.name} (Rp ${nf.format(p.price)}${p.price_original ? `, harga normal Rp ${nf.format(p.price_original)}` : ''} - ${p.colors.join('/')})`

export default function ProductPicker({ id, value, onChange, error }: { id: string; value: string; onChange: (v: string) => void; error?: string }) {
  const [picked, setPicked] = useState<Picked | null>(() => (value.trim() ? derive(value) : null))
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [results, setResults] = useState<CatalogProduct[] | null>(null)
  const [searchedQ, setSearchedQ] = useState('')
  const [loading, setLoading] = useState(false)
  const [failed, setFailed] = useState(false)
  const [retry, setRetry] = useState(0)
  const [live, setLive] = useState('')
  const [popMax, setPopMax] = useState(0)
  const wrapRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const changeRef = useRef<HTMLButtonElement>(null)
  const lastValue = useRef(value)
  const cache = useRef(new Map<string, CatalogProduct[]>())
  const abort = useRef<AbortController | null>(null)
  const focusChange = useRef(false)
  const selectAll = useRef(false)

  const trimmed = q.trim()
  const popular = trimmed.length < MIN_CHARS
  const searching = !popular
  const options: (ProductLike | 'own')[] = popular ? [...POPULAR] : [...(results ?? [])]
  if (trimmed) options.push('own')
  const optionCount = options.length
  const noResults = searching && !loading && (failed || (results !== null && results.length === 0))
  // "0 produk untuk …" above an empty-state title says nothing: hide it when the search came back empty.
  const hideSub = noResults && !failed

  // Keep the chosen card in step when the value changes from outside ("Isi contoh Colorbox", a reset).
  useEffect(() => {
    if (value === lastValue.current) return
    lastValue.current = value
    setOpen(false)
    setActive(-1)
    setQ('')
    setPicked(value.trim() ? derive(value) : null)
  }, [value])

  // The popup never runs off the viewport: put the field at the top of the page when the space below is
  // cramped, then cap the popup so one scroll inside .pp-list reaches every row (including "tulis sendiri").
  useLayoutEffect(() => {
    if (!open) return
    const el = inputRef.current
    if (!el) return
    const measure = () => {
      const box = el.getBoundingClientRect()
      setPopMax(Math.max(200, Math.floor(window.innerHeight - box.bottom - 20)))
    }
    const fit = () => {
      let box = el.getBoundingClientRect()
      if (window.innerHeight - box.bottom - 20 < 400) {
        el.scrollIntoView({ block: 'start' })
        box = el.getBoundingClientRect()
      }
      setPopMax(Math.max(200, Math.floor(window.innerHeight - box.bottom - 20)))
    }
    // The browser's own focus scroll can land a frame later, and opening the popup can nudge the page:
    // re-measure on any scroll so the popup never hangs past the bottom edge.
    let raf = 0
    const onScroll = () => {
      cancelAnimationFrame(raf)
      raf = requestAnimationFrame(measure)
    }
    fit()
    raf = requestAnimationFrame(measure)
    document.addEventListener('scroll', onScroll, true)
    window.addEventListener('resize', fit)
    return () => {
      cancelAnimationFrame(raf)
      document.removeEventListener('scroll', onScroll, true)
      window.removeEventListener('resize', fit)
    }
  }, [open])

  useEffect(() => {
    if (!open || picked) return
    abort.current?.abort()
    if (popular) {
      setLoading(false)
      setFailed(false)
      return
    }
    const key = trimmed.toLowerCase().replace(/\s+/g, ' ')
    const cached = cache.current.get(key)
    if (cached) {
      setResults(cached)
      setSearchedQ(trimmed)
      setLoading(false)
      setFailed(false)
      return
    }
    const ctrl = new AbortController()
    abort.current = ctrl
    setLoading(true)
    setFailed(false)
    setLive('Mencari…')
    const timer = window.setTimeout(() => {
      api.productsSearch(trimmed, ctrl.signal).then(
        (r) => {
          if (ctrl.signal.aborted) return
          const data = (r.data ?? []).slice(0, LIMIT)
          cache.current.set(key, data)
          setResults(data)
          setSearchedQ(trimmed)
          setLoading(false)
          setLive(
            !data.length
              ? `Tidak ada produk untuk “${trimmed}”.`
              : `${data.length === LIMIT ? `${LIMIT} produk teratas` : `${data.length} produk`} untuk “${trimmed}”`,
          )
        },
        (e) => {
          if (ctrl.signal.aborted || isAbort(e)) return
          setResults([])
          setSearchedQ(trimmed)
          setLoading(false)
          setFailed(true)
          setLive('Daftar produk belum bisa dimuat.')
        },
      )
    }, DEBOUNCE_MS)
    return () => {
      window.clearTimeout(timer)
      ctrl.abort()
    }
  }, [open, picked, popular, trimmed, retry])

  // A new query starts a new position in the list.
  useEffect(() => {
    setActive(-1)
  }, [trimmed, results])

  useEffect(() => {
    if (!open || active < 0) return
    document.getElementById(`${id}-o${active}`)?.scrollIntoView({ block: 'nearest' })
  }, [active, open, id])

  useEffect(() => {
    if (!picked || !focusChange.current) return
    changeRef.current?.focus()
    focusChange.current = false
  }, [picked])

  useEffect(() => {
    if (picked || !selectAll.current || !inputRef.current) return
    inputRef.current.focus()
    inputRef.current.select()
    selectAll.current = false
  }, [picked])

  function emit(v: string) {
    lastValue.current = v
    onChange(v)
  }

  function openPopup() {
    setOpen(true)
    setActive(-1)
  }

  function pickProduct(p: ProductLike) {
    emit(briefValue(p))
    setPicked({ kind: 'catalog', label: p.name, sub: `${p.colors.join('/') || '—'} · ${rupiah(p.price)}` })
    setOpen(false)
    setQ('')
    setLive(`Dipilih: ${p.name}, ${p.colors.join(', ')}, ${rupiah(p.price)}`)
    focusChange.current = true
  }

  function pickOwn(focusAfter: boolean) {
    const text = q.trim()
    if (!text) return
    emit(text)
    setPicked({ kind: 'custom', label: text })
    setOpen(false)
    setQ('')
    setLive(`Ditulis sendiri: ${text}`)
    if (focusAfter) focusChange.current = true
  }

  function chooseAgain() {
    if (!picked) return
    selectAll.current = true
    setQ(picked.label)
    setPicked(null)
    openPopup()
  }

  function clearPicked() {
    emit('')
    setPicked(null)
    setQ('')
    setOpen(true)
    requestAnimationFrame(() => inputRef.current?.focus())
  }

  function clearText() {
    setQ('')
    setResults(null)
    setSearchedQ('')
    setActive(-1)
    requestAnimationFrame(() => inputRef.current?.focus())
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (!open) return openPopup()
      setActive((a) => (a < 0 ? 0 : Math.min(a + 1, optionCount - 1)))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (!open) return openPopup()
      setActive((a) => (a < 0 ? optionCount - 1 : Math.max(0, a - 1)))
    } else if (e.key === 'Home' && open) {
      e.preventDefault()
      setActive(0)
    } else if (e.key === 'End' && open) {
      e.preventDefault()
      setActive(optionCount - 1)
    } else if (e.key === 'Enter') {
      e.preventDefault() // never submit the brief from inside the picker
      if (!open) {
        if (trimmed.length >= 2) pickOwn(true)
        return
      }
      const chosen = active >= 0 ? options[active] : undefined
      if (chosen === 'own') pickOwn(true)
      else if (chosen) pickProduct(chosen)
      else if (trimmed.length >= 2) pickOwn(true)
    } else if (e.key === 'Escape') {
      if (open) {
        e.preventDefault()
        setOpen(false)
        setActive(-1)
      } else if (q) {
        e.preventDefault()
        clearText()
      }
    }
  }

  function onBlur(e: React.FocusEvent<HTMLDivElement>) {
    if (e.currentTarget.contains(e.relatedTarget as Node | null)) return
    if (open) {
      setOpen(false)
      setActive(-1)
    }
    if (q.trim()) pickOwn(false)
  }

  const sub = popular
    ? 'Contoh populer'
    : failed
      ? 'Pencarian gagal'
      : loading && results === null
        ? 'Mencari…'
        : `${(results ?? []).length === LIMIT ? `${LIMIT} produk teratas` : `${(results ?? []).length} produk`} untuk “${searchedQ}”`

  if (picked) {
    return (
      <div className="field pp" data-state="chosen" ref={wrapRef}>
        <span className="pp-label" id={`${id}-lab`}>
          Produk acuan
        </span>
        <div className="pp-chosen" data-kind={picked.kind} role="group" aria-labelledby={`${id}-lab`}>
          <span className="pp-chosen-ico">
            <Icon d={picked.kind === 'catalog' ? I.check : PENCIL} size={20} />
          </span>
          <div className="pp-chosen-body">
            <b className="pp-chosen-name">{picked.label}</b>
            {picked.sub && <span className="pp-chosen-sub num">{picked.sub}</span>}
            <span className={`pill ${picked.kind === 'catalog' ? 'ok' : 'plain'}`}>
              {picked.kind === 'catalog' ? 'Dari katalog resmi' : 'Tulisan sendiri, tidak dicek ke katalog'}
            </span>
          </div>
          <div className="pp-chosen-act">
            <button type="button" className="btn soft sm" id={`${id}-change`} ref={changeRef} onClick={chooseAgain}>
              Ganti
            </button>
            <button type="button" className="icon-btn" aria-label="Hapus produk acuan" onClick={clearPicked}>
              <Icon d={CLOSE} />
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      className="field pp"
      data-state="search"
      data-invalid={error || undefined}
      ref={wrapRef}
      onBlur={onBlur}
    >
      <label className="pp-label" htmlFor={id}>
        Produk acuan
      </label>
      <p className="pp-help" id={`${id}-help`}>
        Cari di {nf.format(CATALOG_TOTAL)} produk katalog resmi Colorbox. Ketik nama dalam bahasa Inggris, misalnya <b>denim</b>, <b>blazer</b>,{' '}
        <b>skirt</b>. Pilih satu dari daftar, atau tulis sendiri.
      </p>
      <div className="pp-box">
        <svg className="pp-ico" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" aria-hidden="true">
          <circle cx="11" cy="11" r="7" />
          <path d="m16 16 4 4" />
        </svg>
        <input
          ref={inputRef}
          id={id}
          className="pp-input"
          role="combobox"
          type="text"
          autoComplete="off"
          spellCheck={false}
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={`${id}-list`}
          aria-describedby={`${id}-help ${id}-err`}
          aria-invalid={error ? true : false}
          aria-activedescendant={open && active >= 0 ? `${id}-o${active}` : undefined}
          placeholder="Ketik nama produk…"
          value={q}
          onChange={(e) => {
            setQ(e.target.value)
            setOpen(true)
          }}
          onFocus={() => {
            openPopup()
          }}
          onKeyDown={onKeyDown}
        />
        <button type="button" className="pp-clear icon-btn" aria-label="Hapus tulisan" tabIndex={-1} hidden={!q} onClick={clearText}>
          <Icon d={CLOSE} />
        </button>
        <div className="pp-pop" hidden={!open} style={popMax ? { maxHeight: popMax } : undefined}>
          {!hideSub && (
            <div className="pp-sub" id={`${id}-sub`}>
              {sub}
            </div>
          )}
          {noResults ? (
            <>
              <div className="pp-empty">
                {failed ? (
                  <>
                    <b>Daftar produk belum bisa dimuat.</b>
                    <button
                      type="button"
                      className="btn link"
                      tabIndex={-1}
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => {
                        setResults(null)
                        setFailed(false)
                        setRetry((n) => n + 1)
                      }}
                    >
                      Coba lagi
                    </button>
                    <span className="quiet">Anda tetap bisa menulis nama produk sendiri.</span>
                  </>
                ) : (
                  <>
                    <b>Tidak ada produk untuk “{searchedQ}”.</b>
                    <span>Katalog memakai nama Inggris. Coba:</span>
                    <span className="pp-words">
                      {['jacket', 'shirt', 'pants', 'skirt', 'bag'].map((w) => (
                        <button key={w} type="button" className="btn link" tabIndex={-1} onMouseDown={(e) => e.preventDefault()} onClick={() => setQ(w)}>
                          {w}
                        </button>
                      ))}
                    </span>
                  </>
                )}
              </div>
              {trimmed && (
                <ul className="pp-list" id={`${id}-list`} role="listbox" aria-labelledby={hideSub ? undefined : `${id}-sub`} aria-label={hideSub ? 'Produk acuan' : undefined}>
                  <li
                    className="pp-opt pp-opt-own"
                    role="option"
                    id={`${id}-o0`}
                    aria-selected={active === 0}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => pickOwn(true)}
                  >
                    <span>
                      Pakai tulisan saya: <b>“{trimmed}”</b>
                    </span>
                    <span className="pp-meta">tidak dicek ke katalog</span>
                  </li>
                </ul>
              )}
            </>
          ) : (
            <ul
              className={`pp-list${loading && results !== null ? ' pp-stale' : ''}`}
              id={`${id}-list`}
              role="listbox"
              aria-labelledby={hideSub ? undefined : `${id}-sub`}
              aria-label={hideSub ? 'Produk acuan' : undefined}
              aria-busy={loading || undefined}
            >
              {loading && results === null ? (
                [0, 1, 2].map((i) => (
                  <li key={i} className="pp-skel" aria-hidden="true">
                    <i />
                    <i />
                  </li>
                ))
              ) : (
                <>
                  {options.map((o, i) =>
                    o === 'own' ? (
                      <li
                        key="own"
                        className="pp-opt pp-opt-own"
                        role="option"
                        id={`${id}-o${i}`}
                        aria-selected={active === i}
                        onMouseDown={(e) => e.preventDefault()}
                        onClick={() => pickOwn(true)}
                      >
                        <span>
                          Pakai tulisan saya: <b>“{trimmed}”</b>
                        </span>
                        <span className="pp-meta">tidak dicek ke katalog</span>
                      </li>
                    ) : (
                      <li
                        key={`${o.name}-${o.colors.join('/')}-${i}`}
                        className="pp-opt"
                        role="option"
                        id={`${id}-o${i}`}
                        aria-selected={active === i}
                        onMouseDown={(e) => e.preventDefault()}
                        onClick={() => pickProduct(o)}
                      >
                        <span className="pp-name">{o.name}</span>
                        <span className="pp-price num">{rupiah(o.price)}</span>
                        <span className="pp-meta">{[o.category, o.colors.join(', ')].filter(Boolean).join(' · ')}</span>
                        {o.price_original ? <s className="pp-was num">{rupiah(o.price_original)}</s> : null}
                      </li>
                    ),
                  )}
                </>
              )}
            </ul>
          )}
          {!popular && !loading && !failed && (results?.length ?? 0) === LIMIT && (
            <div className="pp-foot" role="status">
              Menampilkan 20 produk pertama. Ketik lebih spesifik untuk mempersempit.
            </div>
          )}
        </div>
      </div>
      <small className="field-err" id={`${id}-err`} role="alert">
        {error}
      </small>
      <div className="sr" role="status" aria-live="polite" id={`${id}-live`}>
        {live}
      </div>
    </div>
  )
}
