import type { Analysis, Campaign, GraphEdge, GraphNode, PairCode, PairedDevice } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(detail.detail || 'Request failed')
  }
  return response.json()
}

export const api = {
  dashboard: () => request<Record<string, any>>('/api/dashboard'),
  analyze: (payload: Record<string, unknown>) => request<Analysis>('/api/analyze/full', { method: 'POST', body: JSON.stringify(payload) }),
  analysis: (id: string) => request<Analysis>(`/api/analyze/${id}`),
  report: (payload: Record<string, unknown>) => request<{ id: string; status: string; message: string }>('/api/reports', { method: 'POST', body: JSON.stringify(payload) }),
  campaigns: () => request<Campaign[]>('/api/campaigns'),
  campaign: (id: string) => request<Campaign>(`/api/campaigns/${id}`),
  graph: () => request<{ nodes: GraphNode[]; edges: GraphEdge[] }>('/api/intelligence/graph'),
  metrics: () => request<Record<string, any>>('/api/model/metrics'),
  devices: () => request<PairedDevice[]>('/api/devices'),
  createPairCode: () => request<PairCode>('/api/devices/pair-code', { method: 'POST' }),
  call: (payload: { transcript: string; caller_number?: string }) => request<Analysis>('/api/calls/analyze', { method: 'POST', body: JSON.stringify(payload) }),
  startHoneypot: (analysis_id?: string) => request<any>('/api/honeypot/start', { method: 'POST', body: JSON.stringify({ analysis_id }) }),
  honeypot: (id: string) => request<any>(`/api/honeypot/${id}`),
  sendHoneypot: (id: string, content: string) => request<any>(`/api/honeypot/${id}/message`, { method: 'POST', body: JSON.stringify({ content }) }),
}
