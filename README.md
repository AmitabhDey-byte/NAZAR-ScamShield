# NAZAR

NAZAR is a full-stack, explainable digital scam-defense platform built for the CodeVoyage FT-01 ScamShield challenge. It analyzes suspicious messages, URLs, and payment context, explains the risk decision, supports community reporting, runs a strictly defensive synthetic honeypot simulation, and connects reused infrastructure into scam campaigns.

**Live demo:** https://nazar-scam-shield.vercel.app

**API health:** https://nazar-scamshield.onrender.com/api/health

The product follows four layers:

- **SENSE** — extracts amounts, UPI IDs, URLs, phone numbers, claimed organizations, and social-engineering tactics.
- **THINK** — combines message, URL, transaction, community, cross-channel consistency, and measurable ML signals.
- **DECEIVE** — runs an in-app synthetic victim conversation to elicit voluntarily shared indicators. It never contacts real scammers or performs hack-back activity.
- **SHARE** — correlates community reports into a PostgreSQL threat graph and campaign fingerprints (“Scam DNA”).

## Architecture

```mermaid
flowchart LR
  U[React desktop console] -->|REST| A[FastAPI]
  X[Expo Go mobile companion] -->|Pair + sync| A
  A --> S[Deterministic risk engine]
  A --> M[TF-IDF + Logistic Regression]
  A -. optional .-> G[Gemini analysis + safe honeypot replies]
  A --> P[(Neon PostgreSQL)]
  P --> T[Threat graph + campaigns]
  S --> H[Controlled honeypot state machine]
```

The app defaults to a local SQLite database when `DATABASE_URL` is empty, so the complete demo works before credentials are added. Set `DATABASE_URL` to a Neon pooled connection string for runtime traffic, and `DATABASE_URL_UNPOOLED` to a direct connection string for Alembic migrations.

## Tech stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router, Recharts, Lucide
- Mobile: Expo SDK 57, React Native, Expo Camera, Expo Clipboard, AsyncStorage
- Backend: FastAPI, Pydantic, async SQLAlchemy
- Database: Neon PostgreSQL in production; SQLite fallback for zero-setup demo
- ML: word + character TF-IDF and Logistic Regression, evaluated on a separate stratified held-out test set
- AI: Gemini on the backend for structured risk enrichment and controlled honeypot replies; deterministic fallbacks remain available

## Project structure

