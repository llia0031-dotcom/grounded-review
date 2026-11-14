import { useEffect, useMemo, useRef } from 'react'
import type { Lang } from '../copy'
import { reducedMotion } from '../hooks'

/** The tagline: muted at first, each word turning to full ink as it crosses a line in the lower third of the screen. */
export default function Tagline({ lines, lang }: { lines: string[]; lang: Lang }) {
  const host = useRef<HTMLParagraphElement>(null)
  const rows = useMemo(() => {
    const seg = new Intl.Segmenter(lang === 'zh' ? 'zh' : 'en', { granularity: 'word' })
    return lines.map((line) => [...seg.segment(line)].map((s) => s.segment))
  }, [lines, lang])

  useEffect(() => {
    const el = host.current
    if (!el) return
    const spans = [...el.querySelectorAll<HTMLSpanElement>('.tw')]
    if (reducedMotion()) { spans.forEach((s) => s.setAttribute('data-on', 'true')); return }
    spans.forEach((s) => s.removeAttribute('data-on'))
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) { e.target.setAttribute('data-on', 'true'); io.unobserve(e.target) }
    }, { rootMargin: '0px 0px -38% 0px' })
    spans.forEach((s) => io.observe(s))
    return () => io.disconnect()
  }, [rows])

  return (
    <section className="tagline">
      <div className="container">
        <p className="visually-hidden">{lines.join(lang === 'zh' ? '' : ' ')}</p>
        <p ref={host} className="tagline-text" aria-hidden>
          {rows.map((words, r) => (
            <span key={r} className="tl">
              {words.map((w, i) => (/^\s+$/.test(w) ? w : <span key={i} className="tw">{w}</span>))}
            </span>
          ))}
        </p>
      </div>
    </section>
  )
}
