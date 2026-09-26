import { Analyzer } from '../components/Analyzer'
import { PageHeader } from '../components/PageHeader'

export default function Analyze() {
  return <div className="page narrow-page"><PageHeader eyebrow="SENSE → THINK" title="Analyze a potential scam" description="Paste the evidence you received. NAZAR combines message, URL, payment, community, and consistency signals." /><Analyzer /><div className="info-grid"><article className="panel info-card"><span>01 / SENSE</span><h3>Extract signals</h3><p>Find payment IDs, URLs, phone numbers, amounts, claimed organizations and pressure tactics.</p></article><article className="panel info-card"><span>02 / THINK</span><h3>Explain the risk</h3><p>Score every channel separately, then expose the exact reasons behind the final decision.</p></article><article className="panel info-card"><span>03 / ACT</span><h3>Choose safely</h3><p>Stop payment, verify independently, report the indicators, or launch a controlled simulation.</p></article></div></div>
}

