export type ScreenName = 'home' | 'scan' | 'activity' | 'settings'
export type Classification = 'SAFE' | 'SUSPICIOUS' | 'DANGEROUS'

export interface Pairing {
  apiBase: string
  deviceId: string
  deviceToken: string
  deviceName: string
}

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
}

export interface MobileEvent {
  id: string
  analysis_id: string
  source_label: string
  preview: string
  classification: Classification
  score: number
  acknowledged: boolean
  created_at: string
}
