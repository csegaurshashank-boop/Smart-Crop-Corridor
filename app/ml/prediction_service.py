import joblib  # type: ignore
import os
import numpy as np  # type: ignore

MODEL_PATH = os.path.join(os.path.dirname(__file__), "crop_model.pkl")

_model = None


def load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                "Run: python -m app.ml.train_model"
            )
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_crop(
    N: float,
    P: float,
    K: float,
    temperature: float,
    humidity: float,
    rainfall: float,
    ndvi: float,
) -> dict:
    model = load_model()
    features = np.array([[N, P, K, temperature, humidity, rainfall, ndvi]])
    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    classes = model.classes_

    confidence = float(max(probabilities))
    top_predictions = sorted(
        zip(classes, probabilities), key=lambda x: x[1], reverse=True
    )[:3]

    return {
        "recommended_crop": prediction,
        "confidence": round(confidence, 3),
        "top_3": [
            {"crop": c, "probability": round(float(p), 3)}
            for c, p in top_predictions
        ],
    }