from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.models import HealthOut
from app.routers import changes


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="GxP Change Control API",
    description=(
        "Portfolio-safe change control prototype. Synthetic data only. "
        "Not validated software — not for regulated decisions."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(changes.router)


@app.get("/health", response_model=HealthOut)
def health():
    return HealthOut(
        status="ok",
        service="gxp-change-control",
        data_classification="synthetic-portfolio-only",
        version="0.1.0",
    )
