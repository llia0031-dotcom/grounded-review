import type { Copy } from '../copy'
import Light from './Light'

/** The close: the light again, held still (the page has one moving ground, the hero's), and the one action again. */
export default function Close({ t }: { t: Copy }) {
  return (
    <section className="close" aria-labelledby="close-h">
      <Light className="hm-light hm-light--close" paused />
      <div className="container close-inner">
        <h2 id="close-h">{t.close.head}</h2>
        <a className="btn btn--accent" href="#demo">{t.hero.cta}</a>
      </div>
    </section>
  )
}
