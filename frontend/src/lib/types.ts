export type Classification = 'SAFE' | 'SUSPICIOUS' | 'DANGEROUS'

export interface Analysis {
  id: string
  score: number
  classification: Classification
  category: string
  reasons: string[]
  entities: Record<string, unknown>
  component_scores: Record<string, number>
  recommended_action: string
  ai_provider?: string | null
  ai_model?: string | null
  ai_summary?: string | null
  ai_confidence?: number | null
  created_at?: string
}

export interface Campaign {
  id: string
  name: string
  scam_type: string
  status: string
  report_count: number
  fingerprint: Record<string, unknown>
  summary: string
  indicators?: GraphNode[]
}

export interface GraphNode {
  id: string
  type: string
  label?: string
  value?: string
  risk?: number
  risk_score?: number
  reports?: number
  report_count?: number
}

export interface GraphEdge {
  source: string
  target: string
  type: string
  confidence: number
}

export interface PairedDevice {
  id: string
  name: string
  platform: string
  protection_enabled: boolean
  app_version: string
  last_seen: string
  created_at: string
}

export interface PairCode {
  code: string
  expires_at: string
  api_url: string
}
