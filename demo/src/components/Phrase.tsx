import type { Lang } from '../copy'

const seg = new Intl.Segmenter('zh', { granularity: 'word' })

/** Chinese display text broken only between words, never inside one ("核对" stays whole); a short quoted term
 *  (“周五前保证送达”, up to 10 characters) stays on one line as a whole. */
export default function Phrase({ text, lang }: { text: string; lang: Lang }) {
  if (lang !== 'zh') return <>{text}</>
  const parts = text.split(/(“[^”]{1,10}”)/g)
  return (
    <>
      {parts.map((part, i) => (i % 2
        ? <span key={i} className="ph">{part}</span>
        : [...seg.segment(part)].map((s, j) => <span key={`${i}-${j}`} className="ph">{s.segment}</span>)))}
    </>
  )
}
