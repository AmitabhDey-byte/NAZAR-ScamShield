import type { Analysis, MobileEvent, Pairing } from './types'
import { Platform } from 'react-native'

export const DEFAULT_API_BASE = (
  process.env.EXPO_PUBLIC_API_BASE_URL || 'https://nazar-scamshield.onrender.com'
).replace(/\/$/, '')

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(body.detail || `Request failed (${response.status})`)
  }
  return response.json()
}

export async function pairDevice(apiBase: string, code: string, name: string): Promise<Pairing> {
  const base = apiBase.replace(/\/$/, '')
  const result = await request<{ device: { id: string; name: string }; device_token: string }>(`${base}/api/devices/register`, {
    method: 'POST',
    body: JSON.stringify({ pair_code: code, device_name: name, platform: Platform.OS, app_version: '1.0.0' }),
  })
  return { apiBase: base, deviceId: result.device.id, deviceToken: result.device_token, deviceName: result.device.name }
}

export async function analyzeFromPhone(pairing: Pairing | null, text: string, sourceLabel: string): Promise<Analysis> {
  if (pairing) {
    const result = await request<{ analysis: Analysis }>(`${pairing.apiBase}/api/devices/${pairing.deviceId}/events`, {
      method: 'POST',
      headers: { 'X-Device-Token': pairing.deviceToken },
      body: JSON.stringify({ text, source_package: 'expo-go', source_label: sourceLabel }),
    })
    return result.analysis
  }
  throw new Error('Pair this phone with the desktop console before scanning.')
}

export function fetchDeviceEvents(pairing: Pairing): Promise<MobileEvent[]> {
  return request(`${pairing.apiBase}/api/devices/${pairing.deviceId}/events`, {
    headers: { 'X-Device-Token': pairing.deviceToken },
  })
}

export function fetchDeviceFeed(pairing: Pairing): Promise<MobileEvent[]> {
  return request(`${pairing.apiBase}/api/devices/${pairing.deviceId}/feed`, {
    headers: { 'X-Device-Token': pairing.deviceToken },
  })
}

export function heartbeat(pairing: Pairing, protectionEnabled: boolean) {
  return request(`${pairing.apiBase}/api/devices/${pairing.deviceId}/heartbeat?protection_enabled=${protectionEnabled}`, {
    method: 'POST', headers: { 'X-Device-Token': pairing.deviceToken },
  })
}
