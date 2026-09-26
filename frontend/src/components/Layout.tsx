import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { Activity, BarChart3, BrainCircuit, FileWarning, Network, PhoneCall, Radar, ScanSearch, ShieldCheck, Smartphone } from 'lucide-react'
import { Logo } from './Logo'
import { subscribeRealtime, type RealtimeState } from '../lib/realtime'

const nav = [
  { to: '/', label: 'Command center', icon: Radar, end: true },
  { to: '/devices', label: 'Mobile devices', icon: Smartphone },
  { to: '/analyze', label: 'Analyze threat', icon: ScanSearch },
  { to: '/intelligence', label: 'Intelligence', icon: Network },
  { to: '/campaigns', label: 'Campaigns', icon: Activity },
  { to: '/report', label: 'Community report', icon: FileWarning },
  { to: '/calls', label: 'Analyze call', icon: PhoneCall },
  { to: '/model', label: 'Model metrics', icon: BrainCircuit },
]

export function Layout() {
  const [realtime, setRealtime] = useState<RealtimeState>('connecting')
  useEffect(() => subscribeRealtime(() => undefined, setRealtime), [])
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-top"><Logo /><span className="version">v1.0</span></div>
        <div className="phase-strip" aria-label="Defense lifecycle">
          {['Sense', 'Think', 'Deceive', 'Share'].map((item, index) => <span key={item} className={index < 2 ? 'active' : ''}>{item}</span>)}
        </div>
        <nav aria-label="Primary navigation">
          {nav.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-item ${isActive ? 'is-active' : ''}`}>
              <Icon size={18} strokeWidth={1.8} /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="system-card">
          <ShieldCheck size={18} />
          <div><strong>Defense service</strong><span>Rules + ML + Gemini</span></div>
          <i className="status-dot" />
        </div>
      </aside>
      <main className="main-shell">
        <header className="topbar">
          <div className="mobile-brand"><Logo compact /></div>
          <div className="breadcrumb"><span>NAZAR</span><b>/</b><span>Scam defense operations</span></div>
          <div className="top-actions"><span className={`live-pill ${realtime}`}><i /> {realtime === 'live' ? 'LIVE DATA' : realtime.toUpperCase()}</span><button className="icon-button" aria-label="Open activity"><BarChart3 size={18} /></button></div>
        </header>
        <Outlet />
      </main>
      <nav className="mobile-nav" aria-label="Mobile navigation">
        {nav.slice(0, 5).map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} aria-label={label}><Icon size={20} /><span>{label.split(' ')[0]}</span></NavLink>
        ))}
      </nav>
    </div>
  )
}
