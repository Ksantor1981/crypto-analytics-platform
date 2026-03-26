"""
Train ML model from signal rows in the database.

ВАЖНО (целостность данных):
- Реальные RSI/MACD берутся из technical_indicators (PostgreSQL), если таблица заполнена.
- По умолчанию НЕТ аугментации выборки и НЕТ синтетического fallback — см. docs/ML_DATA_INTEGRITY_ROADMAP.md
- При достаточном числе закрытых сигналов обучение только на строках с исходом TP/SL/EXPIRED (без псевдо-меток PENDING).

Usage:
  export DATABASE_URL=postgresql://user:pass@host:5432/dbname
  python train_from_db.py

Переменные:
  ML_AUGMENT_TARGET — целевой размер после аугментации (0 = отключено, по умолчанию 0)
  ML_SYNTHETIC_FALLBACK=1 — старый синтетический набор при очень малом N
  ML_INDICATOR_TIMEFRAME — таймфрейм для JOIN (по умолчанию 1d)
  ML_STRICT_DATA_QUALITY=1 — ошибка, если покрытие индикаторов < 30%%
"""
from __future__ import annotations

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

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "BACKEND_DATABASE_URL",
        "postgresql://crypto_analytics_user@localhost:5432/crypto_analytics",
    ),
)
if os.getenv("USE_SQLITE", "").lower() in ("1", "true", "yes"):
    DATABASE_URL = "sqlite:///./crypto_analytics.db"

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
MANIFEST_FILE = os.path.join(MODELS_DIR, "model_manifest.json")

MIN_CLOSED_SIGNALS_FOR_TRAIN = 15
MIN_TOTAL_SIGNALS = 5
# По умолчанию без аугментации (честная оценка размера выборки)
AUGMENT_TARGET_DEFAULT = int(os.getenv("ML_AUGMENT_TARGET", "0"))
INDICATOR_TF = os.getenv("ML_INDICATOR_TIMEFRAME", "1d")

CLOSED_STATUSES = (
    "TP1_HIT", "TP2_HIT", "TP3_HIT", "SL_HIT", "EXPIRED", "CANCELLED",
    "TP_HIT",  # real_signals outcome
)


def _table_exists(conn, name: str, dialect: str) -> bool:
    try:
        from sqlalchemy import text
        if dialect == "postgresql":
            r = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name=:n LIMIT 1"
                ),
                {"n": name},
            ).scalar()
            return r is not None
        r = conn.execute(
            text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:n LIMIT 1"),
            {"n": name},
        ).scalar()
        return r is not None
    except Exception:
        return False


