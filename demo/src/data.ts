// The stored evaluation output, exported by eval/export_demo.py (one file per page language). Nothing here calls a model.
import { createContext, useContext } from 'react'
import demoZh from './data/demo.json'
import demoEn from './data/demo.en.json'
import type { Lang } from './copy'

export interface Mark { line: number; span: [number, number] }
export interface Violation {
  cat: string; catName: string; clauseRef: string; clauseText: string; clauseUrl: string | null; policySpan: [number, number] | null
  adQuote: string; visual: string; why: string; verified: boolean; marks: Mark[]
}
export interface AdBlock { caption: string; words: string[]; image: string | null; size: [number, number] | null }
export interface Verdict { decision: 'approve' | 'reject'; violations: Violation[]; notes: string }
export interface Ad extends AdBlock, Verdict { id: string; name: string; kind: 'image' | 'text' }
export interface Conversation {
  id: string; name: string
  first: AdBlock & Verdict; answer: string; fixCaption: string; fixWords: string[]
  second: AdBlock & Verdict
}
export interface ChartRow { arm: string; name: string; right: number; n: number; violRejected: number; viol: number; trapsOk: number; traps: number }
export interface Results {
  ads: number; zh: number; en: number; images: number; runs: number
  violRejected: Record<'agent' | 'oneshot', [number, number]>
  clauseRight: Record<'agent' | 'oneshot', [number, number]>
  trapsOk: Record<'agent' | 'oneshot', [number, number]>
  cost: Record<'agent' | 'oneshot', number>
  latency: Record<'agent' | 'oneshot', number>
  chart: ChartRow[]; alwaysReject: [number, number]; fixPassed: [number, number]
}
export interface Dataset { ads: Ad[]; conversations: Conversation[]; results: Results }

export const DATASETS: Record<Lang, Dataset> = {
  zh: demoZh as unknown as Dataset,
  en: demoEn as unknown as Dataset,
}

/** The page's dataset, provided once at the top of the page. */
export const DataContext = createContext<Dataset>(DATASETS.zh)
export const useData = () => useContext(DataContext)

export const pct = (a: number, b: number) => `${Math.round((100 * a) / b)}%`
export const frac = (p: [number, number]) => `${p[0]} / ${p[1]}`

/** Which words of a line are quoted by a violation: [start, end) ranges, merged. */
export function marksFor(lineIndex: number, violations: Violation[]): [number, number][] {
  const spans = violations.flatMap((v) => v.marks.filter((m) => m.line === lineIndex).map((m) => m.span))
  return spans.sort((a, b) => a[0] - b[0])
}
