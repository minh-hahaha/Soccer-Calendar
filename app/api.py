"""Simplified API surface used in the tests.

The production code exposes a comprehensive FastAPI application under
``backend``.  For the purposes of the unit tests in this kata we only
need a very small subset of the functionality.  This module implements
that subset with intentionally light dependencies so that it can be
imported without requiring the full backend stack or a database
connection.  Test cases patch ``load_model``, ``get_db`` and
``get_features_for_match`` to supply controlled behaviour.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query

from .models import Match

# ---------------------------------------------------------------------------
# Dependency placeholders (patched in tests)
# ---------------------------------------------------------------------------


def load_model() -> None:  # pragma: no cover - replaced in tests
    """Load the ML model.  In tests this function is patched."""
    raise RuntimeError("Model loading not implemented")


def get_db():  # pragma: no cover - replaced in tests
    """Database dependency.  Tests patch this to provide a mock session."""
    raise RuntimeError("Database dependency not provided")


def get_features_for_match(db, match_id: int) -> Dict[str, float]:  # pragma: no cover
    """Feature builder placeholder.  Patched in tests."""
    raise RuntimeError("Feature extraction not implemented")


# Model artefacts – patched by tests
model = None
scaler = None
metadata: Dict[str, str] | None = None


app = FastAPI()


def _build_top_features(features: Dict[str, float]) -> List[Dict[str, float]]:
    """Create a basic top-feature list from the raw feature dictionary."""

    top = []
    for name in list(features.keys())[:5]:
        top.append({"name": name, "contribution": 0.0})
    return top


@app.get("/health")
def health() -> Dict[str, Optional[str]]:
    """Simple health check endpoint."""

    try:
        load_model()
        return {"status": "healthy", "model_version": None, "database_connected": True}
    except Exception:
        return {"status": "unhealthy", "model_version": None, "database_connected": False}


@app.get("/predict")
def predict(match_id: int, db=Depends(get_db)) -> Dict[str, object]:
    """Return prediction probabilities for a single match."""

    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    if getattr(match, "status", "") == "FINISHED":
        raise HTTPException(status_code=400, detail="Cannot predict finished matches")

    features = get_features_for_match(db, match_id)

    feature_values = [features.get(k, 0.0) for k in features.keys()]
    scaled = scaler.transform([feature_values])  # type: ignore[operator]
    probs = model.predict_proba(scaled)[0]  # type: ignore[operator]

    return {
        "match_id": match_id,
        "competition": "TEST",
        "kickoff": getattr(match, "utc_date", datetime.utcnow()),
        "home_team_id": getattr(match, "home_team_id", 0),
        "away_team_id": getattr(match, "away_team_id", 0),
        "probs": {"away": probs[0], "draw": probs[1], "home": probs[2]},
        "top_features": _build_top_features(features),
        "model_version": (metadata or {}).get("model_version", "unknown"),
        "calibrated": False,
        "data_quality": features.get("data_quality"),
    }


@app.post("/batch/predict")
def batch_predict(match_ids: List[int], db=Depends(get_db)) -> Dict[str, List[Dict[str, object]]]:
    """Predict multiple matches in one request."""

    predictions = []
    for match_id in match_ids:
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match or getattr(match, "status", "") == "FINISHED":
            continue

        features = get_features_for_match(db, match_id)
        feature_values = [features.get(k, 0.0) for k in features.keys()]
        scaled = scaler.transform([feature_values])  # type: ignore[operator]
        probs = model.predict_proba(scaled)[0]  # type: ignore[operator]

        predictions.append({
            "match_id": match_id,
            "competition": "TEST",
            "kickoff": getattr(match, "utc_date", datetime.utcnow()),
            "home_team_id": getattr(match, "home_team_id", 0),
            "away_team_id": getattr(match, "away_team_id", 0),
            "probs": {"away": probs[0], "draw": probs[1], "home": probs[2]},
            "top_features": _build_top_features(features),
            "model_version": (metadata or {}).get("model_version", "unknown"),
            "calibrated": False,
            "data_quality": features.get("data_quality"),
        })

    return {"predictions": predictions}


@app.get("/features")
def get_features(match_id: int, db=Depends(get_db)) -> Dict[str, object]:
    """Return the raw features for a given match."""

    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

    features = get_features_for_match(db, match_id)
    built_at = getattr(features, "built_at", datetime.utcnow())

    return {"match_id": match_id, "features": features, "built_at": built_at}


__all__ = [
    "app",
    "batch_predict",
    "get_db",
    "get_features",
    "get_features_for_match",
    "health",
    "load_model",
    "model",
    "predict",
    "scaler",
]