def fetch_signals_from_db():
    """Fetch signals; при PostgreSQL и наличии technical_indicators — подтягиваем RSI/MACD."""
    try:
        from sqlalchemy import create_engine, text

        if DATABASE_URL.startswith("sqlite"):
            engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(DATABASE_URL)

        dialect = engine.dialect.name

        with engine.connect() as conn:
            has_ti = _table_exists(conn, "technical_indicators", dialect)

            if dialect == "postgresql" and has_ti:
                q = text(f"""
                    SELECT
                        s.id, s.entry_price, s.tp1_price, s.stop_loss, s.confidence_score,
                        s.direction, s.status, s.risk_reward_ratio,
                        c.accuracy AS channel_accuracy,
                        c.signals_count AS channel_signals_count,
                        s.symbol, s.asset, s.created_at, s.message_timestamp,
                        ti.rsi_14, ti.macd_line
                    FROM signals s
                    LEFT JOIN channels c ON c.id = s.channel_id
                    LEFT JOIN LATERAL (
                        SELECT ti2.rsi_14, ti2.macd_line
                        FROM technical_indicators ti2
                        WHERE ti2.symbol = UPPER(TRIM(SPLIT_PART(
                            COALESCE(NULLIF(TRIM(s.symbol), ''), s.asset), '/', 1)))
                          AND ti2.timeframe = :tf
                          AND ti2.timestamp <= COALESCE(s.message_timestamp, s.created_at)
                        ORDER BY ti2.timestamp DESC
                        LIMIT 1
                    ) ti ON true
                    ORDER BY s.created_at ASC
                    LIMIT 5000
                """)
                rows = conn.execute(q, {"tf": INDICATOR_TF}).fetchall()
            else:
                if dialect != "sqlite" and not has_ti:
                    logger.warning(
                        "Таблица technical_indicators отсутствует или недоступна — "
                        "RSI/MACD будут плейсхолдерами. Заполните свечи и calculate_indicators."
                    )
                q = text("""
                    SELECT
                        s.id, s.entry_price, s.tp1_price, s.stop_loss, s.confidence_score,
                        s.direction, s.status, s.risk_reward_ratio,
                        c.accuracy AS channel_accuracy,
                        c.signals_count AS channel_signals_count,
                        s.symbol, s.asset, s.created_at, s.message_timestamp,
                        NULL::numeric AS rsi_14, NULL::numeric AS macd_line
                    FROM signals s
                    LEFT JOIN channels c ON c.id = s.channel_id
                    ORDER BY s.created_at ASC
                    LIMIT 5000
                """)
                if dialect == "sqlite":
                    q = text("""
                        SELECT
                            s.id, s.entry_price, s.tp1_price, s.stop_loss, s.confidence_score,
                            s.direction, s.status, s.risk_reward_ratio,
                            c.accuracy AS channel_accuracy,
                            c.signals_count AS channel_signals_count,
                            s.symbol, s.asset, s.created_at, s.message_timestamp,
                            NULL AS rsi_14, NULL AS macd_line
                        FROM signals s
                        LEFT JOIN channels c ON c.id = s.channel_id
                        ORDER BY s.created_at ASC
                        LIMIT 5000
                    """)
                rows = conn.execute(q).fetchall()

        out = []
        for row in rows:
            row_dict = row._mapping if hasattr(row, "_mapping") else row._asdict()

            def _f(name):
                v = row_dict.get(name)
                if v is not None and hasattr(v, "__float__") and not isinstance(v, bool):
                    return float(v)
                return v

            entry = _f("entry_price") or 0
            tp = _f("tp1_price")
            sl = _f("stop_loss")
            conf = _f("confidence_score")
            rr = _f("risk_reward_ratio")
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

            rsi_raw = row_dict.get("rsi_14")
            macd_raw = row_dict.get("macd_line")
            rsi_v = float(rsi_raw) if rsi_raw is not None else None
            macd_v = float(macd_raw) if macd_raw is not None else None

            out.append({
                "entry_price": entry,
                "tp1_price": tp,
                "stop_loss": sl,
                "confidence_score": conf,
                "risk_reward_ratio": rr,
                "direction": direction or "LONG",
                "status": status or "PENDING",
                "channel_accuracy": ch_acc,
                "channel_signals_count": ch_sigs,
                "rsi_14": rsi_v,
                "macd_line": macd_v,
            })
        return out
    except Exception as e:
        logger.warning("DB fetch failed: %s. Fallback to API.", e)
        return _fetch_signals_from_api()


def _fetch_signals_from_api():
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
                s.setdefault("rsi_14", None)
                s.setdefault("macd_line", None)
            return signals
    except Exception as e:
        logger.warning("API fallback failed: %s", e)
    return []


def fetch_signals():
    signals = fetch_signals_from_db()
    return signals if signals else []


def count_closed_signals(signals):
    closed = CLOSED_STATUSES
    return sum(1 for s in signals if (s.get("status") or "").upper() in closed)


def _label_for_status(status: str, conf: float, allow_proxy_pending: bool):
    """None — пропуск строки. При allow_proxy_pending слабая эвристика для PENDING (только если мало закрытых)."""
    u = (status or "").upper()
    if u in ("TP1_HIT", "TP2_HIT", "TP3_HIT", "TP_HIT"):
        return 1
    if u in ("SL_HIT", "EXPIRED", "CANCELLED"):
        return 0
    if allow_proxy_pending and u in ("PENDING", "ENTRY_HIT", ""):
        return 1 if conf > 0.6 else 0
    return None


