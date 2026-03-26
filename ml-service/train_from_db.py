"""
Train ML model from real signal data in the database.
Uses direct DB connection (DATABASE_URL). No API auth required.

Usage:
  export DATABASE_URL=postgresql://user:pass@host:5432/dbname
  python train_from_db.py

  Or from backend root: python -m ml_service.train_from_db (if PYTHONPATH includes project root)

Saves models with version: signal_model_v{version}_{timestamp}.pkl
"""
import os
import sys
import logging
import json
import shutil
from datetime import datetime, timezone
from decimal import Decimal

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database: same as backend. Example: postgresql://user:pass@localhost:5432/crypto_analytics
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "BACKEND_DATABASE_URL",
        "postgresql://crypto_analytics_user@localhost:5432/crypto_analytics",
    ),
)
# Fallback for SQLite (e.g. tests)
if os.getenv("USE_SQLITE", "").lower() in ("1", "true", "yes"):
    DATABASE_URL = "sqlite:///./crypto_analytics.db"

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
MANIFEST_FILE = os.path.join(MODELS_DIR, "model_manifest.json")

# Обучать только при наличии минимум N сигналов с известным исходом (TP/SL/EXPIRED)
MIN_CLOSED_SIGNALS_FOR_TRAIN = 15
# Минимум всего сигналов для обучения (иначе — синтетика или пропуск)
MIN_TOTAL_SIGNALS = 5
# Целевой размер выборки после аугментации
AUGMENT_TARGET_SIZE = 500


def fetch_signals_from_db():
    """Fetch signals with channel metrics directly from DB."""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import Engine

        if DATABASE_URL.startswith("sqlite"):
            engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # signals + channel.accuracy, channel.signals_count
            q = text("""
                SELECT
                    s.id, s.entry_price, s.tp1_price, s.stop_loss, s.confidence_score,
                    s.direction, s.status, s.risk_reward_ratio,
                    c.accuracy AS channel_accuracy,
                    c.signals_count AS channel_signals_count
                FROM signals s
                LEFT JOIN channels c ON c.id = s.channel_id
                ORDER BY s.created_at DESC
                LIMIT 5000
            """)
            rows = conn.execute(q).fetchall()

        out = []
        for row in rows:
            row_dict = row._mapping if hasattr(row, "_mapping") else row._asdict()
            entry = row_dict.get("entry_price")
            if entry is not None and hasattr(entry, "__float__"):
                entry = float(entry)
            tp = row_dict.get("tp1_price")
            if tp is not None and hasattr(tp, "__float__"):
                tp = float(tp)
            sl = row_dict.get("stop_loss")
            if sl is not None and hasattr(sl, "__float__"):
                sl = float(sl)
            conf = row_dict.get("confidence_score")
            if conf is not None and hasattr(conf, "__float__"):
                conf = float(conf)
            rr = row_dict.get("risk_reward_ratio")
            if rr is not None and hasattr(rr, "__float__"):
                rr = float(rr)
            ch_acc = row_dict.get("channel_accuracy")
            ch_acc = float(ch_acc) if ch_acc is not None else None
            ch_sigs = row_dict.get("channel_signals_count")
            ch_sigs = int(ch_sigs) if ch_sigs is not None else None
            direction = row_dict.get("direction")
            if hasattr(direction, "value"):
                direction = direction.value
            status = row_dict.get("status")
            if hasattr(status, "value"):
                status = status.value
            out.append({
                "entry_price": entry or 0,
                "tp1_price": tp,
                "stop_loss": sl,
                "confidence_score": conf,
                "risk_reward_ratio": rr,
                "direction": direction or "LONG",
                "status": status or "PENDING",
                "channel_accuracy": ch_acc,
                "channel_signals_count": ch_sigs,
            })
        return out
    except Exception as e:
        logger.warning("DB fetch failed: %s. Fallback to API.", e)
        return _fetch_signals_from_api()


