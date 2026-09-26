from fastapi import APIRouter
from app.services.ml_classifier import get_classifier

router = APIRouter(prefix="/api/model", tags=["model"])


@router.get("/metrics")
async def metrics():
    classifier = get_classifier()
    return {
        **classifier.metrics,
        "features": {"vectorizer": "word + character TF-IDF", "ngrams": "word 1–2, character 3–5", "classifier": "Logistic Regression", "class_weight": "balanced"},
        "notes": "Metrics use the public UCI SMS Spam Collection plus a small India-context supplement. Community submissions are queued as evidence and are never auto-trained without review.",
    }
