import { FormEvent, useEffect, useState } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { Bot, CheckCircle2, Clock3, MapPin, Network, Send, ShieldCheck, Sparkles } from 'lucide-react'
import { PageHeader } from '../components/PageHeader'
import { ErrorBlock, LoadingBlock } from '../components/StateBlock'
import { api } from '../lib/api'

export default function Honeypot() {
  const { id = '' } = useParams()
  const location = useLocation()
  const [session, setSession] = useState<any>(location.state || null)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    const refresh = () => api.honeypot(id).then(value => { if (mounted) setSession(value) }).catch(err => { if (mounted && !session) setError(err.message) })
    refresh()
    const timer = window.setInterval(refresh, 5000)
    return () => { mounted = false; window.clearInterval(timer) }
    // Polling deliberately depends only on the route id.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const send = async (event: FormEvent) => {
    event.preventDefault()
    if (!input.trim()) return
    setLoading(true)
    setError('')
    try {
      setSession(await api.sendHoneypot(id, input))
      setInput('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Message failed')
    } finally {
      setLoading(false)
    }
  }

  if (error && !session) return <div className="page"><ErrorBlock message={error} /></div>
  if (!session) return <div className="page"><LoadingBlock /></div>

  const intel = session.intelligence || {}
  const telemetry = session.telemetry || []
  const canaryLabel = session.canary?.proposed
    ? `Live · ${telemetry.length} hit${telemetry.length === 1 ? '' : 's'}`
    : session.canary?.armed ? 'Armed · waiting' : session.canary?.configured ? 'Available · not armed' : 'Not configured'

  return <div className="page">
    <PageHeader eyebrow="DECEIVE / CONTROLLED SIMULATION" title="Gemini defensive honeypot" description="A synthetic victim persona collects voluntarily shared indicators and approved beacon telemetry." action={<span className={`session-state ${session.active ? 'active' : ''}`}><i />{session.active ? 'Session active' : 'Complete'}</span>} />
    <div className="honeypot-grid">
      <section className="panel chat-panel">
        <div className="chat-safety"><ShieldCheck size={16} /><span>No OTPs, passwords, private victim data, payments, automatic link opening, precise GPS, or unauthorized access.</span></div>
        <div className="chat-stream">{session.messages.map((message: any) => <div className={`chat-message ${message.role}`} key={message.id}><div className="chat-avatar">{message.role === 'assistant' ? <Bot size={17} /> : 'S'}</div><div><span>{message.role === 'assistant' ? 'NAZAR synthetic victim' : 'Scammer message'}</span><p>{message.content}</p></div></div>)}</div>
        <form className="chat-input" onSubmit={send}><textarea value={input} onChange={event => setInput(event.target.value)} placeholder="Paste the scammer’s next message…" rows={2} disabled={!session.active} /><button className="button primary" disabled={loading || !session.active}><Send size={17} />{loading ? 'Gemini is composing…' : 'Generate safe reply'}</button></form>
        {error && <p className="inline-error">{error}</p>}
      </section>
      <aside className="panel intel-panel">
        <div className="panel-heading"><div><span className="panel-kicker">LIVE EXTRACTION</span><h2>Intelligence collected</h2></div><Sparkles size={19} /></div>
        <div className="state-machine"><span>Reply engine</span><strong>{session.reply_engine?.startsWith('gemini') ? 'Gemini' : session.gemini_available ? 'Safety fallback' : 'Safety fallback · add Gemini key'}</strong></div>
        <div className="state-machine"><span>Reply delivery</span><strong>{session.auto_reply?.enabled ? `Automatic ≥ ${session.auto_reply.risk_threshold} · ${session.auto_reply.generated_replies}/${session.auto_reply.max_replies}` : 'Gmail human approval'}</strong></div>
        <div className="state-machine"><span>Telemetry beacon</span><strong>{canaryLabel}</strong></div>
        <div className="state-machine"><span>Current state</span><strong>{session.state.replaceAll('_', ' ')}</strong><div><i style={{ width: `${Math.min(100, (['INITIAL_CONTACT','BUILD_TRUST','DELAY_PAYMENT','COLLECT_PAYMENT_IDENTIFIER','COLLECT_URL','COLLECT_ALTERNATIVE_CONTACT','IDENTIFY_SCAM_SCRIPT','COMPLETE'].indexOf(session.state) + 1) * 12.5)}%` }} /></div></div>
        <div className="intel-list">{['upi_ids','urls','phone_numbers','amounts','claimed_organizations','tactics'].map(key => <div key={key}><span>{key.replaceAll('_', ' ')}</span>{intel[key]?.length ? intel[key].map((value: unknown) => <b key={String(value)}><CheckCircle2 size={14} />{String(value)}</b>) : <em>Waiting for signal</em>}</div>)}</div>
      </aside>
    </div>
    <section className="panel telemetry-panel">
      <div className="panel-heading"><div><span className="panel-kicker">BEACON / NETWORK TELEMETRY</span><h2>Observed requests</h2></div><span className="telemetry-count">{telemetry.length} CAPTURED</span></div>
      {!telemetry.length ? <div className="telemetry-empty"><Network size={22} /><p>Waiting for the approved beacon link to be requested. This view refreshes every five seconds.</p></div> : <div className="telemetry-grid">{telemetry.map((hit: any) => {
        const place = [hit.city, hit.region, hit.country].filter(Boolean).join(', ') || 'Location lookup pending'
        const coordinates = hit.latitude != null && hit.longitude != null ? `${hit.latitude}, ${hit.longitude}` : null
        const flags = Object.entries(hit.privacy_flags || {}).filter(([, value]) => value).map(([key]) => key).join(', ')
        return <article className="telemetry-card" key={hit.id}>
          <div><span className={`telemetry-kind ${hit.client_type.includes('bot') ? 'bot' : ''}`}>{hit.client_type}</span><time><Clock3 size={12} />{new Date(hit.created_at).toLocaleString()}</time></div>
          <strong>{hit.ip_address}</strong>
          <p><MapPin size={14} />{place}{coordinates ? ` · ${coordinates}` : ''}</p>
          <p><Network size={14} />{[hit.asn, hit.organization].filter(Boolean).join(' · ') || `GeoIP: ${hit.geo_status}`}</p>
          <dl><div><dt>Language</dt><dd>{hit.accept_language || 'Not supplied'}</dd></div><div><dt>Timezone</dt><dd>{hit.timezone || 'Unavailable'}</dd></div><div><dt>Net flags</dt><dd>{flags || 'None reported'}</dd></div><div><dt>Referrer</dt><dd>{hit.referrer || 'Not supplied'}</dd></div><div><dt>User agent</dt><dd>{hit.user_agent || 'Not supplied'}</dd></div></dl>
        </article>
      })}</div>}
      <p className="telemetry-disclaimer">IP geolocation is approximate and may identify a VPN, carrier gateway, or link-preview service rather than a person’s physical location.</p>
    </section>
  </div>
}
