import { useState } from 'react'
import type { Copy } from '../copy'
import { useData } from '../data'
import { useReveal } from '../hooks'
import AdView from './AdView'
import VerdictView, { VerdictLine } from './VerdictView'
import { Prose } from '../typography'

/** One stored conversation: review, the advertiser's question and the answer, their own new version, the second review. */
export default function Followup({ t }: { t: Copy }) {
  const { ref, shown } = useReveal<HTMLElement>()
  const DATA = useData()
  const [id, setId] = useState(DATA.conversations[0].id)
  const c = DATA.conversations.find((x) => x.id === id) ?? DATA.conversations[0]
  return (
    <section id="followup" className="section section--band" aria-labelledby="followup-h" ref={ref} data-shown={shown}>
      <div className="container">
        <div className="demo-head">
          <h2 id="followup-h">{t.followup.head}</h2>
          <fieldset className="pick pick--inline">
            <legend className="visually-hidden">{t.followup.pick}</legend>
            <div className="tabs" role="presentation">
              {DATA.conversations.map((x) => (
                <label key={x.id} className="tab" data-on={x.id === id}>
                  <input className="visually-hidden" type="radio" name="conversation" value={x.id} checked={x.id === id} onChange={() => setId(x.id)} />
                  {x.name}
                </label>
              ))}
            </div>
          </fieldset>
        </div>
        <ol className="thread" key={c.id}>
          <li className="turn">
            <p className="turn-label">{t.followup.turn1}</p>
            <div className="turn-body clear">
              <div className="turn-grid">
                <AdView ad={c.first} name={c.name} violations={c.first.violations} t={t} compact />
                <VerdictLine verdict={c.first} t={t} />
              </div>
            </div>
          </li>
          <li className="turn turn--ask">
            <p className="bubble bubble--me">{t.followup.ask}</p>
          </li>
          <li className="turn">
            <div className="bubble bubble--reply">
              <div className="reply-text">{c.answer.split(/\n{2,}/).map((para, i) => <p key={i}><Prose text={para} /></p>)}</div>
              <div className="fix">
                <p className="label">{t.followup.fix}</p>
                <dl className="adview-text">
                  <dt>{t.followup.fixCaption}</dt>
                  <dd>{c.fixCaption}</dd>
                  {c.fixWords.length > 0 && (<><dt>{t.followup.fixWords}</dt><dd>{c.fixWords.map((w, i) => <span key={i} className="adview-line">{w}</span>)}</dd></>)}
                </dl>
              </div>
            </div>
          </li>
          <li className="turn">
            <p className="turn-label">{t.followup.submit}</p>
            <div className="turn-body clear">
              <div className="turn-grid">
                <AdView ad={c.second} name={c.name} violations={c.second.violations} t={t} compact />
                <div>
                  <p className="turn-label turn-label--inner">{t.followup.turn2}</p>
                  <VerdictView verdict={c.second} t={t} />
                </div>
              </div>
            </div>
          </li>
        </ol>
      </div>
    </section>
  )
}
