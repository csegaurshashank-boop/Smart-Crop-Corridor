"""
download_yolo_model.py

Run this ONCE from the project root to download a pre-trained
plant disease YOLOv8 model.

Usage:
    python download_yolo_model.py

It will save:
    app/ml/crop_disease.pt
"""

import os
import urllib.request
import sys
from pathlib import Path

# ── Target path ───────────────────────────────────────────────────────────────
TARGET = Path("app/ml/crop_disease.pt")
TARGET.parent.mkdir(parents=True, exist_ok=True)

# ── Model source ──────────────────────────────────────────────────────────────
# YOLOv8n base weights from Ultralytics official release
# (38-class PlantVillage fine-tuned weights require Roboflow or Kaggle — see below)
BASE_MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt"


def download_with_progress(url: str, dest: Path):
    print(f"Downloading: {url}")
    print(f"Saving to  : {dest}")

    def reporthook(count, block_size, total_size):
        pct = int(count * block_size * 100 / max(total_size, 1))
        bar = "█" * (pct // 4) + "░" * (25 - pct // 4)
        print(f"\r  [{bar}] {pct}%", end="", flush=True)

    urllib.request.urlretrieve(url, dest, reporthook)
    print("\n✅ Download complete!\n")


if __name__ == "__main__":

    if TARGET.exists():
        size_mb = TARGET.stat().st_size / 1024 / 1024
        print(f"✅ Model already exists at {TARGET} ({size_mb:.1f} MB)")
        print("   Delete it and re-run this script to re-download.")
        sys.exit(0)

    print("=" * 60)
    print("  YOLO Plant Disease Model Downloader")
    print("=" * 60)
    print()

    # ── Option A: download official yolov8n base weights ─────────────────────
    # This is the official ultralytics nano model.
    # It detects objects in general (not specifically plant diseases).
    # For plant disease detection you ALSO need either:
    #   Option B — Roboflow fine-tuned model (recommended)
    #   Option C — Train on PlantVillage dataset (best accuracy)

    download_with_progress(BASE_MODEL_URL, TARGET)

    # ── Verify ────────────────────────────────────────────────────────────────
    size_mb = TARGET.stat().st_size / 1024 / 1024
    print(f"  File size : {size_mb:.1f} MB")

    if size_mb < 1:
        print("❌ File seems too small — download may have failed.")
        TARGET.unlink()
        sys.exit(1)

    print(f"  Saved at  : {TARGET}")
    print()
    print("=" * 60)
    print("  IMPORTANT: This is the BASE yolov8n model.")
    print("  For REAL plant disease detection, get a fine-tuned model:")
    print()
    print("  Option 1 (Recommended — Free):")
    print("    → https://universe.roboflow.com/")
    print("    → Search: 'Plant Disease'")
    print("    → Download YOLOv8 model → rename to crop_disease.pt")
    print("    → Place at: app/ml/crop_disease.pt")
    print()
    print("  Option 2 (Kaggle):")
    print("    → https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset")
    print("    → Use a community notebook that exports YOLOv8 weights")
    print()
    print("  Option 3 (Quick test — simulate with base model):")
    print("    → The base model + simulation fallback already works!")
    print("    → Restart server and test the Pest Detection page.")
    print("=" * 60)

    # ── Quick verify the model loads ──────────────────────────────────────────
    print("\nVerifying model loads correctly...")
    try:
        from ultralytics import YOLO
        model = YOLO(str(TARGET))
        print(f"✅ Model loaded successfully!")
        print(f"   Task  : {model.task}")
        print(f"   Names : {list(model.names.values())[:5]} ...")
        print()
        print("🚀 Ready! Restart the FastAPI server:")
        print("   venv\\Scripts\\uvicorn app.main:app --reload")
        print("   Look for: [yolo_pest] ✅ YOLO model loaded ...")
    except Exception as e:
        print(f"⚠  Load test failed: {e}")
        print("   The model file may be corrupt. Try downloading again.")
