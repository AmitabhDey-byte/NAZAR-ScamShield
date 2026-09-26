import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native'
import { StatusBar } from 'expo-status-bar'
import { CameraView, useCameraPermissions } from 'expo-camera'
import * as Clipboard from 'expo-clipboard'
import AsyncStorage from '@react-native-async-storage/async-storage'
import {
  Activity,
  AlertOctagon,
  ArrowRight,
  Camera,
  CheckCircle2,
  ChevronRight,
  ClipboardPaste,
  Eye,
  Link2,
  LockKeyhole,
  Monitor,
  Radar,
  RefreshCw,
  ScanLine,
  Settings,
  ShieldCheck,
  Smartphone,
  TriangleAlert,
  Unlink,
  Wifi,
  X,
} from 'lucide-react-native'

import { analyzeFromPhone, DEFAULT_API_BASE, fetchDeviceFeed, heartbeat, pairDevice } from './src/api'
import { colors } from './src/theme'
import type { Analysis, MobileEvent, Pairing, ScreenName } from './src/types'

const PAIRING_KEY = 'nazar.pairing.v1'

function Logo() {
  return <View style={styles.logo}><View style={styles.logoMark}><View style={styles.logoSlashA} /><View style={styles.logoSlashB} /><View style={styles.logoDot} /></View><Text style={styles.logoText}>NAZAR</Text></View>
}

function StatusBadge({ online }: { online: boolean }) {
  return <View style={[styles.statusBadge, online && styles.statusBadgeOnline]}><View style={[styles.statusDot, online && { backgroundColor: colors.safe }]} /><Text style={[styles.statusBadgeText, online && { color: colors.safe }]}>{online ? 'DESKTOP LINKED' : 'NOT PAIRED'}</Text></View>
}

function RiskMark({ classification, size = 15 }: { classification: string; size?: number }) {
  if (classification === 'DANGEROUS') return <AlertOctagon size={size} color={colors.danger} />
  if (classification === 'SUSPICIOUS') return <TriangleAlert size={size} color={colors.warning} />
  return <CheckCircle2 size={size} color={colors.safe} />
}

function EventRow({ event }: { event: MobileEvent }) {
  const time = new Date(event.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return <View style={styles.eventRow}><View style={styles.eventIcon}><RiskMark classification={event.classification} /></View><View style={styles.eventCopy}><Text style={styles.eventSource}>{event.source_label}</Text><Text numberOfLines={2} style={styles.eventPreview}>{event.preview}</Text><Text style={styles.eventMeta}>{time} · {event.classification}</Text></View><View style={styles.eventScore}><Text style={styles.eventScoreText}>{Math.round(event.score)}</Text><ChevronRight size={14} color={colors.quiet} /></View></View>
}

function BottomNav({ screen, setScreen }: { screen: ScreenName; setScreen: (screen: ScreenName) => void }) {
  const items = [
    { id: 'home' as const, label: 'Protect', icon: ShieldCheck },
    { id: 'scan' as const, label: 'Scan', icon: ScanLine },
    { id: 'activity' as const, label: 'Activity', icon: Activity },
    { id: 'settings' as const, label: 'Settings', icon: Settings },
  ]
  return <View style={styles.bottomNav}>{items.map(({ id, label, icon: Icon }) => <Pressable key={id} onPress={() => setScreen(id)} style={styles.navItem}><Icon size={21} color={screen === id ? colors.gold : colors.quiet} strokeWidth={screen === id ? 2.2 : 1.7} /><Text style={[styles.navLabel, screen === id && styles.navLabelActive]}>{label}</Text>{screen === id && <View style={styles.navIndicator} />}</Pressable>)}</View>
}

function PairModal({ visible, onClose, onPaired }: { visible: boolean; onClose: () => void; onPaired: (pairing: Pairing) => void }) {
  const [apiBase, setApiBase] = useState(DEFAULT_API_BASE)
  const [code, setCode] = useState('')
  const [name, setName] = useState(Platform.OS === 'ios' ? 'My iPhone' : 'My Android')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const connect = async () => {
    setBusy(true); setError('')
    try {
      const pairing = await pairDevice(apiBase.trim(), code.trim(), name.trim())
      await AsyncStorage.setItem(PAIRING_KEY, JSON.stringify(pairing))
      onPaired(pairing)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not pair this phone') }
    finally { setBusy(false) }
  }
  return <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}><KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.modalShade}><View style={styles.pairSheet}><View style={styles.sheetHandle} /><View style={styles.sheetHeader}><View><Text style={styles.kicker}>SECURE DEVICE LINK</Text><Text style={styles.sheetTitle}>Pair with NAZAR Desktop</Text></View><Pressable onPress={onClose} style={styles.iconButton}><X size={19} color={colors.muted} /></Pressable></View><Text style={styles.sheetBody}>On the computer, open Devices and generate a six-digit pairing code. Both devices must reach the same NAZAR API.</Text><Text style={styles.inputLabel}>NAZAR API ADDRESS</Text><TextInput value={apiBase} onChangeText={setApiBase} autoCapitalize="none" keyboardType="url" placeholder="https://nazar-scamshield.onrender.com" placeholderTextColor={colors.quiet} style={styles.input} /><Text style={styles.inputLabel}>PAIRING CODE</Text><TextInput value={code} onChangeText={value => setCode(value.replace(/\D/g, '').slice(0, 6))} keyboardType="number-pad" placeholder="000000" placeholderTextColor={colors.quiet} style={[styles.input, styles.codeInput]} /><Text style={styles.inputLabel}>DEVICE NAME</Text><TextInput value={name} onChangeText={setName} placeholder="My phone" placeholderTextColor={colors.quiet} style={styles.input} />{error ? <Text style={styles.errorText}>{error}</Text> : null}<Pressable disabled={busy || code.length !== 6 || !name.trim()} onPress={connect} style={({ pressed }) => [styles.primaryButton, (pressed || busy || code.length !== 6) && { opacity: .55 }]}>{busy ? <ActivityIndicator color={colors.canvas} /> : <><Link2 size={18} color={colors.canvas} /><Text style={styles.primaryButtonText}>Pair this phone</Text><ArrowRight size={17} color={colors.canvas} /></>}</Pressable><View style={styles.privacyLine}><LockKeyhole size={14} color={colors.safe} /><Text style={styles.privacyText}>The device token stays only on this phone.</Text></View></View></KeyboardAvoidingView></Modal>
}

