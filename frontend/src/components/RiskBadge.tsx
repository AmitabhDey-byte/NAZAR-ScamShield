import { AlertOctagon, CheckCircle2, TriangleAlert } from 'lucide-react'
import type { Classification } from '../lib/types'

export function RiskBadge({ classification }: { classification: Classification | string }) {
  const Icon = classification === 'DANGEROUS' ? AlertOctagon : classification === 'SUSPICIOUS' ? TriangleAlert : CheckCircle2
  return <span className={`risk-badge ${classification.toLowerCase()}`}><Icon size={14} />{classification}</span>
}

