from app.schemas import TransactionContext
from app.services.analyzer import full_analysis, transaction_analysis, url_analysis


def test_electricity_scam_is_dangerous():
    result = full_analysis(
        "Your electricity connection will be disconnected tonight. Pay ₹4980 immediately at ramesh123@oksbi using https://electric-bill-secure.xyz"
    )
    assert result["classification"] == "DANGEROUS"
    assert result["score"] >= 70
    assert result["entities"]["upi_ids"] == ["ramesh123@oksbi"]


def test_normal_friend_payment_is_not_dangerous():
    result = full_analysis("Dinner was lovely, send me ₹350 when free")
    assert result["classification"] != "DANGEROUS"


def test_suspicious_url_rules():
    score, reasons, _ = url_analysis("http://sbi-account-verify.top/login")
    assert score >= 70
    assert any("official domain" in reason for reason in reasons)


def test_transaction_anomaly():
    score, _ = transaction_analysis(TransactionContext(amount=25000, payee="secure-refund@okaxis", is_new_recipient=True, transaction_hour=1, recent_frequency=8))
    assert score >= 80