function ResultModal({ result, onClose }: { result: Analysis | null; onClose: () => void }) {
  if (!result) return null
  const tone = result.classification === 'DANGEROUS' ? colors.danger : result.classification === 'SUSPICIOUS' ? colors.warning : colors.safe
  return <Modal visible transparent animationType="slide" onRequestClose={onClose}><View style={styles.modalShade}><View style={styles.resultSheet}><View style={styles.sheetHandle} /><View style={styles.resultTop}><View style={[styles.resultScoreRing, { borderColor: tone }]}><Text style={[styles.resultScore, { color: tone }]}>{Math.round(result.score)}</Text><Text style={styles.resultOutOf}>/100</Text></View><View style={styles.resultHeading}><View style={styles.resultBadge}><RiskMark classification={result.classification} /><Text style={{ color: tone }}>{result.classification}</Text></View><Text style={styles.resultTitle}>{result.classification === 'DANGEROUS' ? 'Stop. Do not pay or open the link.' : result.classification === 'SUSPICIOUS' ? 'Pause and verify independently.' : 'No strong scam signals found.'}</Text></View></View><View style={[styles.actionCard, { borderColor: `${tone}55` }]}><Text style={styles.actionLabel}>RECOMMENDED ACTION</Text><Text style={styles.actionText}>{result.recommended_action}</Text></View><Text style={styles.sectionLabel}>WHY THIS DECISION</Text><ScrollView style={{ maxHeight: 220 }}>{result.reasons.slice(0, 6).map((reason, index) => <View key={reason} style={styles.reasonRow}><Text style={styles.reasonIndex}>{String(index + 1).padStart(2, '0')}</Text><Text style={styles.reasonText}>{reason}</Text></View>)}</ScrollView><Pressable onPress={onClose} style={styles.secondaryButton}><Text style={styles.secondaryButtonText}>Done</Text></Pressable></View></View></Modal>
}

export default function App() {
  const [screen, setScreen] = useState<ScreenName>('home')
  const [pairing, setPairing] = useState<Pairing | null>(null)
  const [pairOpen, setPairOpen] = useState(false)
  const [events, setEvents] = useState<MobileEvent[]>([])
  const [protectionEnabled, setProtectionEnabled] = useState(true)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [result, setResult] = useState<Analysis | null>(null)

  const syncEvents = useCallback(async (active = pairing) => {
    if (!active) return
    setSyncing(true)
    try { setEvents(await fetchDeviceFeed(active)); await heartbeat(active, protectionEnabled) }
    catch { /* Offline is shown through the last-sync state. */ }
    finally { setSyncing(false) }
  }, [pairing, protectionEnabled])

  useEffect(() => {
    AsyncStorage.getItem(PAIRING_KEY).then(raw => { if (raw) setPairing(JSON.parse(raw)) }).finally(() => setLoading(false))
  }, [])
  useEffect(() => { if (pairing) syncEvents(pairing) }, [pairing, syncEvents])
  useEffect(() => {
    if (!pairing || !protectionEnabled) return
    const interval = setInterval(() => syncEvents(pairing), 30_000)
    return () => clearInterval(interval)
  }, [pairing, protectionEnabled, syncEvents])

  const dangerous = events.filter(event => event.classification === 'DANGEROUS').length
  const online = Boolean(pairing)
  const page = useMemo(() => {
    if (screen === 'scan') return <ScanScreen pairing={pairing} onResult={setResult} onPair={() => setPairOpen(true)} />
    if (screen === 'activity') return <ActivityScreen events={events} syncing={syncing} onSync={() => syncEvents()} paired={online} onPair={() => setPairOpen(true)} />
    if (screen === 'settings') return <SettingsScreen pairing={pairing} enabled={protectionEnabled} setEnabled={value => { setProtectionEnabled(value); if (pairing) heartbeat(pairing, value).catch(() => undefined) }} onPair={() => setPairOpen(true)} onUnpair={async () => { await AsyncStorage.removeItem(PAIRING_KEY); setPairing(null); setEvents([]); setScreen('home') }} />
    return <HomeScreen pairing={pairing} events={events} dangerous={dangerous} enabled={protectionEnabled} loading={loading} syncing={syncing} onPair={() => setPairOpen(true)} onScan={() => setScreen('scan')} onActivity={() => setScreen('activity')} onSync={() => syncEvents()} />
  }, [screen, pairing, events, dangerous, protectionEnabled, loading, syncing, syncEvents, online])

  return <SafeAreaView style={styles.safe}><StatusBar style="light" /><View style={styles.app}>{page}<BottomNav screen={screen} setScreen={setScreen} /></View><PairModal visible={pairOpen} onClose={() => setPairOpen(false)} onPaired={value => { setPairing(value); setPairOpen(false) }} /><ResultModal result={result} onClose={() => setResult(null)} /></SafeAreaView>
}

