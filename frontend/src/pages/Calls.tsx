import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Headphones, ScanLine } from 'lucide-react'
import { PageHeader } from '../components/PageHeader'
import { api } from '../lib/api'

const sample = 'This is the SBI fraud department. Your account will be suspended today unless you complete KYC now. Open sbi-kyc-secure.top and pay ₹999 verification fee to kycdesk@okaxis.'

export default function Calls() {
  const navigate = useNavigate(); const [caller, setCaller] = useState('+91 98765 43210'); const [transcript, setTranscript] = useState(sample); const [loading, setLoading] = useState(false); const [error, setError] = useState('')
  const submit = async (event: FormEvent) => { event.preventDefault(); setLoading(true); setError(''); try { const data = await api.call({ transcript, caller_number: caller }); navigate(`/result/${data.id}`, { state: data }) } catch (err) { setError(err instanceof Error ? err.message : 'Analysis failed') } finally { setLoading(false) } }
  return <div className="page narrow-page"><PageHeader eyebrow="BONUS / CALL ANALYSIS" title="Analyze a suspicious call transcript" description="No call interception. Paste or type a transcript and run it through the same explainable Sense/Think engine." /><form className="panel call-form" onSubmit={submit}><div className="call-icon"><Headphones size={24} /></div><label className="field"><span>Caller number (optional)</span><input value={caller} onChange={event => setCaller(event.target.value)} /></label><label className="field"><span>Call transcript</span><textarea rows={12} value={transcript} onChange={event => setTranscript(event.target.value)} /></label>{error && <p className="inline-error">{error}</p>}<div className="form-actions"><span>Audio stays outside NAZAR; only the transcript is analyzed.</span><button className="button primary" disabled={loading}><ScanLine size={17} />{loading ? 'Analyzing…' : 'Analyze transcript'}</button></div></form></div>
}

