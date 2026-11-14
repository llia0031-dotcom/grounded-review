import type { Copy } from '../copy'
import { useReveal } from '../hooks'

export default function Faq({ t }: { t: Copy }) {
  const { ref, shown } = useReveal<HTMLElement>()
  return (
    <section id="faq" className="section section--faq" aria-labelledby="faq-h" ref={ref} data-shown={shown}>
      <div className="container faq-grid">
        <h2 id="faq-h">{t.faq.head}</h2>
        <div className="faq">
          {t.faq.items.map((f) => (
            <details key={f.q} className="faq-item">
              <summary><span>{f.q}</span></summary>
              <p>{f.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  )
}
