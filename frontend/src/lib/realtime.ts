export type RealtimeState = 'connecting' | 'live' | 'offline'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function subscribeRealtime(
  onEvent: (event: MessageEvent) => void,
  onState?: (state: RealtimeState) => void,
) {
  onState?.('connecting')
  const source = new EventSource(`${API_BASE}/api/realtime/events`)
  const eventTypes = ['analysis.created', 'device.registered', 'device.event', 'report.created', 'honeypot.started', 'honeypot.turn']
  eventTypes.forEach(type => source.addEventListener(type, onEvent))
  source.onopen = () => onState?.('live')
  source.onerror = () => onState?.('offline')
  return () => source.close()
}
