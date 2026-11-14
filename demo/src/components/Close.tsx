import type { Copy } from '../copy'
import Light from './Light'

export default function Close({ t, still }: { t: Copy; still: boolean }) {
  return (
    <section className="close" aria-labelledby="close-h">
      <Light className="hm-light hm-light--close" paused={still} />
      <div className="container close-inner">
        <h2 id="close-h">{t.close.head}</h2>
        <a className="btn btn--accent" href="#demo">{t.hero.cta}</a>
      </div>
    </section>
  )
}
