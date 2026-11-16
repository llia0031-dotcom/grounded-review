import { useEffect, useState } from 'react'
import { reducedMotion } from '../hooks'

const FIGURE_SPACE = ' ' // as wide as a digit, so the figure keeps its width while it counts

/** A figure such as "124 / 124" whose first number counts up to its value once, when its section is first shown.
 *  Screen readers get the final text; with reduced motion the final text is shown at once. */
export default function Roll({ text, run }: { text: string; run: boolean }) {
  const m = text.match(/^(\d+)([\s\S]*)$/)
  const target = m ? Number(m[1]) : 0
  const [n, setN] = useState(target)
  useEffect(() => {
    if (!run || reducedMotion()) { setN(target); return }
    const t0 = performance.now()
    let raf = 0
    const tick = (now: number) => {
      const p = Math.min(1, (now - t0) / 900)
      setN(Math.round(target * (1 - (1 - p) ** 3)))
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    setN(0)
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [run, target])
  if (!m) return <>{text}</>
  return (
    <>
      <span className="visually-hidden">{text}</span>
      <span aria-hidden>{String(n).padStart(m[1].length, FIGURE_SPACE)}{m[2]}</span>
    </>
  )
}