function ScreenHeader({ paired }: { paired: boolean }) {
  return <View style={styles.header}><Logo /><StatusBadge online={paired} /></View>
}

function HomeScreen({ pairing, events, dangerous, enabled, loading, syncing, onPair, onScan, onActivity, onSync }: { pairing: Pairing | null; events: MobileEvent[]; dangerous: number; enabled: boolean; loading: boolean; syncing: boolean; onPair: () => void; onScan: () => void; onActivity: () => void; onSync: () => void }) {
  return <ScrollView contentContainerStyle={styles.screen} showsVerticalScrollIndicator={false}><ScreenHeader paired={Boolean(pairing)} /><View style={styles.greeting}><Text style={styles.kicker}>MOBILE DEFENSE</Text><Text style={styles.pageTitle}>Your pocket scam shield.</Text><Text style={styles.pageSubtitle}>Scan before you tap, pay, or trust.</Text></View><View style={styles.protectionCard}><View style={styles.radarHaloOuter}><View style={styles.radarHalo}><View style={[styles.shieldCore, !enabled && { opacity: .45 }]}>{enabled ? <ShieldCheck size={42} color={colors.gold} /> : <Eye size={42} color={colors.quiet} />}</View></View></View><Text style={styles.protectionTitle}>{enabled ? 'Companion protection is ready' : 'Companion protection is paused'}</Text><Text style={styles.protectionCopy}>Expo Go scans only what you choose: pasted text, clipboard content, and QR codes.</Text><View style={styles.protectionMeta}><View style={styles.metaItem}><Wifi size={14} color={pairing ? colors.safe : colors.quiet} /><Text style={styles.metaText}>{pairing ? 'Desktop synced' : 'Pair a desktop'}</Text></View><View style={styles.metaItem}><LockKeyhole size={14} color={colors.safe} /><Text style={styles.metaText}>Private by default</Text></View></View></View>{!pairing && <Pressable onPress={onPair} style={styles.pairBanner}><View style={styles.pairBannerIcon}><Monitor size={22} color={colors.gold} /></View><View style={{ flex: 1 }}><Text style={styles.pairBannerTitle}>Connect your command center</Text><Text style={styles.pairBannerCopy}>Pair this phone to send incidents to the desktop.</Text></View><ArrowRight size={18} color={colors.gold} /></Pressable>}<View style={styles.quickGrid}><Pressable onPress={onScan} style={styles.quickPrimary}><ScanLine size={24} color={colors.canvas} /><Text style={styles.quickPrimaryTitle}>Scan a threat</Text><ArrowRight size={17} color={colors.canvas} /></Pressable><Pressable onPress={onActivity} style={styles.quickCard}><Activity size={23} color={colors.gold} /><Text style={styles.quickCount}>{events.length}</Text><Text style={styles.quickLabel}>Signals synced</Text></Pressable></View><View style={styles.metricsRow}><View style={styles.metricItem}><Text style={styles.metricValue}>{dangerous}</Text><Text style={styles.metricLabel}>Blocked risks</Text></View><View style={styles.metricDivider} /><View style={styles.metricItem}><Text style={styles.metricValue}>{events.length ? Math.round(events.reduce((sum, event) => sum + event.score, 0) / events.length) : 0}</Text><Text style={styles.metricLabel}>Avg. risk</Text></View><View style={styles.metricDivider} /><View style={styles.metricItem}><Text style={styles.metricValue}>{pairing ? 'ON' : '—'}</Text><Text style={styles.metricLabel}>Desktop link</Text></View></View><View style={styles.sectionHeader}><View><Text style={styles.sectionLabel}>RECENT SIGNALS</Text><Text style={styles.sectionTitle}>From this phone</Text></View><Pressable onPress={onSync} style={styles.refreshButton}>{syncing ? <ActivityIndicator size="small" color={colors.gold} /> : <RefreshCw size={16} color={colors.gold} />}</Pressable></View>{loading ? <ActivityIndicator color={colors.gold} style={{ marginTop: 28 }} /> : events.length ? <View style={styles.listCard}>{events.slice(0, 3).map(event => <EventRow key={event.id} event={event} />)}</View> : <View style={styles.emptyCard}><Radar size={26} color={colors.bronze} /><Text style={styles.emptyTitle}>No signals yet</Text><Text style={styles.emptyCopy}>{pairing ? 'Your scans will appear here and on the desktop.' : 'Pair the phone, then scan a suspicious message or QR.'}</Text></View>}</ScrollView>
}

