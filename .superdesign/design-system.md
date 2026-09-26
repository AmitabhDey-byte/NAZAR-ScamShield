# NAZAR Design System

## Product and audience

NAZAR is a hackathon-ready digital scam-defense operations product for Indian payment users, fraud analysts, and demo judges. It turns an SMS, WhatsApp-style message, URL, QR/payment request, or transaction context into an explainable risk decision and then lets the user report it, simulate a defensive honeypot conversation, and explore related scam campaigns.

The primary job is immediate analysis. The first viewport should show the analyzer and enough live context to make the system feel operational. Avoid a marketing hero, pricing patterns, or generic AI copy.

Core flow: Dashboard → Analyze → Risk result → Trap scammer → Intelligence graph → Campaign. Secondary routes: community report, call transcript analysis, and model metrics.

## Visual thesis

"Live signal operations desk": deep navy surfaces, precise blue/cyan signal lines, sharp data typography, and a restrained telemetry-grid atmosphere. The UI should feel vigilant, credible, and Indian-payment aware—not military cosplay and not a generic neon cyber dashboard.

Use a dense operational product language: navy layers, restrained glass, dot grid, and cyan connection lines. Do not use gold, serif display typography, floating marketing cards, or oversized headlines.

## Color tokens

- Canvas: `#06111f`
- Elevated canvas: `#081827`
- Panel: `rgba(11, 23, 40, 0.88)`
- Panel strong: `#11233a`
- Hairline: `rgba(148, 163, 184, 0.16)`
- Hairline active: `rgba(34, 211, 238, 0.42)`
- Primary text: `#f8fafc`
- Muted text: `#93a4ba`
- Quiet text: `#64748b`
- Primary blue: `#3b82f6`
- Signal cyan: `#22d3ee`
- Signal wash: `rgba(34, 211, 238, 0.10)`
- Safe: `#25c281`
- Suspicious: `#f5a524`
- Dangerous: `#ff5d73`
- Info: `#22d3ee`

Never introduce purple, cyan gradients, or saturated electric-blue surfaces. Status colors are semantic and used sparingly.

## Typography

- UI and body: `Inter`, fallback `ui-sans-serif, system-ui, sans-serif`.
- Data, scores, IDs, labels: `IBM Plex Mono`, fallback `ui-monospace, SFMono-Regular, monospace`.
- Brand wordmark: Inter 800 with slightly tight tracking; the central `A` may receive the bronze accent.
- Page titles: 28–36px, weight 650–750, tight tracking.
- Body: 14–16px, line height 1.5–1.65.
- Small labels: 11–12px uppercase, mono, 0.12em tracking. Never use tiny text for required actions.

## Layout

- Persistent left rail on desktop, compact bottom navigation on mobile.
- 24px outer desktop gutters, 16px on tablet/mobile.
- Dashboard uses a 12-column grid. The analyzer occupies 7–8 columns; live campaign/risk context occupies 4–5.
- Keep key inputs and the Analyze button above the fold at 1440×900.
- Cards use 14–18px radius, not oversized pill-shaped panels.
- Align panel edges and baselines deliberately. Prefer dense, useful information to decorative whitespace.

## Components

- Sidebar: 248px, nearly opaque canvas, subtle right border, compact nav rows with Lucide icons. Active item uses bronze text and a left rail glow.
- Analyzer: segmented input modes for Message, URL, Transaction, Call. Large dark textarea with example placeholder and entity chips. The primary Analyze action is warm bronze with black text.
- Risk score: circular or arc gauge with large mono score and explicit SAFE/SUSPICIOUS/DANGEROUS label. Never rely on color alone.
- Evidence list: stacked concise reasons with small icons and per-signal scores.
- Data cards: hairline borders, faint inset highlight, subtle bronze glow only on active/high-priority cards.
- Tables: compact rows, strong column labels, risk/status chips, useful hover state.
- Graph: dark bounded canvas, thin bronze/gray edges, semantic node colors, readable labels, zoom controls.
- Chat: scammer messages on neutral dark surface; NAZAR persona messages use bronze wash. Intelligence panel updates beside chat.
- Buttons: 42–46px minimum height for primary actions. 10–12px radius. Clear focus ring in bronze light.
- Toasts and empty/loading/error states should be concise and action-oriented.

## Motion

- Use `cubic-bezier(0.4, 0, 0.2, 1)`.
- 140–220ms for hover, focus, and panel transitions.
- One subtle radar sweep or pulsing connection animation is allowed on the dashboard/graph, with reduced-motion support.
- No constant floating animation, parallax, or distracting glow pulses.

## Content rules

- Use realistic Indian payment data: UPI IDs, rupee amounts, SBI/KYC, electricity-disconnection and delivery examples.
- Write for users making a safety decision. Prefer `Do not pay. Verify through the official electricity board number.` over vague reassurance.
- Always explain why a score was assigned.
- Use `Synthetic honeypot simulation` labels so nobody mistakes the demo for live impersonation or hack-back functionality.

## Responsive behavior

- At under 1024px, collapse the sidebar to an icon rail and stack secondary dashboard panels.
- At under 720px, use bottom navigation, one-column cards, full-width actions, and move result evidence below the score summary.
- Tables become cards or scroll inside a clearly bounded region; the page itself must not horizontally overflow.

## Accessibility

- AA contrast for body text and controls.
- Visible `:focus-visible` states.
- Labels for all fields; semantic headings and buttons.
- Status always includes text/icon, not color alone.
- Respect `prefers-reduced-motion`.

## Required screen direction

The dashboard opens directly on the scam analyzer. Above it, show four compact metrics: threats analyzed, dangerous scams, active campaigns, and indicators collected. To the right, show an active-campaign pulse panel with a mini line chart and one high-confidence campaign summary. Below, show recent analyses and a small category distribution. The visual signature is a faint dotted field with one precise bronze sweep line connecting risk evidence to the campaign panel.

Use ONLY the fonts, colors, spacing, and component styles defined in this design system. Do not introduce any fonts, colors, or visual styles not in the design system.

## Mobile companion direction

NAZAR Mobile is the sensor and immediate decision surface; the desktop remains the investigation and response console. The phone home screen should open on protection status, one primary scan action, the last detected incident, and a short stream of recent signals. It must feel calm enough for everyday users while retaining the graphite/bronze NAZAR identity.

- Use a 390×844 reference viewport with safe-area insets and a four-item bottom navigation.
- Mobile canvas is `#080a09`; cards use `#121513`; the strongest brand action uses `#dfbd7a` with dark text.
- The protection card is the memorable visual: a centered radar/shield ring with status, paired-device state, and explicit privacy copy.
- Do not imply Expo Go can monitor other apps in the background. Label the Expo Go mode as `Companion mode` and list its supported sources: camera QR, clipboard scan, pasted text/URL, and server-synced alerts.
- Keep scan results thumb-friendly: score, text decision, reasons, and a single recommended action above deeper evidence.
- Pairing is a short flow requiring desktop URL, six-digit code, and device name. Explain that the phone and computer must reach the same backend.
- The Activity screen lists synced incidents from this device. Dangerous events use coral only for status and the immediate stop action.
- Settings expose data collection controls, retention messaging, paired desktop identity, and a clearly disabled `Passive Android monitoring` row labeled `Requires development build`.
