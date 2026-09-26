import { useEffect, useState } from 'react'
import { PageHeader } from '../components/PageHeader'
import { ThreatGraph } from '../components/ThreatGraph'
import { ErrorBlock, LoadingBlock } from '../components/StateBlock'
import { api } from '../lib/api'

export default function Intelligence() {
  const [graph, setGraph] = useState<any>(null); const [error, setError] = useState('')
  useEffect(() => { api.graph().then(setGraph).catch(err => setError(err.message)) }, [])
  return <div className="page"><PageHeader eyebrow="SHARE / THREAT GRAPH" title="Follow the infrastructure, not the alias." description="Connected phone numbers, UPI IDs, domains and message patterns reveal shared scam operations." />{error ? <ErrorBlock message={error} /> : !graph ? <LoadingBlock /> : <section className="panel graph-panel"><div className="graph-toolbar"><div className="graph-legend">{['PHONE','UPI','DOMAIN','CAMPAIGN'].map(type => <span key={type}><i className={type.toLowerCase()} />{type}</span>)}</div><span>{graph.nodes.length} nodes · {graph.edges.length} relationships</span></div><ThreatGraph nodes={graph.nodes} edges={graph.edges} /></section>}</div>
}

