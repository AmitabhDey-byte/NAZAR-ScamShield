import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, Fingerprint, RadioTower } from 'lucide-react'
import { PageHeader } from '../components/PageHeader'
import { ErrorBlock, LoadingBlock } from '../components/StateBlock'
import { api } from '../lib/api'
import type { Campaign } from '../lib/types'

export default function Campaigns() {
  const [items, setItems] = useState<Campaign[]>([]); const [error, setError] = useState(''); const [loading, setLoading] = useState(true)
  useEffect(() => { api.campaigns().then(setItems).catch(err => setError(err.message)).finally(() => setLoading(false)) }, [])
  return <div className="page"><PageHeader eyebrow="SHARE / CAMPAIGNS" title="Correlated scam campaigns" description="Reports become more useful when shared identifiers and scripts reveal the same operators." />{loading ? <LoadingBlock /> : error ? <ErrorBlock message={error} /> : <div className="campaign-grid">{items.map((campaign, index) => <Link className="panel campaign-card" to={`/campaign/${campaign.id}`} key={campaign.id}><div className="campaign-card-top"><div className="campaign-number">#{String(index + 17).padStart(2, '0')}</div><span className={`campaign-status ${campaign.status}`}><i />{campaign.status}</span></div><h2>{campaign.name}</h2><p>{campaign.summary}</p><div className="campaign-stats"><span><RadioTower size={16} /><b>{campaign.report_count}</b> reports</span><span><Fingerprint size={16} /><b>{String(campaign.fingerprint.infrastructure_reuse || '—')}</b> reuse</span></div><div className="campaign-tags">{((campaign.fingerprint.tactics as string[]) || []).map(item => <span key={item}>{item}</span>)}</div><span className="text-link">Open campaign <ArrowUpRight size={16} /></span></Link>)}</div>}</div>
}

