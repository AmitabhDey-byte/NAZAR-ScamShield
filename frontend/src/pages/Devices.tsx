import { useCallback, useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Clock3, Copy, Link2, RefreshCw, ShieldCheck, Smartphone, Wifi } from 'lucide-react'
import { PageHeader } from '../components/PageHeader'
import { ErrorBlock, LoadingBlock } from '../components/StateBlock'
import { API_BASE, api } from '../lib/api'
import type { PairCode, PairedDevice } from '../lib/types'

function lastSeen(value: string) {
  const date = new Date(value)
  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000))
  if (seconds < 60) return 'Online now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return date.toLocaleDateString()
}

export default function Devices() {
  const [devices, setDevices] = useState<PairedDevice[]>([])
  const [pairCode, setPairCode] = useState<PairCode | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const load = useCallback(async () => {
    try { setDevices(await api.devices()); setError('') }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not load devices') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load(); const timer = window.setInterval(load, 15_000); return () => window.clearInterval(timer) }, [load])
  const apiAddress = useMemo(() => pairCode?.api_url || API_BASE, [pairCode])
  const createCode = async () => {
    setGenerating(true); setCopied(false)
    try { setPairCode(await api.createPairCode()); setError('') }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not create a pairing code') }
    finally { setGenerating(false) }
  }
  const copyCode = async () => {
    if (!pairCode) return
    await navigator.clipboard.writeText(pairCode.code)
    setCopied(true); window.setTimeout(() => setCopied(false), 1500)
  }

  return <div className="page devices-page">
    <PageHeader eyebrow="MOBILE COMPANION" title="Your phones, one defense console." description="Pair the NAZAR Expo Go app, review its submitted scans here, and see whether each companion is online." action={<button className="button secondary" onClick={load}><RefreshCw size={16} />Refresh devices</button>} />
    <section className="device-layout">
      <article className="panel pairing-panel">
        <div className="pairing-icon"><Link2 size={24} /></div>
        <span className="panel-kicker">PAIR A PHONE</span>
        <h2>Connect Expo Go</h2>
        <p>Generate a one-time code, then enter it in the mobile app with the API address below. The code expires after 10 minutes.</p>
        {pairCode ? <div className="pair-code-card">
          <div><span>ONE-TIME CODE</span><strong>{pairCode.code}</strong></div>
          <button className="icon-button" onClick={copyCode} aria-label="Copy pairing code">{copied ? <CheckCircle2 size={18} /> : <Copy size={18} />}</button>
        </div> : <button className="button primary pair-button" disabled={generating} onClick={createCode}><Smartphone size={17} />{generating ? 'Generating…' : 'Generate pairing code'}</button>}
        {pairCode && <button className="button secondary new-code-button" disabled={generating} onClick={createCode}>{generating ? 'Generating…' : 'Generate a new code'}</button>}
        <div className="api-address"><Wifi size={16} /><div><span>PHONE API ADDRESS</span><code>{apiAddress}</code></div></div>
        <div className="pairing-note"><ShieldCheck size={17} /><p>Expo Go mode scans only pasted content, clipboard content, and QR codes you choose. Passive notification monitoring requires a later Android development build.</p></div>
      </article>
      <article className="panel devices-panel">
        <div className="panel-heading"><div><span className="panel-kicker">PAIRED DEVICES</span><h2>Companion status</h2></div><span className="device-count">{devices.length.toString().padStart(2, '0')}</span></div>
        {loading ? <LoadingBlock /> : error ? <ErrorBlock message={error} retry={load} /> : devices.length ? <div className="device-list">{devices.map(device => <div className="device-row" key={device.id}>
          <div className="device-platform"><Smartphone size={21} /></div>
          <div className="device-main"><strong>{device.name}</strong><span>{device.platform.toUpperCase()} · EXPO GO {device.app_version}</span></div>
          <div className="device-state"><span className={lastSeen(device.last_seen) === 'Online now' ? 'online' : ''}><i />{lastSeen(device.last_seen)}</span><small>{device.protection_enabled ? 'Companion enabled' : 'Companion paused'}</small></div>
        </div>)}</div> : <div className="device-empty"><Smartphone size={34} /><h3>No phone paired yet</h3><p>Generate a code and connect the NAZAR mobile companion.</p></div>}
      </article>
    </section>
    <section className="device-steps">
      {[['01','Start the services','Run the API on 0.0.0.0 so your phone can reach it over Wi-Fi.'],['02','Open Expo Go','Scan the Expo QR, open Settings, and choose Pair a desktop console.'],['03','Analyze and sync','Submit suspicious text or QR data; the decision appears on both devices.']].map(([index,title,copy]) => <article className="panel" key={index}><span>{index}</span><div><h3>{title}</h3><p>{copy}</p></div></article>)}
    </section>
  </div>
}
