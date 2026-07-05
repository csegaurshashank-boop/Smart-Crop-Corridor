# 🌾 Smart Crop Corridor System

A full-stack AI-powered platform for smart agriculture — helping farmers monitor fields, detect crop diseases, analyze pests using YOLO, and get personalized farming recommendations.

---

## 🚀 Features

- 🗺️ **Field Management** — Draw and manage agricultural fields on an interactive map
- 🤖 **AI Pest Detection** — YOLO-based image analysis for real-time pest & disease detection
- 📊 **Crop Recommendations** — Season-aware, soil-type-based crop guidance
- 🌐 **NDVI Analysis** — Satellite imagery integration via Copernicus Data Space
- 💧 **Irrigation Insights** — Smart irrigation scheduling based on field data
- 🚨 **Alert System** — Automated alerts for pest outbreaks and crop risks
- 🌏 **Multilingual Support** — Hindi & English UI (i18n)
- 🔐 **JWT Authentication** — Secure login/register for farmers and managers

---

## 🛠️ Tech Stack

### Backend
| Tool | Purpose |
|------|---------|
| **FastAPI** | REST API framework |
| **YOLOv8** | Pest & disease image detection |
| **scikit-learn** | Crop prediction ML model |
| **Python 3.10+** | Core language |

### Frontend
| Tool | Purpose |
|------|---------|
| **React + Vite** | UI framework |
| **Tailwind CSS** | Styling |
| **Leaflet.js** | Interactive maps |
| **i18next** | Multilingual support |

---

## 📁 Project Structure

```
crop-corridor-system/
├── app/                        # FastAPI backend
│   ├── core/                   # Config, security, dependencies
│   ├── ml/                     # YOLO model & prediction service
│   ├── models/                 # SQLAlchemy DB models
│   ├── routes/                 # API route handlers
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic services
│   └── main.py                 # App entry point
├── crop-frontend/              # React frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Page-level components
│   │   ├── services/           # API call helpers
│   │   ├── i18n/               # Language files (en/hi)
│   │   └── context/            # Auth context
│   └── vite.config.js
├── download_yolo_model.py      # Script to download YOLO weights
├── requirements.txt            # Python dependencies
└── .env.example                # Environment variable template
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

---

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/csegaurshashank-boop/Smart-Crop-Corridor.git
cd Smart-Crop-Corridor
```

---

### 2️⃣ Backend Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your credentials
```

#### Download YOLO Model
```bash
python download_yolo_model.py
```

#### Run Backend Server
```bash
uvicorn app.main:app --reload
```
> API will be live at: `http://localhost:8000`  
> Swagger Docs: `http://localhost:8000/docs`

---

### 3️⃣ Frontend Setup

```bash
cd crop-frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```
> Frontend will be live at: `http://localhost:5173`

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
DATABASE_URL=sqlite:///./crop_corridor.db
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Copernicus Data Space (for NDVI/Satellite)
CDSE_CLIENT_ID=your_client_id
CDSE_CLIENT_SECRET=your_client_secret
```

---

## 🤖 ML Models

> ⚠️ **Model files are NOT included in this repository** (large binary files).

| Model | File | Purpose |
|-------|------|---------|
| YOLOv8 | `app/ml/crop_disease.pt` | Pest & disease detection |
| Crop Predictor | `app/ml/crop_model.pkl` | Crop recommendation |

Run `python download_yolo_model.py` to auto-download the YOLO weights.

---

## 📸 Screenshots

> _Coming soon_

---

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">
  Made with ❤️ for Indian Farmers 🇮🇳
</div>
