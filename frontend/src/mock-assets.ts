// Sample files for mock mode only (`npm run dev:mock`). Everything is created in memory, so the repository
// holds no binary fixtures. Imported only from mock-api.ts, which production builds never include.

const enc = new TextEncoder()

// A renderer that fails the way an HTTP endpoint would (415): mock-api turns this into an ApiError.
export class MockAssetError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function canvas2d(w: number, h: number): { canvas: HTMLCanvasElement | OffscreenCanvas; ctx: CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D } {
  if (typeof OffscreenCanvas !== 'undefined') {
    const canvas = new OffscreenCanvas(w, h)
    const ctx = canvas.getContext('2d')
    if (ctx) return { canvas, ctx }
  }
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new MockAssetError(500, 'Kanvas contoh tidak bisa dibuat.')
  return { canvas, ctx }
}

function toPng(canvas: HTMLCanvasElement | OffscreenCanvas): Promise<Blob> {
  // The typeof guard keeps browsers without OffscreenCanvas from touching the name; the cast then narrows for TS.
  if (typeof OffscreenCanvas !== 'undefined' && canvas instanceof OffscreenCanvas) return (canvas as OffscreenCanvas).convertToBlob({ type: 'image/png' })
  const el = canvas as HTMLCanvasElement
  return new Promise((resolve, reject) => {
    el.toBlob((b) => (b ? resolve(b) : reject(new MockAssetError(500, 'Gambar contoh tidak bisa dibuat.'))), 'image/png')
  })
}

// Flat two-stop gradient with the size written on it: an obviously fake image that still fills its box.
export async function pngBlob(w: number, h: number, label: string, tone = 0): Promise<Blob> {
  const { canvas, ctx } = canvas2d(w, h)
  const pairs: [string, string][] = [
    ['#dbe7f5', '#f3e8dd'],
    ['#dfe9df', '#e6e1f4'],
    ['#f4e3e6', '#e2edf5'],
    ['#efe8d4', '#e0eef0'],
  ]
  const [a, b] = pairs[tone % pairs.length]
  const g = ctx.createLinearGradient(0, 0, w, h)
  g.addColorStop(0, a)
  g.addColorStop(1, b)
  ctx.fillStyle = g
  ctx.fillRect(0, 0, w, h)
  // A few soft circles so the crop reads as a photo, not a solid tile.
  ctx.fillStyle = 'rgb(255 255 255 / .35)'
  for (let i = 0; i < 3; i++) {
    ctx.beginPath()
    ctx.arc(w * (0.2 + i * 0.3), h * (0.25 + (i % 2) * 0.4), Math.min(w, h) * 0.16, 0, Math.PI * 2)
    ctx.fill()
  }
  const size = Math.min(w, h)
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillStyle = '#15171c'
  ctx.font = `600 ${Math.round(size * 0.075)}px "DM Sans", system-ui, sans-serif`
  ctx.fillText(label, w / 2, h / 2)
  ctx.fillStyle = '#4e5562'
  ctx.font = `400 ${Math.round(size * 0.038)}px "DM Sans", system-ui, sans-serif`
  ctx.fillText('Contoh berkas · data palsu', w / 2, h / 2 + size * 0.08)
  return toPng(canvas)
}

// 16-bit PCM mono WAV, 16 kHz: a 440 Hz sine with a short fade so playing it is not a click.
export function wavBlob(seconds = 2): Blob {
  const rate = 16000
  const samples = Math.floor(rate * seconds)
  const data = new DataView(new ArrayBuffer(44 + samples * 2))
  const ascii = (off: number, s: string) => {
    for (let i = 0; i < s.length; i++) data.setUint8(off + i, s.charCodeAt(i))
  }
  ascii(0, 'RIFF')
  data.setUint32(4, 36 + samples * 2, true)
  ascii(8, 'WAVE')
  ascii(12, 'fmt ')
  data.setUint32(16, 16, true)
  data.setUint16(20, 1, true) // PCM
  data.setUint16(22, 1, true) // mono
  data.setUint32(24, rate, true)
  data.setUint32(28, rate * 2, true)
  data.setUint16(32, 2, true)
  data.setUint16(34, 16, true)
  ascii(36, 'data')
  data.setUint32(40, samples * 2, true)
  for (let i = 0; i < samples; i++) {
    const t = i / rate
    const fade = Math.min(1, t / 0.05, (seconds - t) / 0.08)
    const v = Math.sin(2 * Math.PI * 440 * t) * 0.28 * Math.max(0, fade)
    data.setInt16(44 + i * 2, Math.round(v * 32767), true)
  }
  return new Blob([data.buffer], { type: 'audio/wav' })
}

