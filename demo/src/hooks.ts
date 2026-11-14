import { useEffect, useRef, useState } from 'react'

export const reducedMotion = () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

/** Marks an element as shown the first time it enters the viewport (one reveal, never replayed). */
export function useReveal<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [shown, setShown] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el || shown) return
    if (reducedMotion()) { setShown(true); return }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setShown(true); io.disconnect() } }, { rootMargin: '0px 0px -12% 0px' })
    io.observe(el)
    return () => io.disconnect()
  }, [shown])
  return { ref, shown }
}

/** Which of the given section ids is in view, for the current nav item. */
export function useCurrentSection(ids: string[]) {
  const [current, setCurrent] = useState<string | null>(null)
  useEffect(() => {
    const seen = new Map<string, number>()
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) seen.set(e.target.id, e.isIntersecting ? e.intersectionRatio : 0)
      let best: string | null = null
      let ratio = 0
      for (const id of ids) { const r = seen.get(id) ?? 0; if (r > ratio) { ratio = r; best = id } }
      setCurrent(best)
    }, { threshold: [0, 0.15, 0.4, 0.7] })
    for (const id of ids) { const el = document.getElementById(id); if (el) io.observe(el) }
    return () => io.disconnect()
  }, [ids.join('|')])
  return current
}