```text
NAZAR/
├── frontend/             React application and all product routes
├── mobile/               Expo Go companion for phone-side scans and sync
├── backend/
│   ├── app/
│   │   ├── routers/      REST endpoints
│   │   ├── services/     Risk, ML, Gemini and honeypot logic
│   │   ├── models.py     SQLAlchemy threat-intelligence schema
│   │   └── main.py       FastAPI application
│   ├── alembic/          Database migration support
│   └── tests/            Risk-engine tests
├── ml/                   UCI SMS Spam Collection, India-context supplement, and provenance
└── .env.example
```

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/docs` for the interactive API.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### 3. Mobile companion with Expo Go

Install Expo Go on the phone, keep the phone and computer on the same Wi-Fi, then run:

```bash
cd mobile
npm install
npx expo start --lan
```

Scan the terminal QR code with Expo Go. In the desktop console, open **Mobile devices**, generate a pairing code, then enter the shown Wi-Fi API address and code in the app. Windows Firewall may ask you to allow Python and Node on private networks.

The Expo Go companion supports camera/QR scanning, pasted or clipboard text analysis, foreground sync, and the shared incident timeline. Expo Go cannot include a custom Android notification-listener service, so passive WhatsApp/SMS notification monitoring is deliberately shown as unavailable. That capability requires a separate Expo development build and explicit Android notification-access consent.

## Environment variables

Copy `.env.example` to `.env` in the repository root.

```dotenv
DATABASE_URL=postgresql://user:password@your-endpoint-pooler.region.aws.neon.tech/neondb?sslmode=require
DATABASE_URL_UNPOOLED=postgresql://user:password@your-endpoint.region.aws.neon.tech/neondb?sslmode=require
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_TIMEOUT_SECONDS=12
URL_INTELLIGENCE_ENABLED=true
URL_INTELLIGENCE_TIMEOUT_SECONDS=4
GOOGLE_SAFE_BROWSING_API_KEY=
URLHAUS_AUTH_KEY=
N8N_WEBHOOK_SECRET=replace-with-a-long-random-secret
CANARYTOKEN_URL=
PUBLIC_API_URL=https://nazar-scamshield.onrender.com
VITE_API_BASE_URL=http://localhost:8000
EXPO_PUBLIC_API_BASE_URL=https://nazar-scamshield.onrender.com
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ALLOWED_ORIGIN_REGEX=^https://[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.vercel\.app$
```

Never prefix the Gemini key with `VITE_`; that would expose it to browser code.
Keep `CANARYTOKEN_URL` server-side in Render as well. The honeypot adds it only
to an explicitly armed, human-approved reply and never requests the URL itself.
Use a fresh token for each controlled demo so unrelated requests cannot create
misleading alerts.

URL analysis uses IANA's RDAP bootstrap data and the authoritative registry's
RDAP service for domain age. For external blacklist checks, configure a Google
Safe Browsing API key and/or a URLhaus Auth-Key in Render. Lookups are made only
to those fixed services; NAZAR never visits the submitted website itself. A
timeout or unavailable provider is reported as unavailable and does not make a
URL look safe.

## Production deployment

The backend is configured for `https://nazar-scamshield.onrender.com`. On the
Render service, set `PUBLIC_API_URL` to that exact URL so phone pairing never
receives Render's private container address.

For Vercel, import the repository, set **Root Directory** to `frontend`, and
set `VITE_API_BASE_URL=https://nazar-scamshield.onrender.com`. The committed
`frontend/vercel.json` keeps React Router pages working when opened or
refreshed directly. After Vercel gives you the final site URL, add that exact
origin to Render's `ALLOWED_ORIGINS` and redeploy the backend, for example:

```dotenv
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://your-nazar-site.vercel.app
```

The default `ALLOWED_ORIGIN_REGEX` also accepts HTTPS Vercel deployment and
preview subdomains. Keep the exact production origin in `ALLOWED_ORIGINS` when
you know it; do not include a path or trailing slash.

For Expo Go, `mobile/.env.example` points to the Render API. Copy it to
`mobile/.env.local` only when you want to override the production default,
then fully reload the app in Expo Go.

## Neon setup

1. Create a Neon project and copy both connection strings.
2. Use the pooled URL (hostname contains `-pooler`) for `DATABASE_URL`.
3. Use the direct URL for `DATABASE_URL_UNPOOLED`; migrations require session semantics that transaction pooling does not provide.
4. From `backend/`, run:

```bash
alembic upgrade head
```

The API also calls `create_all()` at startup for hackathon convenience. Keep Alembic as the source of schema change history for team/production workflows.

## Demo flow

1. Open the command center. The analyzer is the first working surface.
2. Paste or type a suspicious message; NAZAR ships with no fake runtime incidents.
3. Review the separate risk components and extracted indicators.
4. Launch **Trap scammer**, relay the scammer's next message, and review Gemini's bounded synthetic-victim reply.
5. Open the intelligence graph after real reports have created a campaign cluster.
6. Submit a community report and inspect the model evaluation page.
7. Open **Mobile devices**, pair the Expo Go app, and submit a phone-side scan to see it sync into the shared backend.

## Risk engine

The configurable baseline weighting is:

```text
final = 0.25 message + 0.20 URL + 0.20 transaction
      + 0.15 community + 0.20 consistency
```

Critical multi-channel combinations have a conservative override so an urgent threat plus a known indicator or strong identity mismatch is not diluted into a low final score. The response always includes component scores, reasons, entities, classification, and a recommended action.

## ML training and evaluation

