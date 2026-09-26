from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class TransactionContext(BaseModel):
    amount: float = Field(default=0, ge=0, le=10_000_000)
    payee: str = Field(default="", max_length=180)
    is_new_recipient: bool = False
    transaction_hour: int = Field(default=12, ge=0, le=23)
    recent_frequency: int = Field(default=0, ge=0, le=100)


class MessageAnalyzeRequest(BaseModel):
    text: str = Field(min_length=3, max_length=20_000)


class UrlAnalyzeRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)


class FullAnalyzeRequest(BaseModel):
    text: str = Field(min_length=3, max_length=20_000)
    url: str | None = Field(default=None, max_length=2048)
    transaction: TransactionContext | None = None


class AnalysisResponse(BaseModel):
    id: str
    score: float
    classification: str
    category: str
    reasons: list[str]
    entities: dict
    component_scores: dict[str, float]
    recommended_action: str
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_summary: str | None = None
    ai_confidence: float | None = None
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class ReportCreate(BaseModel):
    phone_number: str | None = Field(default=None, max_length=40)
    upi_id: str | None = Field(default=None, max_length=150)
    url: str | None = Field(default=None, max_length=2048)
    message: str = Field(default="", max_length=20_000)
    scam_category: str = Field(default="payment_request_scam", max_length=64)

    @model_validator(mode="after")
    def require_evidence(self):
        self.message = self.message.strip()
        if not any([self.message, self.phone_number, self.upi_id, self.url]):
            raise ValueError("Add a message, phone number, UPI ID, or URL")
        return self


class HoneypotStartRequest(BaseModel):
    analysis_id: str | None = None
    enable_canary: bool = False


class HoneypotMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class CallAnalyzeRequest(BaseModel):
    transcript: str = Field(min_length=10, max_length=30_000)
    caller_number: str | None = Field(default=None, max_length=40)


class DeviceRegisterRequest(BaseModel):
    pair_code: str = Field(min_length=6, max_length=8)
    device_name: str = Field(min_length=2, max_length=120)
    platform: str = Field(default="android", pattern="^(android|ios)$")
    app_version: str = Field(default="1.0.0", max_length=32)


class MobileEventCreate(BaseModel):
    text: str = Field(min_length=3, max_length=20_000)
    source_package: str = Field(default="manual", max_length=180)
    source_label: str = Field(default="Shared text", max_length=100)
    occurred_at: datetime | None = None


class GmailWebhookRequest(BaseModel):
    """Normalized or raw-ish Gmail event fields sent by n8n."""
    sender: str | None = Field(default=None, max_length=320, alias="from")
    subject: str = Field(default="", max_length=500)
    text: str = Field(default="", max_length=40_000)
    html: str = Field(default="", max_length=80_000)
    snippet: str = Field(default="", max_length=2_000)
    message_id: str | None = Field(default=None, max_length=200)
    thread_id: str | None = Field(default=None, max_length=200)
    received_at: datetime | None = None
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TwilioWebhookRequest(BaseModel):
    sender: str | None = Field(default=None, alias="from", max_length=320)
    recipient: str | None = Field(default=None, alias="to", max_length=320)
    body: str = Field(default="", min_length=1, max_length=20_000)
    message_sid: str | None = Field(default=None, alias="MessageSid", max_length=100)
    channel: str = Field(default="sms", max_length=32)
    profile_name: str | None = Field(default=None, alias="ProfileName", max_length=160)
    model_config = ConfigDict(populate_by_name=True, extra="allow")
