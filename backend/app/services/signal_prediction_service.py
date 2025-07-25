class SignalPredictionService:
    def __init__(self):
        self.is_trained = True
        self.model_accuracy = 0.85
    def get_model_status(self):
        return {"is_trained": True, "model_accuracy": 0.85}
signal_prediction_service = SignalPredictionService()