The classifier loads 5,574 real labeled messages from the UCI SMS Spam Collection plus a small reviewed India-context supplement. It combines word and character TF-IDF features and reports accuracy, precision, recall, and F1 on a reproducible stratified 20% held-out test split. The runtime classifier is then fitted on the complete reviewed dataset. Community submissions are not automatically promoted into training data, preventing unreviewed personal data and poisoning attacks. Regenerate the public dataset with `python ml/import_uci_sms.py`.

```bash
cd backend
pytest -q
```

`GET /api/model/metrics` returns accuracy, precision, recall, F1, sample count, source counts, and evaluation method. See `ml/ATTRIBUTION.md` for provenance and license details.

## REST API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/analyze/message` | Message-only signal and ML analysis |
| POST | `/api/analyze/url` | Structural URL, RDAP domain-age, and configured reputation checks |
| POST | `/api/analyze/transaction` | Transaction anomaly score |
| POST | `/api/analyze/full` | Combined explainable decision |
| GET | `/api/analyze/{id}` | Saved analysis |
| POST | `/api/reports` | Community report |
| POST | `/api/honeypot/start` | Start controlled simulation |
| POST | `/api/honeypot/{id}/message` | Add simulated scammer turn |
| GET | `/api/honeypot/{id}` | Session and collected intelligence |
| GET | `/api/campaigns` | Campaign list |
| GET | `/api/campaigns/{id}` | Campaign and Scam DNA |
| GET | `/api/intelligence/graph` | Threat graph nodes and edges |
| GET | `/api/model/metrics` | Reproducible ML evaluation |
| POST | `/api/calls/analyze` | Manual call transcript analysis |
| POST | `/api/devices/pair-code` | Create an expiring phone pairing code |
| POST | `/api/devices/register` | Exchange a code for a scoped device token |
| GET | `/api/devices` | List paired phone companions |
| POST | `/api/devices/{id}/events` | Analyze and sync a phone-submitted signal |
| GET | `/api/devices/{id}/events` | Read that device's synchronized timeline |
| GET | `/api/devices/{id}/feed` | Read that phone's scans plus Gmail/Twilio live signals |
| GET | `/api/realtime/events` | Server-sent live analysis, report, device, and honeypot events |
| GET | `/api/integrations/status` | Last real Gmail, WhatsApp, and SMS deliveries without message contents |
| POST | `/api/integrations/n8n/gmail` | Ingest a Gmail Trigger event from n8n and analyze it live |
| POST | `/api/integrations/n8n/twilio` | Ingest an SMS or WhatsApp event from n8n and analyze it live |

## Privacy and security

- Gemini is optional and only called by the backend. Untrusted message content is explicitly treated as data, not instructions.
- When reputation providers are configured, submitted URLs are sent from the backend to Google Safe Browsing and/or URLhaus for a match lookup. Domain-age checks send only the domain to the authoritative RDAP service.
- The honeypot is a controlled manual relay. Gemini writes a synthetic victim reply, but NAZAR does not automatically message real people, pay, click links, compromise devices, request credentials, or access external systems.
- UI copy warns users not to submit passwords, OTPs, or private victim data.
- Mobile authentication-code/OTP content is rejected by the API and is not stored.
- Expo Go mode is user-initiated: it does not silently read notifications, messages, or other apps.
- Gmail can be connected through n8n using the secured webhook documented in `integrations/n8n/README.md`.
- Secrets are loaded from environment variables and `.env` is ignored by Git.
- API inputs are length-bounded and validated by Pydantic.
- Production deployments should add authentication, role-based access, abuse controls, audit logs, retention limits, encryption policies, and formal model monitoring.

## Limitations and future scope

- Community similarity uses deterministic indicator matching; production can add pgvector embeddings and human-reviewed thresholds.
- Domain checks are structural and offline; production can add safe reputation feeds and DNS/WHOIS age checks.
- User identity is intentionally omitted. Add authentication before storing real user reports in a public deployment.
- Future versions can add an opt-in Android development build for passive notification screening, regional-language models, verified institutional takedown feeds, and privacy-preserving federated campaign sharing.
