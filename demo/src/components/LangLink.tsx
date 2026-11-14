import { Translate } from '@phosphor-icons/react'
import type { Copy } from '../copy'

/** The link to the same page in the other language, labelled in that language. */
export default function LangLink({ t, href }: { t: Copy; href: string }) {
  return (
    <a className="lang-link" href={href} lang={t.other.lang} hrefLang={t.other.lang}>
      <Translate size={16} aria-hidden />
      {t.other.label}
    </a>
  )
}
