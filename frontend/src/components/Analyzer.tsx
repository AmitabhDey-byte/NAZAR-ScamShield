import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, FileText, Globe2, IndianRupee, ScanLine, ShieldAlert } from 'lucide-react'
import { api } from '../lib/api'

const examples = [
  { label: 'Genuine message', tone: 'safe', text: 'Hi, the team meeting has moved to 3 PM tomorrow. See you in the office.' },
  { label: 'Scam message', tone: 'danger', text: 'URGENT: Your SBI KYC is blocked. Pay ₹4,980 now to secure-refund@okaxis and verify at http://sbi-account-verify.top/login.' },
  { label: 'Hindi / Hinglish scam', tone: 'warning', text: 'तुरंत KYC अपडेट करें, नहीं तो आपका बैंक खाता बंद हो जाएगा। अभी इस लिंक को खोलें: http://bank-verify-now.xyz' },
] as const

export function Analyzer({ compact = false }: { compact?: boolean }) {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'message' | 'url' | 'transaction'>('message')
  const [text, setText] = useState('')
  const [url, setUrl] = useState('')
  const [amount, setAmount] = useState('')
  const [payee, setPayee] = useState('')
  const [isNew, setIsNew] = useState(true)
  const [transactionTime, setTransactionTime] = useState(() => `${String(new Date().getHours()).padStart(2, '0')}:00`)
  const [recentFrequency, setRecentFrequency] = useState('0')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const analyze = async () => {
    const input = mode === 'url' ? url : mode === 'transaction' ? `Payment request to ${payee} for ₹${amount}` : text
    if (input.trim().length < 3) { setError('Add a message, URL, or payment context first.'); return }
    setLoading(true); setError('')
    try {
      const transaction = mode === 'transaction' ? {
        amount: Number(amount) || 0,
        payee,
        is_new_recipient: isNew,
        transaction_hour: Number(transactionTime.split(':')[0]) || 0,
        recent_frequency: Number(recentFrequency) || 0,
      } : undefined
      const result = await api.analyze({
        text: input,
        url: mode === 'url' ? url : undefined,
        transaction,
      })
      navigate(`/result/${result.id}`, { state: result })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally { setLoading(false) }
  }

  return (
    <section className={`panel analyzer-panel ${compact ? 'compact' : ''}`}>
      <div className="panel-heading">
        <div><span className="panel-kicker">SENSE + THINK</span><h2>Analyze a suspicious request</h2></div>
        <div className="privacy-note"><ShieldAlert size={14} /> API keys stay on the backend</div>
      </div>
      <div className="mode-tabs" role="tablist" aria-label="Analysis type">
        <button className={mode === 'message' ? 'active' : ''} onClick={() => setMode('message')}><FileText size={16} /> Message</button>
        <button className={mode === 'url' ? 'active' : ''} onClick={() => setMode('url')}><Globe2 size={16} /> URL</button>
        <button className={mode === 'transaction' ? 'active' : ''} onClick={() => setMode('transaction')}><IndianRupee size={16} /> Transaction</button>
      </div>
      {mode === 'message' && <><label className="field"><span>Message or chat text</span><textarea value={text} onChange={event => setText(event.target.value)} rows={compact ? 5 : 7} placeholder="Paste the message exactly as received…" /></label><div className="example-strip"><span>TRY A SAMPLE</span><div>{examples.map(example => <button type="button" key={example.label} className={example.tone} onClick={() => setText(example.text)}>{example.label}</button>)}</div></div></>}
      {mode === 'url' && <label className="field"><span>Suspicious URL</span><input value={url} onChange={event => setUrl(event.target.value)} placeholder="https://example.xyz/verify" /></label>}
      {mode === 'transaction' && <div className="transaction-fields"><div className="form-grid two"><label className="field"><span>Amount</span><div className="input-prefix"><b>₹</b><input type="number" min="0" value={amount} onChange={event => setAmount(event.target.value)} /></div></label><label className="field"><span>Payee / UPI ID</span><input value={payee} onChange={event => setPayee(event.target.value)} placeholder="name@bank" /></label></div><div className="form-grid two"><label className="field"><span>Transaction time</span><input type="time" value={transactionTime} onChange={event => setTransactionTime(event.target.value)} /></label><label className="field"><span>Payments to this recipient in the last 24 hours</span><input type="number" min="0" max="100" value={recentFrequency} onChange={event => setRecentFrequency(event.target.value)} /></label></div><label className="check-field transaction-check"><input type="checkbox" checked={isNew} onChange={event => setIsNew(event.target.checked)} /><span>This is a new recipient</span></label></div>}
      <div className="signal-row"><span>Live signal extraction</span><div><b>UPI</b><b>URLs</b><b>Urgency</b><b>Impersonation</b><b>Payment pressure</b></div></div>
      <div className="analyzer-footer">
        <span className="analysis-scope">Uses live URL, community, ML and Gemini signals when configured.</span>
        <button className="button primary" onClick={analyze} disabled={loading}><ScanLine size={18} />{loading ? 'Analyzing signals…' : 'Analyze threat'}<ArrowRight size={17} /></button>
      </div>
      {error && <p className="inline-error" role="alert">{error}</p>}
    </section>
  )
}
