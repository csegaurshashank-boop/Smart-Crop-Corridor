# YOLO Crop Disease Model — Setup Guide

## Where to place the model

```
app/ml/crop_disease.pt      ← PUT YOUR YOLO WEIGHTS HERE
```

## Option 1 — Use a Pre-trained Public Model (Easiest)

### Roboflow PlantVillage YOLO Model (Free)
1. Go to: https://roboflow.com/models
2. Search: "Plant Disease"
3. Download a YOLOv8 model → Export as `.pt`
4. Rename to `crop_disease.pt` and place in this folder

### OR: Download via Python (38-class PlantVillage)
```python
# Run once from your project root:
from ultralytics import YOLO
model = YOLO("yolov8n.pt")   # downloads base model automatically
# Then fine-tune on plant disease dataset
```

---

## Option 2 — Train Your Own (Recommended for Production)

```
app/ml/
  crop_disease_dataset/
    images/
      train/   ← training images
      val/     ← validation images
    labels/
      train/   ← YOLO format .txt labels
      val/
    data.yaml  ← dataset config
```

### data.yaml format:
```yaml
train: images/train
val:   images/val
nc:    38           # number of classes
names:
  0: apple_scab
  1: apple_black_rot
  # ... (match DISEASE_MAP in yolo_pest_service.py)
```

### Training command:
```bash
cd crop-corridor-system
python -c "
from ultralytics import YOLO
model = YOLO('yolov8s.pt')
model.train(data='app/ml/crop_disease_dataset/data.yaml', epochs=50, imgsz=640)
model.export()
"
# Trained weights will be at: runs/detect/train/weights/best.pt
# Copy to: app/ml/crop_disease.pt
```

---

## Option 3 — Fastest: Download PlantDoc Pre-trained Weights

```bash
# In your terminal (from project root):
pip install gdown
python -c "
import gdown
# PlantDoc YOLOv8n fine-tuned (community model)
gdown.download('https://drive.google.com/uc?id=YOUR_MODEL_ID', 'app/ml/crop_disease.pt')
"
```

---

## Class Map

The `yolo_pest_service.py` DISEASE_MAP covers 38 PlantVillage classes (indices 0–37):

| Index | Disease |
|-------|---------|
| 0  | Apple Scab |
| 1  | Apple Black Rot |
| 3  | Apple Healthy |
| 7  | Corn Grey Leaf Spot |
| 9  | Corn Northern Leaf Blight |
| 20 | Potato Early Blight |
| 21 | Potato Late Blight |
| 28 | Tomato Bacterial Spot |
| 30 | Tomato Late Blight |
| 35 | Tomato Yellow Leaf Curl Virus |
| 37 | Tomato Healthy |
| ... | (full list in yolo_pest_service.py) |

**If your model uses different class indices → update `DISEASE_MAP` in `yolo_pest_service.py`.**

---

## Without the model file

If `crop_disease.pt` is NOT present:
- The system automatically uses the **hash-seeded simulation fallback**
- The API works normally — no crashes
- Frontend shows realistic results
- Server logs: `[yolo_pest] Model not found — using simulation fallback.`

---

## After placing the model

Restart the FastAPI server:
```bash
uvicorn app.main:app --reload
```

Server log on success:
```
[yolo_pest] ✅ YOLO model loaded from app/ml/crop_disease.pt
```
