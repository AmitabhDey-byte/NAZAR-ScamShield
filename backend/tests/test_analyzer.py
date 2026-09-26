from app.schemas import TransactionContext
from app.services.analyzer import full_analysis, transaction_analysis, url_analysis
from app.services.ml_classifier import get_classifier
from app.services.url_intelligence import score_url_intelligence


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


def test_new_domain_and_reputation_hits_raise_external_url_risk():
    new_score, new_reasons = score_url_intelligence(4, [])
    matched_score, matched_reasons = score_url_intelligence(900, ["Google Safe Browsing"])
    assert new_score >= 40
    assert any("registered" in reason for reason in new_reasons)
    assert matched_score == 100
    assert any("Google Safe Browsing" in reason for reason in matched_reasons)


def test_metrics_use_a_separate_held_out_test_set():
    metrics = get_classifier().metrics
    assert metrics["method"] == "Stratified 80/20 held-out test set"
    assert metrics["train_sample_count"] + metrics["test_sample_count"] == metrics["sample_count"]
    assert all(0 <= metrics[name] <= 1 for name in ("precision", "recall", "f1"))
