from fastapi import FastAPI  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from contextlib import asynccontextmanager

from app.database import connect_db, close_db  # type: ignore
from app.routes import auth, users, fields, corridors, analysis, alerts, map, visualization, recommendations, pest_analysis, pest_detection  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="🌾 Crop Corridor Precision Agriculture System",
    description="Satellite-powered crop monitoring and AI-driven field management platform.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(fields.router)
app.include_router(corridors.router)
app.include_router(analysis.router)
app.include_router(alerts.router)
app.include_router(map.router)
app.include_router(visualization.router)
app.include_router(recommendations.router)
app.include_router(pest_analysis.router)
app.include_router(pest_detection.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "✅ API is running",
        "project": "Crop Corridor Precision Agriculture System",
        "docs": "/docs",
    }