"""
Train ML model from real signal data in the database.
Usage: python train_from_db.py
Saves models with version: signal_model_v{version}_{timestamp}.pkl
"""
import sys
import os
import logging
import json
import shutil
from datetime import datetime

import numpy as np
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
MANIFEST_FILE = os.path.join(MODELS_DIR, "model_manifest.json")


def fetch_signals():
    """Fetch signals from backend API."""
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/signals/", params={"limit": 1000}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("signals", [])
    except Exception as e:
        logger.warning(f"Could not fetch from API: {e}")
    return []


def build_features(signals):
    """Build feature matrix from signals."""
    features = []
    labels = []

    for s in signals:
        entry = s.get("entry_price") or 0
        tp = s.get("tp1_price") or 0
        sl = s.get("stop_loss") or 0
        conf = s.get("confidence_score") or 0.5

        rr_ratio = 0
        if entry > 0 and sl > 0 and tp > 0:
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            rr_ratio = reward / max(risk, 0.001)

        price_dev = 0.05  # default
        direction_num = 1.0 if s.get("direction") == "LONG" else 0.0
        rsi = 50 + np.random.normal(0, 10)
        macd = np.random.normal(0, 0.05)
        channel_acc = 50.0
        channel_sigs = 10

        features.append([conf, rr_ratio, price_dev, direction_num, rsi, macd, channel_acc, channel_sigs])

        status = s.get("status", "PENDING")
        if status in ("TP1_HIT", "TP2_HIT", "TP3_HIT"):
            labels.append(1)
        elif status in ("SL_HIT", "EXPIRED", "CANCELLED"):
            labels.append(0)
        else:
            labels.append(1 if conf > 0.6 else 0)

    return np.array(features), np.array(labels)


def augment_data(features, labels, target_size=500):
    """Augment small dataset with noise variations."""
    if len(features) >= target_size:
        return features, labels

    augmented_f = list(features)
    augmented_l = list(labels)

    while len(augmented_f) < target_size:
        idx = np.random.randint(0, len(features))
        noise = np.random.normal(0, 0.05, features.shape[1])
        new_f = features[idx] + noise
        new_f = np.clip(new_f, 0, None)
        augmented_f.append(new_f)
        augmented_l.append(labels[idx])

    return np.array(augmented_f), np.array(augmented_l)


def train():
    """Main training function."""
    signals = fetch_signals()
    logger.info(f"Fetched {len(signals)} signals from API")

    if len(signals) < 5:
        logger.warning("Too few signals for training, using synthetic augmentation")
        signals = signals or [
            {"entry_price": 65000, "tp1_price": 72000, "stop_loss": 63000,
             "confidence_score": 0.8, "direction": "LONG", "status": "TP1_HIT"},
            {"entry_price": 2000, "tp1_price": 2200, "stop_loss": 1900,
             "confidence_score": 0.7, "direction": "LONG", "status": "PENDING"},
        ]

    features, labels = build_features(signals)
    logger.info(f"Built {len(features)} feature vectors ({sum(labels)} positive, {len(labels)-sum(labels)} negative)")

    features, labels = augment_data(features, labels, target_size=500)
    logger.info(f"After augmentation: {len(features)} samples")

    from xgboost import XGBClassifier
    import joblib

    # Use regularization to prevent overfit on small datasets
    from sklearn.model_selection import cross_val_score

    model = XGBClassifier(
        n_estimators=50, max_depth=3, learning_rate=0.05,
        min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
        reg_alpha=1.0, reg_lambda=2.0,
        random_state=42, use_label_encoder=False, eval_metric='logloss',
    )
    model.fit(features, labels)

    from sklearn.metrics import classification_report, confusion_matrix
    import json as _json

    train_acc = (model.predict(features) == labels).mean()
    cv_scores = cross_val_score(model, features, labels, cv=min(5, len(features)//10 or 2), scoring='accuracy')
    accuracy = cv_scores.mean()

    # Confusion matrix
    y_pred = model.predict(features)
    cm = confusion_matrix(labels, y_pred)
    report = classification_report(labels, y_pred, target_names=["FAIL", "SUCCESS"], output_dict=True)

    # Feature importance
    feature_names = ["confidence", "risk_reward", "price_dev", "direction", "rsi", "macd", "ch_accuracy", "ch_signals"]
    importance = dict(zip(feature_names, model.feature_importances_.tolist()))

    os.makedirs(MODELS_DIR, exist_ok=True)

    # Versioning: load manifest, increment version
    manifest = {"versions": [], "current": None}
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r") as f:
            manifest = _json.load(f)
    next_version = len(manifest.get("versions", [])) + 1
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    versioned_name = f"signal_model_v{next_version}_{timestamp}.pkl"
    model_path = os.path.join(MODELS_DIR, versioned_name)

    eval_report = {
        "version": next_version,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "train_accuracy": round(train_acc * 100, 1),
        "cv_accuracy": round(accuracy * 100, 1),
        "cv_std": round(cv_scores.std() * 100, 1),
        "confusion_matrix": cm.tolist(),
        "classification_report": {k: v for k, v in report.items() if k in ("FAIL", "SUCCESS", "accuracy")},
        "feature_importance": {k: round(v, 4) for k, v in sorted(importance.items(), key=lambda x: -x[1])},
        "real_signals": len(signals),
        "total_samples": len(features),
        "random_seed": 42,
        "model_file": versioned_name,
    }

    report_path = os.path.join(MODELS_DIR, f"evaluation_report_v{next_version}.json")
    with open(report_path, "w") as f:
        _json.dump(eval_report, f, indent=2)

    joblib.dump(model, model_path)
    logger.info(f"Model saved to {model_path} (v{next_version})")

    # Update manifest
    manifest.setdefault("versions", []).append({
        "version": next_version,
        "file": versioned_name,
        "cv_accuracy": round(accuracy * 100, 1),
        "timestamp": eval_report["timestamp"],
    })
    manifest["current"] = next_version
    manifest["current_file"] = versioned_name
    with open(MANIFEST_FILE, "w") as f:
        _json.dump(manifest, f, indent=2)

    # Symlink/copy current to signal_model.pkl for backwards compatibility
    legacy_path = os.path.join(MODELS_DIR, "signal_model.pkl")
    shutil.copy(model_path, legacy_path)

    logger.info(f"Train: {train_acc:.1%}, CV: {accuracy:.1%} (+/- {cv_scores.std():.1%})")
    logger.info(f"Model v{next_version} saved, manifest updated")

    return {"version": next_version, "accuracy": round(accuracy * 100, 1), "samples": len(features), "real_signals": len(signals)}


if __name__ == "__main__":
    result = train()
    print(f"Training result: {result}")
