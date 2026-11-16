import { Pause, Play } from '@phosphor-icons/react'
import type { Copy } from '../copy'
import { useData } from '../data'
import Chip from './Chip'
import Light from './Light'
import Phrase from './Phrase'
import Words, { wordCount } from './Words'

/** The hero's figure: the real stored review of the first workspace ad, lying in the water light. */
function Sample({ t }: { t: Copy }) {
  const ad = useData().ads[0]
  const v = ad.violations[0]
  return (
    <figure className="hero-figure">
      <div className="clear clear--lead sample">
        {ad.image && <img className="sample-img" src={ad.image} alt={t.demo.imageAlt(ad.name)} width={ad.size?.[0]} height={ad.size?.[1]} />}
        <div className="sample-body">
          <div className="sample-row" style={{ ['--i' as string]: 0 }}><Chip decision={ad.decision} t={t} /><span className="sample-cat">{v.catName}</span></div>
          <p className="sample-row sample-quote" style={{ ['--i' as string]: 1 }}><mark>{v.adQuote}</mark></p>
          <p className="sample-row sample-ref" style={{ ['--i' as string]: 2 }}>{v.clauseRef}</p>
        </div>
      </div>
    </figure>
  )
}

export default function Hero({ t, still, onToggleStill }: { t: Copy; still: boolean; onToggleStill: () => void }) {
  const data = useData()
  return (
    <section className="hero" aria-labelledby="hero-h">
      <Light paused={still} />
      <button type="button" className="motion-toggle" aria-pressed={still} aria-label={still ? t.motion.play : t.motion.pause} title={still ? t.motion.play : t.motion.pause} onClick={onToggleStill}>
        {still ? <Play size={16} weight="fill" aria-hidden /> : <Pause size={16} weight="fill" aria-hidden />}
      </button>
      <div className="container hero-grid">
        <div className="hero-text">
          <h1 id="hero-h">{t.hero.head.map((line, i) => <span key={line} className="h-line"><Words text={line} lang={t.lang} from={t.hero.head.slice(0, i).reduce((sum, l) => sum + wordCount(l, t.lang), 0)} />{t.lang === 'en' && i < t.hero.head.length - 1 ? ' ' : ''}</span>)}</h1>
          <p className="lead"><Phrase text={t.hero.lead} lang={t.lang} /></p>
          <a className="btn btn--accent" href="#demo">{t.hero.cta}</a>
          <p className="proof"><Phrase text={t.hero.proof(data.results.ads)} lang={t.lang} /></p>
        </div>
        <Sample t={t} />
      </div>
    </section>
  )
}
