# Shared components

## Logo
Path: `frontend/src/components/Logo.tsx`
Brand mark and wordmark.

```tsx
export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand" aria-label="NAZAR">
      <span className="brand-mark" aria-hidden="true"><i /><b /></span>
      {!compact && <span>NAZAR</span>}
    </div>
  )
}
```

## Analyzer
Path: `frontend/src/components/Analyzer.tsx`
Reusable message, URL, and transaction analysis work surface. Props: `compact?: boolean`.

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, FileText, Globe2, IndianRupee, ScanLine, ShieldAlert } from 'lucide-react'
import { api } from '../lib/api'

const SAMPLE = 'Your electricity connection will be disconnected tonight. Pay ₹4980 immediately at ramesh123@oksbi using https://electric-bill-secure.xyz'

export function Analyzer({ compact = false }: { compact?: boolean }) {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'message' | 'url' | 'transaction'>('message')
  const [text, setText] = useState(SAMPLE)
  const [url, setUrl] = useState('')
  const [amount, setAmount] = useState('4980')
  const [payee, setPayee] = useState('ramesh123@oksbi')
  const [isNew, setIsNew] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const analyze = async () => {
    const input = mode === 'url' ? url : mode === 'transaction' ? `Payment request to ${payee} for ₹${amount}` : text
    if (input.trim().length < 3) { setError('Add a message, URL, or payment context first.'); return }
    setLoading(true); setError('')
    try {
      const result = await api.analyze({
        text: input,
        url: mode === 'url' ? url : undefined,
        transaction: { amount: Number(amount) || 0, payee, is_new_recipient: isNew, transaction_hour: new Date().getHours(), recent_frequency: 1 },
      })
      navigate(`/result/${result.id}`, { state: result })
    } catch (err) {
      setError(err instanceof Error ? `${err.message}. Is the API running on port 8000?` : 'Analysis failed')
    } finally { setLoading(false) }
  }

  return (
    <section className={`panel analyzer-panel ${compact ? 'compact' : ''}`}>
      <div className="panel-heading">
        <div><span className="panel-kicker">SENSE + THINK</span><h2>Analyze a suspicious request</h2></div>
        <div className="privacy-note"><ShieldAlert size={14} /> Processed locally first</div>
      </div>
      <div className="mode-tabs" role="tablist" aria-label="Analysis type">
        <button className={mode === 'message' ? 'active' : ''} onClick={() => setMode('message')}><FileText size={16} /> Message</button>
        <button className={mode === 'url' ? 'active' : ''} onClick={() => setMode('url')}><Globe2 size={16} /> URL</button>
        <button className={mode === 'transaction' ? 'active' : ''} onClick={() => setMode('transaction')}><IndianRupee size={16} /> Transaction</button>
      </div>
      {mode === 'message' && <label className="field"><span>Message or chat text</span><textarea value={text} onChange={event => setText(event.target.value)} rows={compact ? 5 : 7} /></label>}
      {mode === 'url' && <label className="field"><span>Suspicious URL</span><input value={url} onChange={event => setUrl(event.target.value)} placeholder="https://example.xyz/verify" /></label>}
      {mode === 'transaction' && <div className="form-grid two"><label className="field"><span>Amount</span><div className="input-prefix"><b>₹</b><input type="number" value={amount} onChange={event => setAmount(event.target.value)} /></div></label><label className="field"><span>Payee / UPI ID</span><input value={payee} onChange={event => setPayee(event.target.value)} /></label></div>}
      <div className="signal-row"><span>Signals in context</span><div><b>₹4,980</b><b>UPI ID</b><b>Urgency</b><b>Threat</b><b>.xyz domain</b></div></div>
      <div className="analyzer-footer">
        <label className="check-field"><input type="checkbox" checked={isNew} onChange={event => setIsNew(event.target.checked)} /><span>New recipient</span></label>
        <button className="button primary" onClick={analyze} disabled={loading}><ScanLine size={18} />{loading ? 'Analyzing signals…' : 'Analyze threat'}<ArrowRight size={17} /></button>
      </div>
      {error && <p className="inline-error" role="alert">{error}</p>}
    </section>
  )
}
```

## PageHeader
Path: `frontend/src/components/PageHeader.tsx`
Reusable route heading. Props: eyebrow, title, description, action.

```tsx
import type { ReactNode } from 'react'

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return (
    <div className="page-header">
      <div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>
      {action && <div className="page-action">{action}</div>}
    </div>
  )
}
```

## RiskBadge
Path: `frontend/src/components/RiskBadge.tsx`
Semantic risk decision chip.

```tsx
import { AlertOctagon, CheckCircle2, TriangleAlert } from 'lucide-react'
import type { Classification } from '../lib/types'

export function RiskBadge({ classification }: { classification: Classification | string }) {
  const Icon = classification === 'DANGEROUS' ? AlertOctagon : classification === 'SUSPICIOUS' ? TriangleAlert : CheckCircle2
  return <span className={`risk-badge ${classification.toLowerCase()}`}><Icon size={14} />{classification}</span>
}
```

## StateBlock
Path: `frontend/src/components/StateBlock.tsx`
Shared loading and error states.

```tsx
import { AlertTriangle, LoaderCircle } from 'lucide-react'

export function LoadingBlock({ label = 'Loading intelligence…' }: { label?: string }) {
  return <div className="state-block"><LoaderCircle className="spin" size={20} /><span>{label}</span></div>
}

export function ErrorBlock({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="state-block error"><AlertTriangle size={20} /><span>{message}</span>{retry && <button onClick={retry}>Retry</button>}</div>
}
```
