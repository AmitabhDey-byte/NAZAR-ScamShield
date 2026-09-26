import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Dna } from 'lucide-react'
import { PageHeader } from '../components/PageHeader'
import { ErrorBlock, LoadingBlock } from '../components/StateBlock'
import { api } from '../lib/api'
import type { Campaign } from '../lib/types'

export default function CampaignDetail() {
  const { id = '' } = useParams(); const [campaign, setCampaign] = useState<Campaign | null>(null); const [error, setError] = useState('')
  useEffect(() => { api.campaign(id).then(setCampaign).catch(err => setError(err.message)) }, [id])
  if (error) return <div className="page"><ErrorBlock message={error} /></div>; if (!campaign) return <div className="page"><LoadingBlock /></div>
  return <div className="page"><Link to="/campaigns" className="back-link"><ArrowLeft size={16} /> All campaigns</Link><PageHeader eyebrow={`${campaign.status.toUpperCase()} CAMPAIGN`} title={campaign.name} description={campaign.summary} action={<span className="report-count">{campaign.report_count}<small>linked reports</small></span>} /><div className="campaign-detail-grid"><section className="panel dna-panel"><div className="panel-heading"><div><span className="panel-kicker">SCAM DNA</span><h2>Behavioral fingerprint</h2></div><Dna size={21} /></div><div className="dna-grid">{Object.entries(campaign.fingerprint).map(([key, value]) => <div key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{Array.isArray(value) ? value.join(' · ') : String(value)}</strong></div>)}</div></section><section className="panel"><div className="panel-heading"><div><span className="panel-kicker">CONNECTED SIGNALS</span><h2>Campaign indicators</h2></div></div><div className="campaign-indicators">{campaign.indicators?.map(item => <div key={item.id}><span>{item.type}</span><strong>{item.value || item.label}</strong><b>{Math.round(item.risk_score || item.risk || 0)} risk</b></div>)}</div></section></div></div>
}

