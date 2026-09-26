"""Repair NAZAR's exported n8n workflows without copying credentials or instance IDs.

Usage:
    python prepare_workflows.py path/to/twilio.json path/to/gmail.json
"""

import json
import sys
from pathlib import Path


API = "https://nazar-scamshield.onrender.com"


def connection(*names):
    return [{"node": name, "type": "main", "index": 0} for name in names]


def output(*branches):
    return {"main": [connection(*branch) for branch in branches]}


def clean(workflow):
    return {
        "name": workflow["name"],
        "nodes": workflow["nodes"],
        "connections": workflow["connections"],
        "settings": {"executionOrder": "v1"},
        "active": False,
    }


def set_header_auth(node):
    params = node["parameters"]
    params["authentication"] = "genericCredentialType"
    params["genericAuthType"] = "httpHeaderAuth"
    params.pop("headerParameters", None)
    params.pop("sendHeaders", None)
    # Select a Header Auth credential in n8n after import. The exported file
    # deliberately contains no credential ID or secret.
    node.pop("credentials", None)


def repair_twilio(workflow):
    workflow = clean(workflow)
    workflow["name"] = "NAZAR - Twilio SMS and WhatsApp Intake"
    obsolete = {"Extract Proposed Reply (New Session)"}
    workflow["nodes"] = [n for n in workflow["nodes"] if n["name"] not in obsolete]
    nodes = {node["name"]: node for node in workflow["nodes"]}

    for name, path in (
        ("Send to NAZAR", "/api/integrations/n8n/twilio"),
        ("Start Honeypot Session", "/api/honeypot/start"),
        ("Send Message to Honeypot Session", "/api/honeypot/"),
    ):
        node = nodes[name]
        set_header_auth(node)
        node["parameters"]["url"] = API + path
    nodes["Send Message to Honeypot Session"]["parameters"]["url"] = (
        "={{ '" + API + "/api/honeypot/' + $json.session_id + '/message' }}"
    )
    nodes["Start Honeypot Session"]["parameters"]["jsonBody"] = (
        '={{ JSON.stringify({ analysis_id: $("Send to NAZAR").item.json.analysis.id, enable_canary: true }) }}'
    )
    for name in ("Lookup Honeypot Session", "Save Sender-Session Mapping"):
        nodes[name]["parameters"]["dataTableId"]["value"] = "RESELECT_TABLE_IN_N8N"
    nodes["Lookup Honeypot Session"]["alwaysOutputData"] = True
    nodes["Dangerous?"]["parameters"]["conditions"]["conditions"] = [{
        "id": "risk-at-least-30",
        "leftValue": "={{ String(Number($('Send to NAZAR').item.json.analysis.score) >= 30) }}",
        "rightValue": "true",
        "operator": {"type": "string", "operation": "equals"},
    }]

    reply = nodes["Extract Proposed Reply (Existing Session)"]
    reply["name"] = "Extract Proposed Reply"
    reply["notes"] = "Extracts the latest generated assistant reply after the incoming message was processed."
    approval = nodes["Human Approval: Honeypot Reply"]["parameters"]
    approval["sendTo"] = "REPLACE_WITH_APPROVER_EMAIL"
    approval["approvalOptions"] = {"values": {"approvalType": "double"}}
    sender = nodes["Send Approved Honeypot Reply"]
    sender["parameters"].update({
        "resource": "sms",
        "operation": "send",
        "from": "={{ $('Normalize Twilio').item.json.to.replace(/^whatsapp:/, '') }}",
        "to": "={{ $('Normalize Twilio').item.json.from.replace(/^whatsapp:/, '') }}",
        "message": "={{ $('Extract Proposed Reply').item.json.proposed_reply }}",
    })

    workflow["connections"] = {
        "Twilio Incoming Message": output(["Respond Empty TwiML Immediately"]),
        "Respond Empty TwiML Immediately": output(["Normalize Twilio"]),
        "Normalize Twilio": output(["Send to NAZAR"]),
        "Send to NAZAR": output(["Lookup Honeypot Session"], ["Log Analysis Error (no secrets)"]),
        "Lookup Honeypot Session": output(["Existing Session?"]),
        "Existing Session?": output(["Send Message to Honeypot Session"], ["Dangerous?"]),
        "Dangerous?": output(["Start Honeypot Session"], []),
        "Start Honeypot Session": output(["Save Sender-Session Mapping"], ["Log Honeypot Error (no secrets)"]),
        "Save Sender-Session Mapping": output(["Send Message to Honeypot Session"]),
        "Send Message to Honeypot Session": output(["Extract Proposed Reply"], ["Log Honeypot Error (no secrets)"]),
        "Extract Proposed Reply": output(["Human Approval: Honeypot Reply"]),
        "Human Approval: Honeypot Reply": output(["Approved?"]),
        "Approved?": output(["Send Approved Honeypot Reply"], []),
        "Send Approved Honeypot Reply": output([], ["Log Send Error (no secrets)"]),
    }
    return workflow


def repair_gmail(workflow):
    workflow = clean(workflow)
    workflow["name"] = "NAZAR - Gmail Intake"
    workflow["nodes"] = [node for node in workflow["nodes"] if not node.get("disabled")]
    workflow["connections"]["Mark Email as Read"] = output([])
    nodes = {node["name"]: node for node in workflow["nodes"]}
    set_header_auth(nodes["Send to NAZAR"])
    nodes["Send to NAZAR"]["parameters"]["url"] = API + "/api/integrations/n8n/gmail"
    nodes["Gmail Trigger - New Unread"]["parameters"].setdefault("maxResults", 10)
    # Gmail's simplify=false output includes parsed text/html, needed by NAZAR.
    trigger = nodes["Gmail Trigger - New Unread"]["parameters"]
    trigger["simple"] = False
    trigger.setdefault("filters", {})["includeSpamTrash"] = True
    trigger["filters"]["q"] = '-in:trash -subject:"NAZAR: approve honeypot reply"'
    return workflow


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python prepare_workflows.py TWILIO_EXPORT GMAIL_EXPORT")
    twilio = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    gmail = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8-sig"))
    folder = Path(__file__).resolve().parent
    for name, workflow in (
        ("nazar-twilio-intake.json", repair_twilio(twilio)),
        ("nazar-gmail-intake.json", repair_gmail(gmail)),
    ):
        (folder / name).write_text(json.dumps(workflow, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(folder / name)


if __name__ == "__main__":
    main()
