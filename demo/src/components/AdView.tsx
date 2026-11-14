import type { Copy } from '../copy'
import { marksFor, type AdBlock, type Violation } from '../data'

/** A line of the ad with the quoted words marked. */
export function Marked({ text, spans }: { text: string; spans: [number, number][] }) {
  if (!spans.length) return <>{text}</>
  const out: React.ReactNode[] = []
  let at = 0
  spans.forEach(([s, e], i) => {
    if (s < at) return
    if (s > at) out.push(text.slice(at, s))
    out.push(<mark key={i}>{text.slice(s, e)}</mark>)
    at = e
  })
  out.push(text.slice(at))
  return <>{out}</>
}

/** The ad as the reviewer sees it: the image, the caption, and the words read from the image, offending words marked. */
export default function AdView({ ad, name, violations, t, compact }: { ad: AdBlock; name: string; violations: Violation[]; t: Copy; compact?: boolean }) {
  return (
    <div className={`adview${compact ? ' adview--compact' : ''}${ad.image ? '' : ' adview--text'}`}>
      {ad.image && <img className="adview-img" src={ad.image} alt={t.demo.imageAlt(name)} width={ad.size?.[0]} height={ad.size?.[1]} loading="lazy" decoding="async" />}
      <dl className="adview-text">
        <dt>{t.demo.caption}</dt>
        <dd><Marked text={ad.caption} spans={marksFor(0, violations)} /></dd>
        {ad.words.length > 0 && (
          <>
            <dt>{t.demo.words}</dt>
            <dd>
              {ad.words.map((w, i) => <span key={i} className="adview-line"><Marked text={w} spans={marksFor(i + 1, violations)} /></span>)}
            </dd>
          </>
        )}
      </dl>
    </div>
  )
}
