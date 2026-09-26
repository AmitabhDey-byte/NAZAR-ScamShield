# Routes

Framework: React 18, React Router 7, Vite 6.
Layout: every route uses `frontend/src/components/Layout.tsx`.

| Route | Component | Purpose |
|---|---|---|
| / | frontend/src/pages/Dashboard.tsx | Command center and inline analyzer |
| /analyze | frontend/src/pages/Analyze.tsx | Full analysis input |
| /result/:id | frontend/src/pages/Result.tsx | Explainable risk report |
| /honeypot/:id | frontend/src/pages/Honeypot.tsx | Controlled defensive simulation |
| /intelligence | frontend/src/pages/Intelligence.tsx | Threat graph |
| /campaigns | frontend/src/pages/Campaigns.tsx | Campaign list |
| /campaign/:id | frontend/src/pages/CampaignDetail.tsx | Scam DNA and indicators |
| /report | frontend/src/pages/Report.tsx | Community reporting |
| /calls | frontend/src/pages/Calls.tsx | Call transcript analysis |
| /model | frontend/src/pages/ModelMetrics.tsx | ML evaluation |

## Router configuration

```tsx
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

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}

export default function App() {
  return <Suspense fallback={<div className="route-loading"><LoadingBlock /></div>}><ScrollToTop /><Routes><Route element={<Layout />}><Route path="/" element={<Dashboard />} /><Route path="/analyze" element={<Analyze />} /><Route path="/result/:id" element={<Result />} /><Route path="/honeypot/:id" element={<Honeypot />} /><Route path="/intelligence" element={<Intelligence />} /><Route path="/campaigns" element={<Campaigns />} /><Route path="/campaign/:id" element={<CampaignDetail />} /><Route path="/report" element={<Report />} /><Route path="/calls" element={<Calls />} /><Route path="/model" element={<ModelMetrics />} /><Route path="*" element={<Navigate to="/" replace />} /></Route></Routes></Suspense>
}
```
