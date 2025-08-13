import pandas as pd
from sqlalchemy.orm import Session
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os
from datetime import datetime

from ..models import SignalResult

MODEL_DIR = "./ml_models"
MODEL_PATH = os.path.join(MODEL_DIR, "signal_model.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "metadata.json")

class SignalPredictionService:
    def __init__(self, db: Session):
        self.db = db
        self.model = None
        self.load_model()
        os.makedirs(MODEL_DIR, exist_ok=True)

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)

    def get_model_status(self):
        if not os.path.exists(MODEL_PATH) or not os.path.exists(METADATA_PATH):
            return {"model_trained": False}
        
        with open(METADATA_PATH, 'r') as f:
            import json
            metadata = json.load(f)
        
        return {
            "model_trained": True,
            "last_trained": metadata.get("last_trained"),
            "model_version": metadata.get("model_version"),
            "training_accuracy": metadata.get("training_accuracy")
        }

    def train_model(self):
        results = self.db.query(SignalResult).all()
        if len(results) < 20: # Минимальное количество данных для обучения
            return {"status": "failed", "message": "Not enough data to train model", "details": {"current_samples": len(results), "required_samples": 20}}

        data = pd.DataFrame([r.__dict__ for r in results])
        
        # Простая подготовка данных
        features = ['pnl', 'duration_minutes', 'max_drawdown', 'risk_reward_ratio']
        target = 'is_success'
        
        df = data[features + [target]].copy()
        df.dropna(inplace=True)

        if df.shape[0] < 20:
            return {"status": "failed", "message": "Not enough clean data to train model", "details": {"clean_samples": df.shape[0], "required_samples": 20}}

        X = df[features]
        y = df[target]

        if len(y.unique()) < 2:
            return {"status": "failed", "message": "Target variable must have at least two classes.", "details": {"unique_classes": len(y.unique())}}

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Оценка модели
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Сохранение модели и метаданных
        joblib.dump(model, MODEL_PATH)
        self.model = model
        
        metadata = {
            "last_trained": datetime.utcnow().isoformat(),
            "model_version": "1.0.0",
            "training_accuracy": accuracy,
            "training_samples": len(df)
        }
        with open(METADATA_PATH, 'w') as f:
            import json
            json.dump(metadata, f)

        return {"status": "success", "message": "Model trained successfully", "details": metadata}

    def predict(self, signal_id: int):
        if not self.model:
            raise ValueError("Model is not trained yet.")
        
        result = self.db.query(SignalResult).filter(SignalResult.signal_id == signal_id).first()
        if not result:
            raise ValueError(f"SignalResult with signal_id {signal_id} not found.")

        features = pd.DataFrame([{
            'pnl': result.pnl,
            'duration_minutes': result.duration_minutes,
            'max_drawdown': result.max_drawdown,
            'risk_reward_ratio': result.risk_reward_ratio
        }])
        
        prediction = self.model.predict_proba(features)[:, 1]
        return {"signal_id": signal_id, "prediction": prediction[0]}

    def batch_predict(self, signal_ids: list[int]):
        predictions = []
        for signal_id in signal_ids:
            try:
                prediction = self.predict(signal_id)
                predictions.append(prediction)
            except ValueError:
                # Пропускаем сигналы без данных
                continue
        return {"predictions": predictions}