function ScanScreen({ pairing, onResult, onPair }: { pairing: Pairing | null; onResult: (result: Analysis) => void; onPair: () => void }) {
  const [text, setText] = useState('')
  const [cameraOpen, setCameraOpen] = useState(false)
  const [scanned, setScanned] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [permission, requestPermission] = useCameraPermissions()
  const analyze = async (source = 'Pasted message') => {
    if (!pairing) { onPair(); return }
    if (text.trim().length < 3) { setError('Paste a message, URL, or QR value first.'); return }
    setBusy(true); setError('')
    try { onResult(await analyzeFromPhone(pairing, text.trim(), source)) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Analysis failed') }
    finally { setBusy(false) }
  }
  const openCamera = async () => {
    if (!permission?.granted) { const result = await requestPermission(); if (!result.granted) { setError('Camera permission is required to scan a QR code.'); return } }
    setScanned(false); setCameraOpen(true)
  }
  return <ScrollView contentContainerStyle={styles.screen} keyboardShouldPersistTaps="handled"><ScreenHeader paired={Boolean(pairing)} /><View style={styles.greeting}><Text style={styles.kicker}>SENSE + THINK</Text><Text style={styles.pageTitle}>Check it before you act.</Text><Text style={styles.pageSubtitle}>NAZAR explains the signal, not just the score.</Text></View><View style={styles.scanTools}><Pressable onPress={async () => { const value = await Clipboard.getStringAsync(); if (value) setText(value); else setError('Clipboard is empty.') }} style={styles.toolButton}><ClipboardPaste size={20} color={colors.gold} /><Text style={styles.toolButtonText}>Paste clipboard</Text></Pressable><Pressable onPress={openCamera} style={styles.toolButton}><Camera size={20} color={colors.gold} /><Text style={styles.toolButtonText}>Scan QR</Text></Pressable></View>{cameraOpen && <View style={styles.cameraCard}><CameraView style={StyleSheet.absoluteFill} barcodeScannerSettings={{ barcodeTypes: ['qr'] }} onBarcodeScanned={scanned ? undefined : ({ data }) => { setScanned(true); setText(data); setCameraOpen(false) }} /><Pressable onPress={() => setCameraOpen(false)} style={styles.cameraClose}><X size={18} color={colors.text} /></Pressable><View style={styles.qrFrame} /></View>}<View style={styles.inputCard}><View style={styles.inputCardHeader}><View><Text style={styles.sectionLabel}>MESSAGE, URL OR PAYMENT REQUEST</Text><Text style={styles.inputHint}>Authentication-code notifications are never accepted.</Text></View><Link2 size={18} color={colors.bronze} /></View><TextInput value={text} onChangeText={setText} multiline textAlignVertical="top" placeholder="Paste suspicious content…" placeholderTextColor={colors.quiet} style={styles.scanInput} /><View style={styles.signalChips}><Text style={styles.signalChip}>UPI</Text><Text style={styles.signalChip}>URL</Text><Text style={styles.signalChip}>URGENCY</Text><Text style={styles.signalChip}>AMOUNT</Text></View></View>{error ? <Text style={styles.errorText}>{error}</Text> : null}<Pressable onPress={() => analyze(cameraOpen ? 'QR code' : 'Mobile scan')} disabled={busy} style={({ pressed }) => [styles.primaryButton, (pressed || busy) && { opacity: .6 }]}>{busy ? <ActivityIndicator color={colors.canvas} /> : <><ScanLine size={19} color={colors.canvas} /><Text style={styles.primaryButtonText}>Analyze and sync</Text><ArrowRight size={17} color={colors.canvas} /></>}</Pressable><View style={styles.explainer}><ShieldCheck size={18} color={colors.safe} /><View style={{ flex: 1 }}><Text style={styles.explainerTitle}>What gets sent?</Text><Text style={styles.explainerCopy}>Only the content you submit and the resulting threat indicators. NAZAR skips OTP/code notifications.</Text></View></View></ScrollView>
}

function ActivityScreen({ events, syncing, onSync, paired, onPair }: { events: MobileEvent[]; syncing: boolean; onSync: () => void; paired: boolean; onPair: () => void }) {
  return <ScrollView contentContainerStyle={styles.screen}><ScreenHeader paired={paired} /><View style={styles.titleRow}><View style={styles.greeting}><Text style={styles.kicker}>SYNCED INTELLIGENCE</Text><Text style={styles.pageTitle}>Activity</Text><Text style={styles.pageSubtitle}>Signals collected from this device.</Text></View><Pressable onPress={onSync} style={styles.refreshButton}>{syncing ? <ActivityIndicator size="small" color={colors.gold} /> : <RefreshCw size={17} color={colors.gold} />}</Pressable></View>{!paired ? <View style={styles.emptyCard}><Smartphone size={28} color={colors.bronze} /><Text style={styles.emptyTitle}>This phone is not paired</Text><Text style={styles.emptyCopy}>Connect a desktop console to sync and investigate incidents.</Text><Pressable onPress={onPair} style={styles.secondaryButton}><Text style={styles.secondaryButtonText}>Pair device</Text></Pressable></View> : events.length ? <View style={styles.listCard}>{events.map(event => <EventRow key={event.id} event={event} />)}</View> : <View style={styles.emptyCard}><Activity size={28} color={colors.bronze} /><Text style={styles.emptyTitle}>The timeline is clear</Text><Text style={styles.emptyCopy}>Run a scan and the incident will appear here.</Text></View>}</ScrollView>
}

function SettingsScreen({ pairing, enabled, setEnabled, onPair, onUnpair }: { pairing: Pairing | null; enabled: boolean; setEnabled: (value: boolean) => void; onPair: () => void; onUnpair: () => void }) {
  const confirmUnpair = () => Alert.alert('Unpair this phone?', 'Local pairing credentials will be removed. Existing desktop incidents remain available.', [{ text: 'Cancel', style: 'cancel' }, { text: 'Unpair', style: 'destructive', onPress: onUnpair }])
  return <ScrollView contentContainerStyle={styles.screen}><ScreenHeader paired={Boolean(pairing)} /><View style={styles.greeting}><Text style={styles.kicker}>PRIVACY + CONNECTION</Text><Text style={styles.pageTitle}>Settings</Text><Text style={styles.pageSubtitle}>You decide what NAZAR can inspect and sync.</Text></View><Text style={styles.sectionLabel}>PROTECTION</Text><View style={styles.settingsCard}><View style={styles.settingRow}><View style={styles.settingIcon}><ShieldCheck size={18} color={colors.gold} /></View><View style={styles.settingCopy}><Text style={styles.settingTitle}>Companion mode</Text><Text style={styles.settingSubtitle}>Allow scans and desktop sync</Text></View><Switch value={enabled} onValueChange={setEnabled} trackColor={{ false: colors.panelStrong, true: colors.bronze }} thumbColor={enabled ? colors.gold : colors.quiet} /></View><View style={styles.settingRow}><View style={styles.settingIcon}><Eye size={18} color={colors.quiet} /></View><View style={styles.settingCopy}><Text style={[styles.settingTitle, { color: colors.quiet }]}>Passive Android monitoring</Text><Text style={styles.settingSubtitle}>Requires a development build</Text></View><View style={styles.disabledPill}><Text style={styles.disabledPillText}>UNAVAILABLE</Text></View></View></View><Text style={styles.sectionLabel}>EXPO GO SOURCES</Text><View style={styles.settingsCard}>{[[ClipboardPaste,'Clipboard scan','Only when you tap Paste'],[Camera,'QR camera','Only while the scanner is open'],[Activity,'Synced alerts','From your paired NAZAR backend']].map(([Icon,title,subtitle]) => { const I = Icon as typeof Camera; return <View style={styles.settingRow} key={String(title)}><View style={styles.settingIcon}><I size={18} color={colors.info} /></View><View style={styles.settingCopy}><Text style={styles.settingTitle}>{String(title)}</Text><Text style={styles.settingSubtitle}>{String(subtitle)}</Text></View><CheckCircle2 size={17} color={colors.safe} /></View> })}</View><Text style={styles.sectionLabel}>PAIRED DESKTOP</Text><View style={styles.settingsCard}>{pairing ? <><View style={styles.deviceCard}><View style={styles.deviceAvatar}><Monitor size={22} color={colors.gold} /></View><View style={{ flex: 1 }}><Text style={styles.deviceTitle}>{pairing.deviceName}</Text><Text style={styles.deviceAddress} numberOfLines={1}>{pairing.apiBase}</Text></View></View><Pressable onPress={confirmUnpair} style={styles.unpairButton}><Unlink size={16} color={colors.danger} /><Text style={styles.unpairText}>Unpair this phone</Text></Pressable></> : <Pressable onPress={onPair} style={styles.pairRow}><View style={styles.settingIcon}><Link2 size={18} color={colors.gold} /></View><View style={styles.settingCopy}><Text style={styles.settingTitle}>Pair a desktop console</Text><Text style={styles.settingSubtitle}>Required for analysis and incident sync</Text></View><ChevronRight size={17} color={colors.quiet} /></Pressable>}</View><View style={styles.versionRow}><Logo /><Text style={styles.versionText}>Expo Go companion · v1.0.0</Text></View></ScrollView>
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.canvas }, app: { flex: 1, backgroundColor: colors.canvas }, screen: { paddingHorizontal: 18, paddingTop: Platform.OS === 'android' ? 24 : 8, paddingBottom: 112 },
  header: { minHeight: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }, logo: { flexDirection: 'row', alignItems: 'center', gap: 9 }, logoMark: { width: 29, height: 29, borderRadius: 8, borderWidth: 1, borderColor: 'rgba(223,189,122,.35)', backgroundColor: 'rgba(185,144,85,.08)', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }, logoSlashA: { position: 'absolute', width: 16, height: 2, backgroundColor: colors.gold, transform: [{ rotate: '39deg' }] }, logoSlashB: { position: 'absolute', width: 16, height: 2, backgroundColor: colors.gold, transform: [{ rotate: '-39deg' }] }, logoDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: colors.danger }, logoText: { color: colors.text, fontSize: 18, fontWeight: '800', letterSpacing: -0.7 },
  statusBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingVertical: 7, paddingHorizontal: 9, borderRadius: 30, borderWidth: 1, borderColor: colors.line, backgroundColor: 'rgba(255,255,255,.02)' }, statusBadgeOnline: { borderColor: 'rgba(114,201,139,.18)', backgroundColor: 'rgba(114,201,139,.05)' }, statusDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: colors.quiet }, statusBadgeText: { color: colors.quiet, fontSize: 8, fontWeight: '700', letterSpacing: 1 },
  greeting: { marginTop: 27, marginBottom: 22 }, kicker: { color: colors.bronze, fontSize: 10, fontWeight: '700', letterSpacing: 1.6 }, pageTitle: { color: colors.text, fontSize: 31, fontWeight: '700', letterSpacing: -1.3, marginTop: 7 }, pageSubtitle: { color: colors.muted, fontSize: 14, lineHeight: 21, marginTop: 5 },
  protectionCard: { borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, borderRadius: 22, padding: 22, alignItems: 'center', overflow: 'hidden' }, radarHaloOuter: { width: 154, height: 154, borderRadius: 77, borderWidth: 1, borderColor: 'rgba(185,144,85,.08)', alignItems: 'center', justifyContent: 'center', marginBottom: 17 }, radarHalo: { width: 122, height: 122, borderRadius: 61, borderWidth: 1, borderColor: 'rgba(185,144,85,.14)', backgroundColor: 'rgba(185,144,85,.03)', alignItems: 'center', justifyContent: 'center' }, shieldCore: { width: 84, height: 84, borderRadius: 42, borderWidth: 1, borderColor: 'rgba(223,189,122,.32)', backgroundColor: 'rgba(185,144,85,.09)', alignItems: 'center', justifyContent: 'center' }, protectionTitle: { color: colors.text, fontSize: 18, fontWeight: '700', letterSpacing: -.4 }, protectionCopy: { color: colors.muted, textAlign: 'center', fontSize: 12, lineHeight: 18, maxWidth: 290, marginTop: 7 }, protectionMeta: { width: '100%', marginTop: 18, paddingTop: 15, borderTopWidth: 1, borderTopColor: colors.line, flexDirection: 'row', justifyContent: 'space-around' }, metaItem: { flexDirection: 'row', alignItems: 'center', gap: 6 }, metaText: { color: colors.muted, fontSize: 9, fontWeight: '600' },
  pairBanner: { marginTop: 13, minHeight: 76, padding: 13, borderRadius: 16, borderWidth: 1, borderColor: 'rgba(185,144,85,.2)', backgroundColor: 'rgba(185,144,85,.06)', flexDirection: 'row', alignItems: 'center', gap: 12 }, pairBannerIcon: { width: 42, height: 42, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(185,144,85,.10)' }, pairBannerTitle: { color: colors.text, fontSize: 13, fontWeight: '700' }, pairBannerCopy: { color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: 3 },
  quickGrid: { flexDirection: 'row', gap: 11, marginTop: 13 }, quickPrimary: { flex: 1.45, minHeight: 108, borderRadius: 17, backgroundColor: colors.gold, padding: 15, justifyContent: 'space-between' }, quickPrimaryTitle: { color: colors.canvas, fontSize: 14, fontWeight: '700' }, quickCard: { flex: 1, borderRadius: 17, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, padding: 15, justifyContent: 'space-between' }, quickCount: { color: colors.text, fontSize: 23, fontWeight: '700' }, quickLabel: { color: colors.muted, fontSize: 10 },
  metricsRow: { marginTop: 13, borderRadius: 15, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, minHeight: 74, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around' }, metricItem: { flex: 1, alignItems: 'center', gap: 3 }, metricValue: { color: colors.text, fontSize: 18, fontWeight: '700' }, metricLabel: { color: colors.quiet, fontSize: 8, letterSpacing: .4 }, metricDivider: { width: 1, height: 28, backgroundColor: colors.line },
  sectionHeader: { marginTop: 27, marginBottom: 11, flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between' }, sectionLabel: { color: colors.bronze, fontSize: 9, fontWeight: '700', letterSpacing: 1.3 }, sectionTitle: { color: colors.text, fontSize: 17, fontWeight: '700', marginTop: 5 }, refreshButton: { width: 38, height: 38, borderRadius: 11, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, alignItems: 'center', justifyContent: 'center' },
  listCard: { borderRadius: 17, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, overflow: 'hidden' }, eventRow: { minHeight: 89, padding: 13, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: colors.line, gap: 11 }, eventIcon: { width: 38, height: 38, borderRadius: 11, backgroundColor: colors.elevated, alignItems: 'center', justifyContent: 'center' }, eventCopy: { flex: 1 }, eventSource: { color: colors.text, fontSize: 12, fontWeight: '600' }, eventPreview: { color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: 3 }, eventMeta: { color: colors.quiet, fontSize: 8, fontWeight: '600', letterSpacing: .5, marginTop: 5 }, eventScore: { flexDirection: 'row', alignItems: 'center', gap: 2 }, eventScoreText: { color: colors.text, fontSize: 12, fontWeight: '700' },
  emptyCard: { minHeight: 190, borderRadius: 17, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, padding: 25, alignItems: 'center', justifyContent: 'center' }, emptyTitle: { color: colors.text, fontSize: 15, fontWeight: '700', marginTop: 11 }, emptyCopy: { color: colors.muted, fontSize: 11, lineHeight: 17, textAlign: 'center', maxWidth: 270, marginTop: 5 },
  bottomNav: { position: 'absolute', left: 0, right: 0, bottom: 0, height: Platform.OS === 'ios' ? 88 : 72, paddingBottom: Platform.OS === 'ios' ? 18 : 4, borderTopWidth: 1, borderTopColor: colors.line, backgroundColor: '#0A0D0B', flexDirection: 'row' }, navItem: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 4 }, navLabel: { color: colors.quiet, fontSize: 9, fontWeight: '600' }, navLabelActive: { color: colors.gold }, navIndicator: { position: 'absolute', top: 0, width: 25, height: 2, borderRadius: 2, backgroundColor: colors.gold },
  modalShade: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,.72)' }, pairSheet: { backgroundColor: colors.panel, borderTopLeftRadius: 25, borderTopRightRadius: 25, borderWidth: 1, borderColor: colors.line, padding: 20, paddingBottom: Platform.OS === 'ios' ? 34 : 22 }, resultSheet: { backgroundColor: colors.panel, borderTopLeftRadius: 25, borderTopRightRadius: 25, borderWidth: 1, borderColor: colors.line, padding: 20, paddingBottom: Platform.OS === 'ios' ? 34 : 22 }, sheetHandle: { width: 38, height: 4, borderRadius: 4, alignSelf: 'center', backgroundColor: '#3A3E3A', marginBottom: 19 }, sheetHeader: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between' }, sheetTitle: { color: colors.text, fontSize: 24, fontWeight: '700', letterSpacing: -.8, marginTop: 5 }, sheetBody: { color: colors.muted, fontSize: 12, lineHeight: 18, marginTop: 11, marginBottom: 18 }, iconButton: { width: 36, height: 36, borderRadius: 10, borderWidth: 1, borderColor: colors.line, alignItems: 'center', justifyContent: 'center' }, inputLabel: { color: colors.bronze, fontSize: 9, fontWeight: '700', letterSpacing: 1.1, marginTop: 12, marginBottom: 7 }, input: { minHeight: 48, borderRadius: 11, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.elevated, color: colors.text, paddingHorizontal: 13, fontSize: 13 }, codeInput: { fontSize: 22, letterSpacing: 8, fontWeight: '700' }, errorText: { color: colors.danger, fontSize: 11, lineHeight: 16, marginTop: 10 },
  primaryButton: { minHeight: 52, borderRadius: 13, backgroundColor: colors.gold, marginTop: 18, paddingHorizontal: 17, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 }, primaryButtonText: { color: colors.canvas, fontSize: 14, fontWeight: '700', flex: 1, textAlign: 'center' }, secondaryButton: { minHeight: 47, borderRadius: 12, borderWidth: 1, borderColor: colors.line, backgroundColor: 'rgba(255,255,255,.025)', alignItems: 'center', justifyContent: 'center', marginTop: 14, paddingHorizontal: 16 }, secondaryButtonText: { color: colors.text, fontSize: 13, fontWeight: '700' }, privacyLine: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, marginTop: 13 }, privacyText: { color: colors.muted, fontSize: 9 },
  scanTools: { flexDirection: 'row', gap: 10, marginBottom: 13 }, toolButton: { flex: 1, minHeight: 50, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, borderRadius: 13, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 }, toolButtonText: { color: colors.text, fontSize: 11, fontWeight: '600' }, cameraCard: { height: 260, borderRadius: 18, overflow: 'hidden', borderWidth: 1, borderColor: colors.line, marginBottom: 13 }, cameraClose: { position: 'absolute', right: 12, top: 12, width: 36, height: 36, borderRadius: 18, backgroundColor: 'rgba(0,0,0,.7)', alignItems: 'center', justifyContent: 'center' }, qrFrame: { position: 'absolute', width: 170, height: 170, borderRadius: 16, borderWidth: 2, borderColor: colors.gold, alignSelf: 'center', top: 44 }, inputCard: { borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, borderRadius: 17, padding: 15 }, inputCardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }, inputHint: { color: colors.quiet, fontSize: 9, marginTop: 5 }, scanInput: { minHeight: 180, color: colors.text, fontSize: 14, lineHeight: 21, marginTop: 14, padding: 13, borderRadius: 12, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.elevated }, signalChips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 11 }, signalChip: { color: colors.bronze, fontSize: 8, fontWeight: '700', paddingHorizontal: 8, paddingVertical: 5, borderRadius: 20, backgroundColor: 'rgba(185,144,85,.08)' }, explainer: { marginTop: 15, padding: 13, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(114,201,139,.14)', backgroundColor: 'rgba(114,201,139,.04)', flexDirection: 'row', gap: 10 }, explainerTitle: { color: colors.text, fontSize: 11, fontWeight: '700' }, explainerCopy: { color: colors.muted, fontSize: 9, lineHeight: 14, marginTop: 3 },
  resultTop: { flexDirection: 'row', alignItems: 'center', gap: 16 }, resultScoreRing: { width: 95, height: 95, borderRadius: 48, borderWidth: 6, alignItems: 'center', justifyContent: 'center', flexDirection: 'row' }, resultScore: { fontSize: 37, fontWeight: '800', letterSpacing: -2 }, resultOutOf: { color: colors.quiet, fontSize: 9, marginTop: 19 }, resultHeading: { flex: 1 }, resultBadge: { flexDirection: 'row', alignItems: 'center', gap: 6 }, resultTitle: { color: colors.text, fontSize: 20, lineHeight: 25, fontWeight: '700', letterSpacing: -.6, marginTop: 8 }, actionCard: { borderWidth: 1, borderRadius: 13, padding: 13, marginTop: 18, backgroundColor: colors.elevated }, actionLabel: { color: colors.bronze, fontSize: 8, fontWeight: '700', letterSpacing: 1 }, actionText: { color: colors.text, fontSize: 12, lineHeight: 18, marginTop: 5 }, reasonRow: { minHeight: 45, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: colors.line }, reasonIndex: { color: colors.bronze, fontSize: 9, fontWeight: '700', width: 30 }, reasonText: { color: colors.muted, fontSize: 11, flex: 1 },
  titleRow: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between' }, settingsCard: { borderWidth: 1, borderColor: colors.line, backgroundColor: colors.panel, borderRadius: 16, marginTop: 9, marginBottom: 23, overflow: 'hidden' }, settingRow: { minHeight: 72, paddingHorizontal: 14, flexDirection: 'row', alignItems: 'center', gap: 11, borderBottomWidth: 1, borderBottomColor: colors.line }, settingIcon: { width: 38, height: 38, borderRadius: 11, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.elevated }, settingCopy: { flex: 1 }, settingTitle: { color: colors.text, fontSize: 12, fontWeight: '600' }, settingSubtitle: { color: colors.muted, fontSize: 9, lineHeight: 14, marginTop: 3 }, disabledPill: { paddingHorizontal: 8, paddingVertical: 6, borderRadius: 20, backgroundColor: colors.elevated }, disabledPillText: { color: colors.quiet, fontSize: 7, fontWeight: '700', letterSpacing: .6 }, deviceCard: { padding: 14, flexDirection: 'row', alignItems: 'center', gap: 11 }, deviceAvatar: { width: 44, height: 44, borderRadius: 13, backgroundColor: 'rgba(185,144,85,.08)', alignItems: 'center', justifyContent: 'center' }, deviceTitle: { color: colors.text, fontSize: 12, fontWeight: '700' }, deviceAddress: { color: colors.muted, fontSize: 9, marginTop: 4 }, unpairButton: { minHeight: 46, borderTopWidth: 1, borderTopColor: colors.line, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 }, unpairText: { color: colors.danger, fontSize: 10, fontWeight: '600' }, pairRow: { minHeight: 76, paddingHorizontal: 14, flexDirection: 'row', alignItems: 'center', gap: 11 }, versionRow: { alignItems: 'center', gap: 10, marginVertical: 18 }, versionText: { color: colors.quiet, fontSize: 9 },
})