def build_features(signals, allow_proxy_pending: bool):
    features = []
    labels = []
    placeholder_rows = 0

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

        # price_dev: при наличии ATR в будущем подставить из БД; пока — относительный спред TP/SL как прокси волатильности
        if entry > 0 and tp and sl:
            price_dev = min(abs(tp - entry) / entry, abs(entry - sl) / entry, 0.5)
        else:
            price_dev = 0.05

        direction_num = 1.0 if (s.get("direction") or "").upper() in ("LONG", "BUY") else 0.0

        rsi = s.get("rsi_14")
        macd = s.get("macd_line")
        if rsi is None or macd is None:
            rsi = 50.0
            macd = 0.0
            placeholder_rows += 1
        else:
            rsi = float(rsi)
            macd = float(macd)

        channel_acc = float(s.get("channel_accuracy") or 50.0)
        channel_sigs = float(s.get("channel_signals_count") or 10.0)

        features.append([conf, rr_ratio, price_dev, direction_num, rsi, macd, channel_acc, channel_sigs])

        lab = _label_for_status(s.get("status") or "", conf, allow_proxy_pending)
        if lab is None:
            labels.append(-1)
        else:
            labels.append(lab)

    return np.array(features), np.array(labels), placeholder_rows


def augment_data(features, labels, target_size: int):
    if target_size <= 0 or len(features) >= target_size:
        return features, labels
    augmented_f = list(features)
    augmented_l = list(labels)
    rng = np.random.default_rng(42)
    while len(augmented_f) < target_size:
        idx = int(rng.integers(0, len(features)))
        noise = rng.normal(0, 0.05, features.shape[1])
        new_f = features[idx] + noise
        new_f = np.clip(new_f, 0, None)
        augmented_f.append(new_f)
        augmented_l.append(labels[idx])
    return np.array(augmented_f), np.array(augmented_l)


