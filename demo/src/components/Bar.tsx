import type { Copy } from '../copy'
import { useCurrentSection } from '../hooks'
import LangLink from './LangLink'

const SECTIONS = ['demo', 'followup', 'results', 'faq'] as const

export default function Bar({ t }: { t: Copy }) {
  const current = useCurrentSection([...SECTIONS])
  return (
    <header className="bar">
      <div className="container bar-inner">
        <a className="logo" href="#top">
          <svg width="22" height="22" viewBox="0 0 32 32" aria-hidden><rect x="5" y="6" width="22" height="20" rx="5" fill="none" stroke="currentColor" strokeWidth="3" /><path d="M11 16.5l3.6 3.5L21.5 12" fill="none" stroke="var(--color-accent)" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" /></svg>
          <span className="logo-name">{t.brand}</span>
        </a>
        <nav className="links" aria-label={t.brand}>
          {SECTIONS.map((id) => (
            <a key={id} href={`#${id}`} aria-current={current === id ? 'location' : undefined}>{t.nav[id]}</a>
          ))}
        </nav>
        <LangLink t={t} href={t.other.home} />
      </div>
    </header>
  )
}
