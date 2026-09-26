import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Activity, ArrowUpRight, Fingerprint, RadioTower, ShieldAlert, Smartphone } from 'lucide-react'
import { Area, AreaChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis } from 'recharts'
import { Analyzer } from '../components/Analyzer'
import { PageHeader } from '../components/PageHeader'
import { RiskBadge } from '../components/RiskBadge'
import { api } from '../lib/api'
import { subscribeRealtime } from '../lib/realtime'

const colors = ['#3B82F6', '#22D3EE', '#25C281', '#F5A524', '#FF5D73', '#93A4BA']
const statMeta = [
  ['threats_analyzed', 'Threats analyzed', Activity, 'Stored analyses'],
  ['dangerous_scams', 'Dangerous scams', ShieldAlert, 'High-risk decisions'],
  ['active_campaigns', 'Tracked campaigns', RadioTower, 'From confirmed reports'],
  ['indicators_collected', 'Indicators collected', Fingerprint, 'Observed in submissions'],
] as const

export default function Dashboard() {
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState('')
  const load = useCallback(() => api.dashboard().then(value => { setData(value); setError('') }).catch(err => setError(err.message)), [])
  useEffect(() => { load(); return subscribeRealtime(() => load()) }, [load])

  if (!data) return <div className="page"><PageHeader eyebrow="COMMAND CENTER" title="Live scam operations" description="Waiting for your backend…" />{error && <p className="inline-error">{error}</p>}</div>
  const campaign = data.top_campaign
  return <div className="page dashboard-page">
    <PageHeader eyebrow="COMMAND CENTER" title="Live scam operations" description="Every number below comes from an analysis, paired phone, or community report stored by your backend." action={<span className="sync-label"><i /> Updated {new Date(data.generated_at).toLocaleTimeString()}</span>} />
    <section className="stats-grid">{statMeta.map(([key, label, Icon, context]) => <article className="stat-card" key={key}><div><span>{label}</span><strong>{Number(data.metrics[key] || 0).toLocaleString('en-IN')}</strong></div><div className="stat-side"><Icon size={19} /><b>{context}</b></div></article>)}</section>
    <section className="dashboard-main"><Analyzer compact /><article className="panel campaign-pulse">
      <div className="panel-heading"><div><span className="panel-kicker">REAL-TIME SIGNALS</span><h2>{campaign ? 'Campaign pulse' : 'Awaiting confirmed reports'}</h2></div>{campaign && <span className="risk-badge suspicious">{campaign.status.toUpperCase()}</span>}</div>
      <div className="sparkline"><ResponsiveContainer width="100%" height={136}><AreaChart data={data.reports_over_time}><defs><linearGradient id="signalArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#22D3EE" stopOpacity={0.32} /><stop offset="1" stopColor="#22D3EE" stopOpacity={0} /></linearGradient></defs><XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#93A4BA', fontSize: 10 }} /><Tooltip contentStyle={{ background: '#11233A', border: '1px solid rgba(148,163,184,.18)', borderRadius: 10 }} /><Area type="monotone" dataKey="signals" stroke="#22D3EE" fill="url(#signalArea)" strokeWidth={2} /></AreaChart></ResponsiveContainer></div>
      {campaign ? <><div className="campaign-focus"><div className="campaign-index"><RadioTower size={21} /></div><div><h3>{campaign.name}</h3><p>{campaign.summary} {campaign.report_count} confirmed report{campaign.report_count === 1 ? '' : 's'}.</p></div></div><div className="indicator-list">{campaign.indicators.length ? campaign.indicators.map((item: any) => <span key={item.id}><i className="danger-dot" />{item.value}<b>{item.reports} reports · {item.observations} observations</b></span>) : <span>No indicator linked yet.</span>}</div><Link className="text-link" to={`/campaign/${campaign.id}`}>Open campaign graph <ArrowUpRight size={16} /></Link></> : <div className="empty-card"><Smartphone size={24} /><h3>No manufactured campaign data</h3><p>Pair the Expo app or submit a report. Verified signals will appear here immediately.</p></div>}
    </article></section>
    <section className="dashboard-lower"><article className="panel recent-panel"><div className="panel-heading"><div><span className="panel-kicker">RECENT DECISIONS</span><h2>Analysis queue</h2></div><Link to="/analyze" className="text-link">New analysis <ArrowUpRight size={15} /></Link></div>{data.recent.length ? <div className="table-wrap"><table><thead><tr><th>Source</th><th>Category</th><th>Risk</th><th>Decision</th></tr></thead><tbody>{data.recent.map((item: any) => <tr key={item.id}><td><span className="source-id">{item.source_type.toUpperCase()}</span></td><td>{item.category.replaceAll('_', ' ')}</td><td><b className="score-cell">{Math.round(item.score)}</b>/100</td><td><RiskBadge classification={item.classification} /></td></tr>)}</tbody></table></div> : <div className="empty-card"><Activity size={24} /><h3>No analyses yet</h3><p>Run the first scan from the web console or your paired phone.</p></div>}</article>
      <article className="panel distribution-panel"><div className="panel-heading"><div><span className="panel-kicker">ALL STORED SIGNALS</span><h2>Scam categories</h2></div></div>{data.category_distribution.length ? <div className="distribution-body"><ResponsiveContainer width="58%" height={190}><PieChart><Pie data={data.category_distribution} dataKey="value" innerRadius={55} outerRadius={78} paddingAngle={3}>{data.category_distribution.map((_: any, index: number) => <Cell key={index} fill={colors[index % colors.length]} />)}</Pie><Tooltip contentStyle={{ background: '#11233A', border: '1px solid rgba(148,163,184,.18)', borderRadius: 10 }} /></PieChart></ResponsiveContainer><div className="legend">{data.category_distribution.map((item: any, index: number) => <span key={item.name}><i style={{ background: colors[index % colors.length] }} />{item.name.replaceAll('_', ' ')}<b>{item.value}</b></span>)}</div></div> : <div className="empty-card"><Fingerprint size={24} /><h3>No category data</h3><p>Categories are calculated from real analyses only.</p></div>}</article></section>
  </div>
}