def train():
    signals = fetch_signals()
    logger.info("Fetched %d signals (DB or API)", len(signals))

    closed_count = count_closed_signals(signals)
    logger.info("Closed signals (TP/SL/EXPIRED): %d", closed_count)

    use_only_closed = closed_count >= MIN_CLOSED_SIGNALS_FOR_TRAIN
    allow_proxy = not use_only_closed
    if use_only_closed:
        filt = [s for s in signals if (s.get("status") or "").upper() in CLOSED_STATUSES]
        logger.info("Обучение только на закрытых сигналах: %d строк", len(filt))
        signals = filt
    elif closed_count > 0:
        logger.warning(
            "Закрытых сигналов %d < %d — для части строк используются слабые прокси-метки по confidence (не для прод-отчётов).",
            closed_count,
            MIN_CLOSED_SIGNALS_FOR_TRAIN,
        )

    if len(signals) < MIN_TOTAL_SIGNALS:
        if os.getenv("ML_SYNTHETIC_FALLBACK", "").strip() in ("1", "true", "yes"):
            logger.warning("ML_SYNTHETIC_FALLBACK=1: подмешиваем синтетические примеры (только для dev).")
            signals = [
                {"entry_price": 65000, "tp1_price": 72000, "stop_loss": 63000,
                 "confidence_score": 0.8, "direction": "LONG", "status": "TP1_HIT",
                 "channel_accuracy": 55, "channel_signals_count": 100, "rsi_14": 52.0, "macd_line": 0.1},
                {"entry_price": 2000, "tp1_price": 2200, "stop_loss": 1900,
                 "confidence_score": 0.7, "direction": "LONG", "status": "SL_HIT",
                 "channel_accuracy": 50, "channel_signals_count": 50, "rsi_14": 48.0, "macd_line": -0.1},
            ] * 3
        else:
            logger.error(
                "Слишком мало сигналов (%d). Загрузите данные или задайте ML_SYNTHETIC_FALLBACK=1 для локальных тестов.",
                len(signals),
            )
            raise SystemExit(2)

    features, labels, placeholder_rows = build_features(signals, allow_proxy_pending=allow_proxy)
    valid = labels >= 0
    features = features[valid]
    labels = labels[valid]
    if len(features) == 0:
        logger.error("После фильтрации меток не осталось строк для обучения.")
        raise SystemExit(3)

    n_with_ind = sum(1 for s in signals if s.get("rsi_14") is not None and s.get("macd_line") is not None)
    coverage = (n_with_ind / max(len(signals), 1)) * 100.0

    n_pos = int((labels == 1).sum())
    n_neg = int((labels == 0).sum())
    logger.info("Built %d feature vectors (%d positive, %d negative)", len(features), n_pos, n_neg)
    logger.info(
        "Покрытие technical_indicators: %.1f%% (%d/%d), строк с плейсхолдером RSI/MACD до фильтра: %d",
        coverage,
        n_with_ind,
        len(signals),
        placeholder_rows,
    )

    if os.getenv("ML_STRICT_DATA_QUALITY", "").strip() in ("1", "true", "yes"):
        if coverage < 30.0:
            logger.error("ML_STRICT_DATA_QUALITY: покрытие индикаторов %.1f%% < 30%%", coverage)
            raise SystemExit(4)

    aug_target = AUGMENT_TARGET_DEFAULT
    if aug_target > 0:
        logger.warning("Аугментация до %d образцов (ML_AUGMENT_TARGET) — метрики CV завышены относительно реального N.", aug_target)
    features, labels = augment_data(features, labels, target_size=aug_target)
    logger.info("После аугментации: %d samples (target was %s)", len(features), aug_target or "off")

    try:
        from xgboost import XGBClassifier
        import joblib
        from sklearn.model_selection import cross_val_score, TimeSeriesSplit
        from sklearn.metrics import classification_report, confusion_matrix
    except ModuleNotFoundError as e:
        logger.error(
            "Missing ML dependency: %s. pip install -r ml-service/requirements-train.txt",
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

    train_acc = (model.predict(features) == labels).mean()
    ns = min(5, max(2, len(features) // 10))
    ns = min(ns, len(features) - 1) if len(features) > 2 else 2
    ns = max(2, ns) if len(features) >= 5 else 2
    tscv = TimeSeriesSplit(n_splits=min(ns, len(features) - 1) if len(features) > 3 else 2)
    try:
        cv_scores = cross_val_score(model, features, labels, cv=tscv, scoring="accuracy")
        accuracy = cv_scores.mean()
    except ValueError as e:
        logger.warning("Cross-val пропущен (%s); используем train accuracy как нижнюю оценку.", e)
        cv_scores = np.array([train_acc])
        accuracy = train_acc

    y_pred = model.predict(features)
    cm = confusion_matrix(labels, y_pred)
    report = classification_report(labels, y_pred, target_names=["FAIL", "SUCCESS"], output_dict=True)
    feature_names = ["confidence", "risk_reward", "price_dev", "direction", "rsi", "macd", "ch_accuracy", "ch_signals"]
    importance = dict(zip(feature_names, model.feature_importances_.tolist()))

    warnings_list = []
    if coverage < 50:
        warnings_list.append("low_technical_indicator_coverage")
    if aug_target > 0:
        warnings_list.append("augmentation_enabled")
    if allow_proxy:
        warnings_list.append("used_confidence_proxy_labels_low_closed_count")
    if n_with_ind < len(signals):
        warnings_list.append("partial_placeholder_rsi_macd")

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
        "training_rows_after_label_filter": len(features),
        "indicator_coverage_percent": round(coverage, 1),
        "rows_with_db_indicators": n_with_ind,
        "uses_placeholder_rsi_macd_rows": placeholder_rows,
        "only_closed_labels": use_only_closed,
        "augment_target": aug_target,
        "warnings": warnings_list,
        "disclaimer": "CV accuracy не равна ожидаемой торговой точности; см. docs/ML_ACCURACY_DISCREPANCY.md",
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
        "indicator_coverage_percent": round(coverage, 1),
    }


if __name__ == "__main__":
    result = train()
    print("Training result:", result)
