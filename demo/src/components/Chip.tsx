import { CheckCircle, XCircle } from '@phosphor-icons/react'
import type { Copy } from '../copy'

/** The decision as a status chip: pass in the water tint with a check, fail in the error tone with a cross. */
export default function Chip({ decision, t, big }: { decision: 'approve' | 'reject'; t: Copy; big?: boolean }) {
  const pass = decision === 'approve'
  return (
    <span className={`chip${big ? ' chip--big' : ''}`} data-v={pass ? 'pass' : 'fail'}>
      {pass ? <CheckCircle size={big ? 18 : 16} weight="fill" aria-hidden /> : <XCircle size={big ? 18 : 16} weight="fill" aria-hidden />}
      {pass ? t.demo.pass : t.demo.fail}
    </span>
  )
}
