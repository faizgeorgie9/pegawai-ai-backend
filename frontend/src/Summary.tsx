import type { EvalSummary } from './bff'
import { ALL_DIMENSIONS } from './results'
import { SCENARIOS } from './scenarios'
import { Empty } from './ui-extra'

// Experiment summary at the top of Evaluasi. All numbers come from GET /api/evaluations/summary (real evaluations, latest one per case).
export default function Summary({ data }: { data: EvalSummary }) {
  if (!data.total_evaluations) return <Empty title="Belum ada evaluasi">Ringkasan muncul setelah evaluasi pertama disimpan.</Empty>
  const tested = new Set(data.cases.map((c) => c.case_id))
  const groups = [
    { label: 'Marketing', ids: SCENARIOS.filter((s) => s.group === 'marketing').map((s) => s.id) },
    { label: 'CS', ids: SCENARIOS.filter((s) => s.group === 'cs').map((s) => s.id) },
  ]
  const untested = SCENARIOS.filter((s) => !tested.has(s.id)).map((s) => s.id)
  const when = data.latest_at ? new Date(data.latest_at * 1000).toLocaleString('id-ID', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '–'
  return (
    <section className="sum" aria-labelledby="sum-h">
      <header className="sum-head">
        <h2 id="sum-h">Ringkasan eksperimen</h2>
        <span className="quiet small">Evaluasi terakhir: {when}</span>
      </header>
      <div className="sum-grid">
        {groups.map((g) => {
          const n = g.ids.filter((id) => tested.has(id)).length
          return (
            <div key={g.label} className="card sum-stat">
              <span className="quiet small">{g.label}</span>
              <b className="num">{n} <i>dari {g.ids.length} kasus</i></b>
            </div>
          )
        })}
        <div className="card sum-stat"><span className="quiet small">Lulus</span><b className="num">{data.counts.pass}</b></div>
        <div className="card sum-stat"><span className="quiet small">Gagal</span><b className="num">{data.counts.fail}</b></div>
        <div className="card sum-stat"><span className="quiet small">Nonaktif</span><b className="num">{data.counts.blocked}</b></div>
      </div>
      <p className="quiet small">Hasil dihitung dari evaluasi terbaru tiap kasus.</p>
      <div className="sum-cols">
        <div className="card sum-panel">
          <h3>Rata-rata skor per dimensi</h3>
          <p className="quiet small">Marketing (9 dimensi) dan CS (6 kriteria) digabung; Accuracy, Relevance, Brand, dan Knowledge dipakai keduanya.</p>
          <ul className="sbars">
            {ALL_DIMENSIONS.map((d) => {
              const v = data.dimensions[d.key]?.avg ?? null
              return (
                <li key={d.key}>
                  <span>{d.label}</span>
                  <span className="sbar" role="img" aria-label={v === null ? 'Belum ada skor' : `${v.toFixed(1)} dari 5`}><i style={{ width: v === null ? 0 : `${(v / 5) * 100}%` }} /></span>
                  <b className="num">{v === null ? '–' : v.toFixed(1)}</b>
                </li>
              )
            })}
          </ul>
        </div>
        <div className="card sum-panel">
          <h3>Belum diuji</h3>
          {untested.length ? (
            <ul className="ids">{untested.map((id) => <li key={id} className="pill plain">{id}</li>)}</ul>
          ) : (
            <p className="quiet">Semua kasus sudah diuji.</p>
          )}
        </div>
      </div>
    </section>
  )
}
