import { ArrowUpRight, SealCheck } from '@phosphor-icons/react'
import type { Copy } from '../copy'
import type { Verdict, Violation } from '../data'
import Chip from './Chip'
import { Marked } from './AdView'
import { Prose } from '../typography'

function ViolationCard({ v, t }: { v: Violation; t: Copy }) {
  return (
    <article className="viol">
      <h4 className="viol-h">{v.catName}</h4>
      <div className="viol-pair">
        <div>
          <p className="label">{v.adQuote ? t.demo.adQuote : t.demo.inPicture}</p>
          {v.adQuote ? <blockquote className="viol-quote">“{v.adQuote}”</blockquote> : <p className="viol-visual"><Prose text={v.visual} /></p>}
        </div>
        <div>
          {v.clauseText ? (
            <>
              <p className="label">{t.demo.clause}<span className="viol-ref">{v.clauseRef}</span></p>
              <blockquote className="viol-law"><Marked text={v.clauseText} spans={v.policySpan ? [v.policySpan] : []} /></blockquote>
            </>
          ) : (
            <>
              <p className="label">{t.demo.clause}</p>
              {v.clauseUrl ? <a className="viol-link" href={v.clauseUrl}>{v.clauseRef}<ArrowUpRight size={14} aria-hidden /></a> : <p className="viol-ref">{v.clauseRef}</p>}
            </>
          )}
        </div>
      </div>
      <p className="viol-why"><Prose text={v.why} /></p>
      {v.verified && <p className="viol-check"><SealCheck size={16} weight="fill" aria-hidden />{v.adQuote ? t.demo.verified : t.demo.verifiedClause}</p>}
    </article>
  )
}

/** The verdict: the decision, then one card per violation, or the reason a risky-looking ad passes. */
export default function VerdictView({ verdict, t, headingLevel = 3 }: { verdict: Verdict; t: Copy; headingLevel?: 3 | 4 }) {
  const n = verdict.violations.length
  const H = headingLevel === 3 ? 'h3' : 'h4'
  return (
    <div className="verdict">
      <div className="verdict-head">
        <H className="visually-hidden">{verdict.decision === 'approve' ? t.demo.pass : t.demo.fail}</H>
        <Chip decision={verdict.decision} t={t} big />
        {n > 0 && <span className="verdict-count">{t.demo.count(n)}</span>}
      </div>
      {n > 0 ? (
        <div className="viols">{verdict.violations.map((v, i) => <ViolationCard key={i} v={v} t={t} />)}</div>
      ) : (
        <div className="allowed">
          <p className="label">{t.demo.allowed}</p>
          <p><Prose text={verdict.notes} /></p>
        </div>
      )}
    </div>
  )
}

/** One line per violation: the decision, then category and the words (or what the picture shows). For a turn already shown in full above. */
export function VerdictLine({ verdict, t }: { verdict: Verdict; t: Copy }) {
  return (
    <div className="vline">
      <Chip decision={verdict.decision} t={t} big />
      {verdict.violations.length > 0 ? (
        <ul className="vline-list">
          {verdict.violations.map((v, i) => (
            <li key={i}><span className="vline-cat">{v.catName}</span>{v.adQuote ? <mark>{v.adQuote}</mark> : <span><Prose text={v.visual} /></span>}<span className="vline-ref">{v.clauseRef}</span></li>
          ))}
        </ul>
      ) : <p className="vline-notes"><Prose text={verdict.notes} /></p>}
    </div>
  )
}
