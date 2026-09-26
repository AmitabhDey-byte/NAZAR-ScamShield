import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Layout } from './components/Layout'
import { LoadingBlock } from './components/StateBlock'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Analyze = lazy(() => import('./pages/Analyze'))
const Result = lazy(() => import('./pages/Result'))
const Honeypot = lazy(() => import('./pages/Honeypot'))
const Intelligence = lazy(() => import('./pages/Intelligence'))
const Campaigns = lazy(() => import('./pages/Campaigns'))
const CampaignDetail = lazy(() => import('./pages/CampaignDetail'))
const Report = lazy(() => import('./pages/Report'))
const Calls = lazy(() => import('./pages/Calls'))
const ModelMetrics = lazy(() => import('./pages/ModelMetrics'))
const Devices = lazy(() => import('./pages/Devices'))

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}

export default function App() {
  return <Suspense fallback={<div className="route-loading"><LoadingBlock /></div>}><ScrollToTop /><Routes><Route element={<Layout />}><Route path="/" element={<Dashboard />} /><Route path="/devices" element={<Devices />} /><Route path="/analyze" element={<Analyze />} /><Route path="/result/:id" element={<Result />} /><Route path="/honeypot/:id" element={<Honeypot />} /><Route path="/intelligence" element={<Intelligence />} /><Route path="/campaigns" element={<Campaigns />} /><Route path="/campaign/:id" element={<CampaignDetail />} /><Route path="/report" element={<Report />} /><Route path="/calls" element={<Calls />} /><Route path="/model" element={<ModelMetrics />} /><Route path="*" element={<Navigate to="/" replace />} /></Route></Routes></Suspense>
}
