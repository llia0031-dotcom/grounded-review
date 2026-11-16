import type { Lang } from '../copy'

function split(text: string, lang: Lang): string[] {
  if (lang !== 'zh') return text.split(/(\s+)/)
  const seg = new Intl.Segmenter('zh', { granularity: 'word' })
  return text.split(/(“[^”]{1,10}”)/g).flatMap((part, i) => (i % 2 ? [part] : [...seg.segment(part)].map((s) => s.segment)))
}

/** How many animated words a line has, so the next line can continue the count. */
export function wordCount(text: string, lang: Lang): number {
  return split(text, lang).filter((w) => w.trim()).length
}

/** A heading line whose words come in one after another, once, on load (opacity and a short rise only). The text
 *  stays real text for screen readers; Chinese breaks only between words, and a short quoted term stays whole. */
export default function Words({ text, lang, from = 0 }: { text: string; lang: Lang; from?: number }) {
  let n = from
  return (
    <>
      {split(text, lang).map((w, i) => (w.trim() ? <span key={i} className="hw ph" style={{ ['--i' as string]: n++ }}>{w}</span> : w))}
    </>
  )
}
