import { useEffect, useState } from 'react'
import { BrainCircuit, Database, FlaskConical, Scale } from 'lucide-react'
import { PageHeader } from '../components/PageHeader'
import { ErrorBlock, LoadingBlock } from '../components/StateBlock'
import { api } from '../lib/api'

export default function ModelMetrics() {
  const [data, setData] = useState<any>(null); const [error, setError] = useState('')
  useEffect(() => { api.metrics().then(setData).catch(err => setError(err.message)) }, [])
  return <div className="page"><PageHeader eyebrow="ADMIN / EVALUATION" title="Measurable ML, not an AI black box." description="The deterministic classifier provides repeatable metrics; Gemini is an optional backend-only enrichment signal." />{error ? <ErrorBlock message={error} /> : !data ? <LoadingBlock /> : <><section className="metric-grid">{[['accuracy','Accuracy'],['precision','Precision'],['recall','Recall'],['f1','F1 score']].map(([key,label]) => <article className="panel metric-card" key={key}><span>{label}</span><strong>{Math.round(data[key] * 100)}<small>%</small></strong><div><i style={{ width: `${data[key] * 100}%` }} /></div></article>)}</section><section className="model-grid"><article className="panel model-card"><BrainCircuit size={22} /><span>MODEL</span><h2>{data.model_name}</h2><p>Transparent text features and a linear decision boundary make this signal easy to evaluate and explain.</p></article><article className="panel model-card"><Database size={22} /><span>DATASET</span><h2>{data.sample_count} demo samples</h2><p>Balanced synthetic examples cover payments, KYC, utility, delivery, job, reward and everyday safe messages.</p></article><article className="panel model-card"><FlaskConical size={22} /><span>EVALUATION</span><h2>{data.method}</h2><p>Every example is held out once, providing a more reliable demo metric than training-set accuracy.</p></article><article className="panel model-card"><Scale size={22} /><span>WEIGHTING</span><h2>Balanced classes</h2><p>Class weights reduce bias when the real dataset contains many more ordinary messages than scams.</p></article></section><section className="panel limitation"><span>Responsible use</span><p>{data.notes} NAZAR combines this model with deterministic URL, transaction, community and cross-channel consistency checks before making a final decision.</p></section></>}</div>
}

