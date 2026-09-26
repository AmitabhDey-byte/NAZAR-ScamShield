# NAZAR n8n setup: Twilio SMS, WhatsApp, and Gmail

These two importable workflows target the deployed Render API at
`https://nazar-scamshield.onrender.com`:

- `nazar-twilio-intake.json`: Twilio inbound webhook → NAZAR analysis →
  existing or new Gemini honeypot → Gmail approval → Twilio reply.
- `nazar-gmail-intake.json`: Gmail Trigger → NAZAR analysis → mark the email read
  only after NAZAR accepts it. There is no automatic reply to email.

The files were prepared from the two supplied n8n exports. They have no
credential IDs, API keys, or n8n instance IDs. **Import them as new workflows**
and keep the originals disabled while testing, or each incoming event may run
twice. The Twilio export had several disconnected branches; the version here
fixes those paths. It also removes the `whatsapp:` prefix before the n8n Twilio
node adds that prefix itself.

## 1. Render

In the Render backend service, set `N8N_WEBHOOK_SECRET` to a long random value.
Keep `GEMINI_API_KEY` configured if you want Gemini analysis and honeypot
replies. Deploy the latest backend code before testing. Check `/api/health` and
confirm `integrations.n8n_gmail` and `integrations.n8n_twilio` say `configured`.

To arm the visible honeypot tripwire, create a fresh **Web Bug** token and set
`CANARYTOKEN_URL` in Render. Never paste the token into GitHub, n8n, Vercel, or
frontend environment variables: anyone who requests it can create a false
alert. NAZAR validates the hostname but never opens the URL itself.

## 2. n8n credentials

Create one **Header Auth** credential for NAZAR. Set **Name** to
`X-NAZAR-Webhook-Secret` and **Value** to the exact `N8N_WEBHOOK_SECRET` from
Render. Attach this credential to these HTTP Request nodes:

- Gmail: `Send to NAZAR`
- Twilio: `Send to NAZAR`, `Start Honeypot Session`, and
  `Send Message to Honeypot Session`

The workflow JSON uses **Generic Credential Type → Header Auth**. Do not enter
the secret in the workflow's ordinary Header Parameters field.

Attach your **Gmail OAuth2** credential to `Gmail Trigger - New Unread`,
`Mark Email as Read`, and `Human Approval: Honeypot Reply`. Attach a **Twilio**
credential (Account SID and Auth Token) to `Send Approved Honeypot Reply`.
Set the actual approver address in that Gmail approval node, replacing
`REPLACE_WITH_APPROVER_EMAIL`.

The included Twilio workflow sends `enable_canary: true` when it creates a new
honeypot session. If you already published an older workflow, open **Start
Honeypot Session** and set its JSON body to:

```javascript
{{ JSON.stringify({ analysis_id: $("Send to NAZAR").item.json.analysis.id, enable_canary: true }) }}
```

Keep the Gmail human-approval node enabled. The Canary link appears in the
proposed reply but is not sent until you approve it.

## 3. Twilio session table

In n8n, create a Data Table named `nazar_honeypot_sessions` with these **Text**
columns: `sender`, `session_id`, `channel`, `last_analysis_id`, and
`last_message_sid`. In both `Lookup Honeypot Session` and
`Save Sender-Session Mapping`, select this table from the dropdown. The
placeholder `RESELECT_TABLE_IN_N8N` is intentional. The lookup node already has
**Always Output Data** enabled, which lets a new sender reach the new-session
branch.

The workflow checks for an existing session before checking the current
message's risk. That lets later, innocuous sounding scammer replies continue
the same honeypot conversation. A new sender starts a honeypot only if NAZAR
classifies the first message as `SUSPICIOUS` or `DANGEROUS`.

## 4. Point Twilio to n8n

Open the imported `NAZAR - Twilio SMS and WhatsApp Intake` workflow and
**publish/activate** it. In `Twilio Incoming Message`, copy the **Production
URL** (not the Test URL). The path is `nazar-twilio-incoming`.

In Twilio Console, open **Phone Numbers → Active Numbers → your SMS number →
Messaging → A message comes in**. Select **Webhook**, paste the n8n Production
URL, set **HTTP POST**, and save. For the WhatsApp Sandbox, set the same URL in
**Sandbox settings → When a message comes in**, with **POST**. Twilio will send
form fields such as `From`, `To`, `Body`, and `MessageSid` to n8n.

The `Respond Empty TwiML Immediately` node sends a valid empty XML response to
Twilio before NAZAR analysis runs. An outgoing message is sent only if an
approver clicks **Approve** in the Gmail approval email.

## 5. Start Gmail intake

Open the imported `NAZAR - Gmail Intake` workflow. Confirm the Gmail OAuth2
credential, Header Auth credential, and Render URL are selected, then
**publish/activate** it. It polls once a minute for new unread messages,
including Spam but excluding Trash. It fetches parsed text and HTML rather than
metadata alone. The workflow removes the `UNREAD` label after a successful
NAZAR response; it leaves messages unread when NAZAR returns an error.
Its Gmail search excludes NAZAR approval emails if the approver uses the same
inbox.

## 6. End-to-end test

1. Send an SMS or WhatsApp Sandbox message to your Twilio number. Inspect the
   n8n execution. `Send to NAZAR` should return `status: accepted` and an
   `analysis` object. Check the NAZAR dashboard and paired Expo app feed.
2. Use a message with a clear scam signal to test the honeypot. Inspect
   `Send Message to Honeypot Session` for a `messages` array and Gemini reply.
   Approve it in the email and confirm the Twilio node succeeds.
3. Send one new email to the connected Gmail inbox. Inspect the Gmail n8n
   execution, then confirm a `gmail` analysis appears in NAZAR. The email
   should be marked read only after `Send to NAZAR` succeeds.

If the n8n HTTP Request returns `401`, the Header Auth secret differs from
Render. If it returns `503`, set `N8N_WEBHOOK_SECRET` in Render and redeploy. If
the Twilio workflow stops at its table nodes, select your new Data Table in both
nodes. If Twilio produces no n8n execution, check that the workflow is active
and Twilio uses the Production URL.

The Twilio webhook is publicly reachable and this starter workflow does not
validate Twilio's request signature. Use a dedicated demo number and keep
human approval enabled for outbound replies. Production use should validate
`X-Twilio-Signature` before processing inbound events.
