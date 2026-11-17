import type { Copy } from '../copy'
import { frac, pct, useData } from '../data'
import { useReveal } from '../hooks'
import Phrase from './Phrase'
import Roll from './Roll'

/** Results: three figures, then one bar chart (share of image ads judged right per method) with the always-reject line. */
export default function Results({ t }: { t: Copy }) {
  const { ref, shown } = useReveal<HTMLElement>()
  const r = useData().results
  const f = t.results.figures
  const items = [
    { fig: frac(r.violRejected.agent), label: f.caught.label, note: f.caught.note(r.violRejected.agent[1] / r.runs, r.violRejected.agent[1]) },
    { fig: frac(r.clauseRight.agent), label: f.clause.label, note: f.clause.note(r.clauseRight.agent[1]) },
    { fig: frac(r.trapsOk.agent), label: f.traps.label, note: f.traps.note(r.trapsOk.agent[1] / r.runs, r.trapsOk.agent[1], frac(r.trapsOk.oneshot)) },
  ]
  const always = (100 * r.alwaysReject[0]) / r.alwaysReject[1]
  return (
    <section id="results" className="section" aria-labelledby="results-h" ref={ref} data-shown={shown}>
      <div className="container">
        <div className="section-head">
          <h2 id="results-h">{t.results.head}</h2>
          <p className="lead"><Phrase text={t.results.lead(r)} lang={t.lang} /></p>
        </div>
        <ul className="figures">
          {items.map((it) => (
            <li key={it.label} className="figure">
              <p className="fig num"><Roll text={it.fig} run={shown} /></p>
              <h3><Phrase text={it.label} lang={t.lang} /></h3>
              <p className="fig-note"><Phrase text={it.note} lang={t.lang} /></p>
            </li>
          ))}
        </ul>
        <figure className="chart">
          <figcaption className="chart-h">{t.results.chart.head}</figcaption>
          <div className="chart-plot" style={{ ['--always-f' as string]: always / 100 }}>
            <span className="chart-always" aria-hidden><span>{t.results.chart.always(pct(r.alwaysReject[0], r.alwaysReject[1]))}</span></span>
            <ul className="bars">
              {r.chart.map((row) => {
                const share = (100 * row.right) / row.n
                const count = t.results.chart.count(row.right, row.n, row.n > r.images)
                return (
                  <li key={row.arm} className="bar-row" tabIndex={0} aria-label={t.results.chart.aria(row.name, pct(row.right, row.n), count, t.results.chart.detail(`${row.violRejected} / ${row.viol}`, `${row.trapsOk} / ${row.traps}`))}>
                    <span className="bar-name">{row.name}</span>
                    <span className="bar-track"><span className="bar-fill" style={{ width: `${share}%` }} /></span>
                    <span className="bar-val num">{pct(row.right, row.n)}</span>
                    <span className="bar-tip" role="tooltip">{count} · {t.results.chart.detail(`${row.violRejected} / ${row.viol}`, `${row.trapsOk} / ${row.traps}`)}</span>
                  </li>
                )
              })}
            </ul>
          </div>
        </figure>
        <p className="cost"><Phrase text={t.results.cost(r.cost.agent.toFixed(4), r.cost.oneshot.toFixed(4), String(r.latency.agent), String(r.latency.oneshot))} lang={t.lang} /></p>
      </div>
    </section>
  )
}
