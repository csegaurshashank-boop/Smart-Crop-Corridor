"""
Run this script once to train and save the crop recommendation model:
    python -m app.ml.train_model
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "crop_model.pkl")


def generate_synthetic_data(n_samples: int = 2000) -> pd.DataFrame:
    """Generate synthetic crop dataset for training."""
    np.random.seed(42)
    crops = {
        "wheat":   dict(N=(60,100),  P=(30,60),   K=(40,80),   temp=(15,25), humidity=(50,70), rainfall=(200,400), ndvi=(0.4,0.8)),
        "rice":    dict(N=(80,120),  P=(40,80),   K=(40,80),   temp=(20,35), humidity=(70,90), rainfall=(800,1500),ndvi=(0.5,0.9)),
        "maize":   dict(N=(70,120),  P=(30,70),   K=(50,100),  temp=(18,30), humidity=(55,75), rainfall=(400,800), ndvi=(0.45,0.85)),
        "cotton":  dict(N=(100,150), P=(50,80),   K=(50,100),  temp=(25,38), humidity=(50,70), rainfall=(500,700), ndvi=(0.3,0.7)),
        "sugarcane":dict(N=(100,180),P=(50,100),  K=(100,200), temp=(20,35), humidity=(60,80), rainfall=(700,1200),ndvi=(0.55,0.9)),
        "soybean": dict(N=(20,60),   P=(50,100),  K=(60,120),  temp=(20,30), humidity=(55,75), rainfall=(400,700), ndvi=(0.4,0.8)),
    }

    records = []
    for crop, params in crops.items():
        for _ in range(n_samples // len(crops)):
            records.append({
                "N":          np.random.uniform(*params["N"]),
                "P":          np.random.uniform(*params["P"]),
                "K":          np.random.uniform(*params["K"]),
                "temperature":np.random.uniform(*params["temp"]),
                "humidity":   np.random.uniform(*params["humidity"]),
                "rainfall":   np.random.uniform(*params["rainfall"]),
                "ndvi":       np.random.uniform(*params["ndvi"]),
                "label":      crop,
            })
    return pd.DataFrame(records)


def train_and_save():
    print("📊 Generating training data...")
    df = generate_synthetic_data(3000)

    X = df[["N", "P", "K", "temperature", "humidity", "rainfall", "ndvi"]]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("🌲 Training RandomForestClassifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    print("\n📈 Classification Report:")
    print(classification_report(y_test, model.predict(X_test)))

    joblib.dump(model, MODEL_PATH)
    print(f"\n✅ Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    train_and_save()