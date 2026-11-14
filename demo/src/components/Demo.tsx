import { useState } from 'react'
import type { Copy } from '../copy'
import { useData } from '../data'
import { useReveal } from '../hooks'
import AdView from './AdView'
import VerdictView from './VerdictView'

/** The workspace: pick an ad; the ad on the left, the review on the right. */
export default function Demo({ t }: { t: Copy }) {
  const { ref, shown } = useReveal<HTMLElement>()
  const DATA = useData()
  const [id, setId] = useState(DATA.ads[0].id)
  const ad = DATA.ads.find((a) => a.id === id) ?? DATA.ads[0]
  return (
    <section id="demo" className="section" aria-labelledby="demo-h" ref={ref} data-shown={shown}>
      <div className="container">
        <div className="demo-head">
          <h2 id="demo-h">{t.demo.head}</h2>
        </div>
        <div className="clear stage">
          <fieldset className="pick">
            <legend>{t.demo.pick}</legend>
            <div className="pick-opts">
              {DATA.ads.map((a) => (
                <label key={a.id} className="opt" data-on={a.id === id}>
                  <input className="visually-hidden" type="radio" name="ad" value={a.id} checked={a.id === id} onChange={() => setId(a.id)} />
                  <span>{a.name}</span>
                  <span className="opt-sub">{t.demo.kind[a.kind]}</span>
                </label>
              ))}
            </div>
          </fieldset>
          <div className="work" key={ad.id}>
            <div className="work-ad">
              <h3 className="label">{t.demo.ad}</h3>
              <AdView ad={ad} name={ad.name} violations={ad.violations} t={t} />
            </div>
            <div className="work-verdict" aria-live="polite">
              <VerdictView verdict={ad} t={t} headingLevel={4} />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
