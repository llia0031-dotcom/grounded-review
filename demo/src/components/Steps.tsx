import type { Copy, Lang } from '../copy'
import Phrase from './Phrase'
import { useReveal } from '../hooks'

export default function Steps({ t, lang }: { t: Copy; lang: Lang }) {
  const { ref, shown } = useReveal<HTMLElement>()
  return (
    <section className="section" aria-labelledby="steps-h" ref={ref} data-shown={shown}>
      <div className="container">
        <h2 id="steps-h" className="visually-hidden">{t.steps.head}</h2>
        <ol className="steps">
          {t.steps.items.map((s, i) => (
            <li key={s.h} className="step">
              <span className="step-n" aria-hidden>{i + 1}</span>
              <h3>{s.h}</h3>
              <p><Phrase text={s.p} lang={lang} /></p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
