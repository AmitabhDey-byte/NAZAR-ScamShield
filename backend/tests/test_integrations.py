from app.routers.integrations import _extract_twilio_payload


def test_twilio_accepts_original_form_fields_from_n8n():
    event = _extract_twilio_payload({"body": {
        "From": "whatsapp:+919000012345",
        "To": "whatsapp:+14155238886",
        "Body": "Please pay at https://example.test",
        "MessageSid": "SM123",
        "ProfileName": "Unknown",
    }})

    assert event.sender == "whatsapp:+919000012345"
    assert event.recipient == "whatsapp:+14155238886"
    assert event.body == "Please pay at https://example.test"
    assert event.message_sid == "SM123"
    assert event.profile_name == "Unknown"


def test_twilio_accepts_existing_flat_n8n_mapping():
    event = _extract_twilio_payload({
        "from": "+919000012345", "to": "+14155238886",
        "body": "Payment due", "MessageSid": "SM456", "channel": "sms",
    })

    assert event.sender == "+919000012345"
    assert event.body == "Payment due"
    assert event.channel == "sms"