// 2 s WebM from a canvas. Browsers without MediaRecorder or captureStream get a 415, which the card shows
// as its error state ("Video tidak bisa dimuat.") exactly as a broken file would.
export async function webmBlob(w: number, h: number, label: string): Promise<Blob> {
  if (typeof MediaRecorder === 'undefined' || typeof HTMLCanvasElement.prototype.captureStream !== 'function') {
    throw new MockAssetError(415, 'Browser ini tidak bisa membuat video contoh.')
  }
  const mime = ['video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm'].find((m) => MediaRecorder.isTypeSupported(m))
  if (!mime) throw new MockAssetError(415, 'Browser ini tidak bisa membuat video contoh.')
  // captureStream lives on a real canvas element, not on OffscreenCanvas.
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new MockAssetError(500, 'Video contoh tidak bisa dibuat.')
  const bg = (t: number) => {
    const g = ctx.createLinearGradient(0, 0, w, h)
    g.addColorStop(0, `hsl(${210 + t * 20} 45% 84%)`)
    g.addColorStop(1, `hsl(${28 + t * 18} 42% 88%)`)
    ctx.fillStyle = g
    ctx.fillRect(0, 0, w, h)
    ctx.fillStyle = '#15171c'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.font = `600 ${Math.round(Math.min(w, h) * 0.07)}px "DM Sans", system-ui, sans-serif`
    ctx.fillText(label, w / 2, h / 2)
    ctx.fillStyle = '#4e5562'
    ctx.font = `400 ${Math.round(Math.min(w, h) * 0.035)}px "DM Sans", system-ui, sans-serif`
    ctx.fillText(`Contoh video · ${(t * 2).toFixed(1)} dtk · data palsu`, w / 2, h / 2 + Math.min(w, h) * 0.075)
  }
  bg(0)
  const stream = canvas.captureStream(25)
  const rec = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: 900_000 })
  const chunks: BlobPart[] = []
  rec.ondataavailable = (e) => {
    if (e.data.size) chunks.push(e.data)
  }
  rec.start(200)
  const started = performance.now()
  const timer = window.setInterval(() => {
    bg(Math.min(1, (performance.now() - started) / 2000))
  }, 50)
  await new Promise<void>((resolve) => {
    rec.onstop = () => resolve()
    window.setTimeout(() => rec.stop(), 2000)
  })
  window.clearInterval(timer)
  stream.getTracks().forEach((t) => t.stop())
  return new Blob(chunks, { type: mime.split(';')[0] })
}

// One-page PDF 1.4 written by hand, so opening it in a tab shows a real document.
export function pdfBlob(title = 'Contoh dokumen', lines: string[] = []): Blob {
  const esc = (s: string) => s.replace(/\\/g, '\\\\').replace(/\(/g, '\\(').replace(/\)/g, '\\)')
  const body = [title, '', ...(lines.length ? lines : ['Ini contoh berkas PDF dari mode contoh Pegawai AI.', 'Isinya bukan dokumen asli dan tidak disimpan di mana pun.', '', 'Baris teks panjang dipotong agar tetap muat di halaman ini.', 'Gunakan tombol Unduh untuk menguji alur unduhan berkas.'])]
  const text = body.map((l, i) => `BT /F1 ${i === 0 ? 18 : 11} Tf 56 ${780 - i * 22} Td (${esc(l.slice(0, 92))}) Tj ET`).join('\n')
  const objs = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',
    `<< /Length ${text.length} >>\nstream\n${text}\nendstream`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
  ]
  let out = '%PDF-1.4\n'
  const offsets: number[] = []
  objs.forEach((o, i) => {
    offsets.push(out.length)
    out += `${i + 1} 0 obj\n${o}\nendobj\n`
  })
  const xref = out.length
  out += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n`
  for (const off of offsets) out += `${String(off).padStart(10, '0')} 00000 n \n`
  out += `trailer\n<< /Size ${objs.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`
  return new Blob([out], { type: 'application/pdf' })
}

// 12 rows × 5 columns with a semicolon-free shape; the card previews the first 6 rows.
export function csvBlob(): Blob {
  const rows = [
    ['Tanggal', 'Produk', 'Warna', 'Ukuran', 'Jumlah'],
    ['2026-11-01', 'Kemeja Linen', 'Krem', 'M', '12'],
    ['2026-11-01', 'Celana Kulot', 'Hitam', 'L', '8'],
    ['2026-11-02', 'Dress Midi', 'Terracotta', 'S', '5'],
    ['2026-11-02', 'Blazer Oversize', 'Abu', 'M', '3'],
    ['2026-11-03', 'Rok Plisket', 'Cokelat', 'M', '7'],
    ['2026-11-03', 'Kemeja Linen', 'Putih', 'L', '9'],
    ['2026-11-04', 'Tunik A-line', 'Hijau', 'S', '4'],
    ['2026-11-04', 'Celana Kulot', 'Navy', 'M', '6'],
    ['2026-11-05', 'Dress Midi', 'Hitam', 'M', '10'],
    ['2026-11-05', 'Outer Rajut', 'Krem', 'L', '2'],
    ['2026-11-06', 'Kemeja Linen', 'Biru', 'S', '5'],
    ['2026-11-06', 'Rok Plisket', 'Hitam', 'L', '3'],
  ]
  const text = rows.map((r) => r.map((c) => (/[",\n]/.test(c) ? `"${c.replace(/"/g, '""')}"` : c)).join(',')).join('\n') + '\n'
  return new Blob([text], { type: 'text/csv;charset=utf-8' })
}

// DOCX/XLSX/PPTX/ZIP stand-ins: only the PK signature matters (download and "which tile?" tests).
export function zipLikeBlob(ext: string, bytes = 2048): Blob {
  const buf = new Uint8Array(bytes)
  buf.set([0x50, 0x4b, 0x03, 0x04])
  let x = 0x9e3779b9
  for (let i = 4; i < bytes; i++) {
    x = (x * 1664525 + 1013904223) >>> 0
    buf[i] = x & 0xff
  }
  const mime = ext === 'docx' ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' : ext === 'xlsx' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : ext === 'pptx' ? 'application/vnd.openxmlformats-officedocument.presentationml.presentation' : 'application/zip'
  return new Blob([buf], { type: mime })
}

// Plain text, used by document cards that are neither PDF nor a spreadsheet.
export function textBlob(text: string): Blob {
  return new Blob([enc.encode(text)], { type: 'text/plain;charset=utf-8' })
}
