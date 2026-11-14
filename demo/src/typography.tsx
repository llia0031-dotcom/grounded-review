// Chinese typography for display prose (the agent's explanations and replies), per the Chinese copywriting
// guidelines (sparanoid/chinese-copywriting-guidelines): a space between Chinese and Latin letters or digits,
// none around full-width punctuation. pangu.js (pinned 10.4.1, the version the chinese-web-typography skill tests)
// inserts the spaces; it also spaces Chinese curly quotes, which the guidelines do not, so those spaces are removed.
// English prose (no Chinese characters) gets curly quotes instead.
// Never applied to quotations: the ad's words and the clause text are shown exactly as written.
import { Pangu } from 'pangu/shared'

const pangu = new Pangu()
const FULL = '　-〿一-鿿＀-￯“”‘’'
const AROUND_QUOTES = [new RegExp(`([${FULL}]) ([“”‘’])`, 'g'), new RegExp(`([“”‘’]) ([${FULL}])`, 'g')]

const CJK = /[一-鿿]/

/** English display prose: straight quotes to curly ones (“…”, ‘…’, and ’ for apostrophes), as on the rest of the page. */
function smartQuotes(text: string): string {
  return text
    .replace(/(^|[\s([{—–/-])"/g, '$1“').replace(/"/g, '”')
    .replace(/(^|[\s([{—–/-])'/g, '$1‘').replace(/'/g, '’')
}

export function prose(text: string): string {
  if (!CJK.test(text ?? '')) return smartQuotes(text ?? '')
  let out = pangu.spaceText(text ?? '')
  for (let i = 0; i < 2; i++) for (const re of AROUND_QUOTES) out = out.replace(re, '$1$2')
  return out
}

/** Display prose with short quoted terms (“改善失眠”, up to 10 characters) kept on one line; longer quotes wrap normally. */
export function Prose({ text }: { text: string }) {
  const parts = prose(text).split(/(“[^”]{1,10}”)/g)
  return <>{parts.map((p, i) => (i % 2 ? <span key={i} className="ph">{p}</span> : p))}</>
}
