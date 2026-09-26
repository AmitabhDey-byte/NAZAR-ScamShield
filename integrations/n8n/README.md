# Gmail → NAZAR with n8n

This integration makes Gmail a real-time NAZAR source:

`Gmail Trigger → HTTP Request → NAZAR /api/integrations/n8n/gmail → Gemini + ML + SSE dashboard`

1. Set `N8N_WEBHOOK_SECRET` in `D:\NAZAR\.env`, restart the backend, and keep it private.
2. In n8n, add a **Gmail Trigger** node for new messages. Use the message ID, sender, subject, snippet, and plain-text body fields.
3. Add an **HTTP Request** node:
   - Method: `POST`
   - URL: `http://YOUR_COMPUTER_LAN_IP:8000/api/integrations/n8n/gmail`
   - Header: `X-NAZAR-Webhook-Secret: YOUR_N8N_WEBHOOK_SECRET`
   - Body: JSON, mapping `from`, `subject`, `text`, `snippet`, `id`, and `threadId` from the Gmail node.
4. Test with one mailbox message. The desktop dashboard should update without a refresh.

If n8n runs in Docker, `localhost` inside n8n points to the container. Use `http://host.docker.internal:8000/...` on Windows or the computer's LAN IP. For n8n Cloud, the backend must be reachable through an HTTPS tunnel or deployed server; never expose the webhook without the secret.

NAZAR stores the email as a `gmail` analysis and sends only the extracted evidence through the existing rules, ML, and optional Gemini pipeline. It does not automatically reply to email.

## Twilio SMS / WhatsApp

Use a second n8n workflow for messaging:

`Twilio inbound webhook → n8n Webhook → NAZAR /api/integrations/n8n/twilio → live dashboard`

Configure Twilio's incoming-message webhook to your n8n Webhook URL. In n8n, forward this JSON to NAZAR with the same `X-NAZAR-Webhook-Secret` header:

```json
{
  "from": "whatsapp:+919000012345",
  "to": "whatsapp:+1415XXXXXXX",
  "body": "Your bank account will be blocked. Pay immediately.",
  "MessageSid": "SMxxxxxxxx",
  "channel": "whatsapp",
  "ProfileName": "Unknown sender"
}
```

NAZAR analyzes the message, stores it as `twilio_sms` or `twilio_whatsapp`, and streams the result to the dashboard and paired Expo app. For a reply, route the approved synthetic-victim text through an n8n **Twilio → Send SMS/WhatsApp** node. Keep outbound sending behind an analyst approval step; NAZAR does not silently send messages to real people.

Twilio and WhatsApp require an approved sender/number, account credentials, and a publicly reachable HTTPS n8n webhook. For local testing, use an n8n tunnel or deploy n8n; do not expose port 8000 directly to the internet.