def _fetch_signals_from_api():
    """Fallback: fetch from backend API (requires auth token or public endpoint)."""
    try:
        import requests
        token = os.getenv("TRAIN_API_TOKEN")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = requests.get(
            f"{BACKEND_URL}/api/v1/signals/",
            params={"limit": 1000},
            timeout=10,
            headers=headers,
        )
        if resp.status_code == 200:
            data = resp.json()
            signals = data.get("signals", [])
            for s in signals:
                s.setdefault("channel_accuracy", None)
                s.setdefault("channel_signals_count", None)
            return signals
    except Exception as e:
        logger.warning("API fallback failed: %s", e)
    return []


def fetch_signals():
    """Preferred: DB. Fallback: API."""
    signals = fetch_signals_from_db()
    if not signals:
        return []
    return signals


def count_closed_signals(signals):
    """Number of signals with resolved outcome (TP/SL/EXPIRED/CANCELLED)."""
    closed = ("TP1_HIT", "TP2_HIT", "TP3_HIT", "SL_HIT", "EXPIRED", "CANCELLED")
    return sum(1 for s in signals if (s.get("status") or "").upper() in closed)


def build_features(signals):
    """Build feature matrix from signals. Real channel_accuracy and channel_signals_count."""
    features = []
    labels = []

    for s in signals:
        entry = s.get("entry_price") or 0
        tp = s.get("tp1_price") or 0
        sl = s.get("stop_loss") or 0
        conf = float(s.get("confidence_score") or 0.5)
        if isinstance(conf, Decimal):
            conf = float(conf)

        rr_ratio = float(s.get("risk_reward_ratio") or 0)
        if rr_ratio <= 0 and entry > 0 and sl and tp:
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            rr_ratio = reward / max(risk, 0.001)

        price_dev = 0.05
        direction_num = 1.0 if (s.get("direction") or "").upper() in ("LONG", "BUY") else 0.0
        rsi = 50.0  # placeholder until real market data
        macd = 0.0  # placeholder
        channel_acc = float(s.get("channel_accuracy") or 50.0)
        channel_sigs = float(s.get("channel_signals_count") or 10.0)

        features.append([conf, rr_ratio, price_dev, direction_num, rsi, macd, channel_acc, channel_sigs])

        status = (s.get("status") or "PENDING").upper()
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
    """Main training function. Skips real training if too few closed signals."""
    signals = fetch_signals()
    logger.info("Fetched %d signals (DB or API)", len(signals))

    closed_count = count_closed_signals(signals)
    logger.info("Closed signals (TP/SL/EXPIRED): %d", closed_count)

    if len(signals) < MIN_TOTAL_SIGNALS:
        logger.warning("Too few signals (min %d). Using synthetic data.", MIN_TOTAL_SIGNALS)
        signals = [
            {"entry_price": 65000, "tp1_price": 72000, "stop_loss": 63000,
             "confidence_score": 0.8, "direction": "LONG", "status": "TP1_HIT",
             "channel_accuracy": 55, "channel_signals_count": 100},
            {"entry_price": 2000, "tp1_price": 2200, "stop_loss": 1900,
             "confidence_score": 0.7, "direction": "LONG", "status": "PENDING",
             "channel_accuracy": 50, "channel_signals_count": 50},
        ] * 3

    features, labels = build_features(signals)
    n_pos = int(labels.sum())
    n_neg = len(labels) - n_pos
    logger.info("Built %d feature vectors (%d positive, %d negative)", len(features), n_pos, n_neg)

    if closed_count < MIN_CLOSED_SIGNALS_FOR_TRAIN and len(signals) >= MIN_TOTAL_SIGNALS:
        logger.warning(
            "Closed signals %d < %d. Training will use PENDING labels (confidence proxy). "
            "Retrain when more outcomes are available.",
            closed_count, MIN_CLOSED_SIGNALS_FOR_TRAIN,
        )

    features, labels = augment_data(features, labels, target_size=AUGMENT_TARGET_SIZE)
    logger.info("After augmentation: %d samples", len(features))

    try:
        from xgboost import XGBClassifier
        import joblib
        from sklearn.model_selection import cross_val_score
        from sklearn.metrics import classification_report, confusion_matrix
    except ModuleNotFoundError as e:
        logger.error(
            "Missing ML dependency: %s. From project root: pip install -r ml-service/requirements-train.txt",
            e.name,
        )
        raise SystemExit(1) from e
    import json as _json

    xgb_params = dict(
        n_estimators=50, max_depth=3, learning_rate=0.05,
        min_child_weight=5, subsample=0.8, colsample_bytree=0.8,
        reg_alpha=1.0, reg_lambda=2.0, random_state=42,
    )
    try:
        import xgboost as _xgb
        if getattr(_xgb, "__version__", "0").startswith(("0.", "1.", "2.")):
            xgb_params["use_label_encoder"] = False
            xgb_params["eval_metric"] = "logloss"
    except Exception:
        pass
    model = XGBClassifier(**xgb_params)
    model.fit(features, labels)

    from sklearn.model_selection import TimeSeriesSplit

    train_acc = (model.predict(features) == labels).mean()
    tscv = TimeSeriesSplit(n_splits=min(5, max(2, len(features) // 10)))
    cv_scores = cross_val_score(model, features, labels, cv=tscv, scoring="accuracy")
    accuracy = cv_scores.mean()

    y_pred = model.predict(features)
    cm = confusion_matrix(labels, y_pred)
    report = classification_report(labels, y_pred, target_names=["FAIL", "SUCCESS"], output_dict=True)
    feature_names = ["confidence", "risk_reward", "price_dev", "direction", "rsi", "macd", "ch_accuracy", "ch_signals"]
    importance = dict(zip(feature_names, model.feature_importances_.tolist()))

    os.makedirs(MODELS_DIR, exist_ok=True)
    manifest = {"versions": [], "current": None}
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r") as f:
            manifest = _json.load(f)
    next_version = len(manifest.get("versions", [])) + 1
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    versioned_name = f"signal_model_v{next_version}_{timestamp}.pkl"
    model_path = os.path.join(MODELS_DIR, versioned_name)

    eval_report = {
        "version": next_version,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "train_accuracy": round(train_acc * 100, 1),
        "cv_accuracy": round(accuracy * 100, 1),
        "cv_std": round(cv_scores.std() * 100, 1),
        "confusion_matrix": cm.tolist(),
        "classification_report": {k: v for k, v in report.items() if k in ("FAIL", "SUCCESS", "accuracy")},
        "feature_importance": {k: round(v, 4) for k, v in sorted(importance.items(), key=lambda x: -x[1])},
        "real_signals": len(signals),
        "closed_signals": count_closed_signals(signals),
        "total_samples": len(features),
        "random_seed": 42,
        "model_file": versioned_name,
    }

    report_path = os.path.join(MODELS_DIR, f"evaluation_report_v{next_version}.json")
    with open(report_path, "w") as f:
        _json.dump(eval_report, f, indent=2)

    joblib.dump(model, model_path)
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

    legacy_path = os.path.join(MODELS_DIR, "signal_model.pkl")
    shutil.copy(model_path, legacy_path)

    logger.info("Train: %.1f%%, CV: %.1f%% (+/- %.1f%%)", train_acc * 100, accuracy * 100, cv_scores.std() * 100)
    logger.info("Model v%d saved, manifest updated", next_version)
    return {
        "version": int(next_version),
        "accuracy": float(round(accuracy * 100, 1)),
        "samples": int(len(features)),
        "real_signals": len(signals),
        "closed_signals": int(closed_count),
    }


if __name__ == "__main__":
    result = train()
    print("Training result:", result)
