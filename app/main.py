from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import init_db
from app.models import ErrorDetail, HealthOut, ValidationErrorBody
from app.routers import changes, meta, schemas


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="GxP Change Control API",
    description=(
        "Portfolio-safe change control prototype. Synthetic data only. "
        "Not validated software — not for regulated decisions.\n\n"
        "**Validation:** Pydantic v2; JSON Schema at `/schemas`; "
        "**timezone policy** at `/meta/timezone-policy` (aware ISO required, storage UTC). "
        "Invalid input → HTTP **422**."
    ),
    version="0.1.3",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def pydantic_validation_handler(_: Request, exc: RequestValidationError):
    details: list[ErrorDetail] = []
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", ())]
        details.append(
            ErrorDetail(
                loc=loc,
                msg=err.get("msg", "Validation error"),
                type=err.get("type", "value_error"),
            )
        )
    body = ValidationErrorBody(details=details)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=body.model_dump(),
    )


app.include_router(changes.router)
app.include_router(schemas.router)
app.include_router(meta.router)


@app.get("/health", response_model=HealthOut)
def health():
    return HealthOut(
        status="ok",
        service="gxp-change-control",
        data_classification="synthetic-portfolio-only",
        version="0.1.3",
    )
