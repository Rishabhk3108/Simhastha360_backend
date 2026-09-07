from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.user import ROLE_ADMIN, User
from app.routers import (
    ai,
    auth,
    facilities,
    family,
    field_team,
    health_card,
    incidents,
    ivr,
    reports,
    tasks,
    volunteers,
    zones,
)


def _bootstrap_admin() -> None:
    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.phone == settings.admin_bootstrap_phone).first()
        if not exists:
            admin = User(
                name="Command Centre Admin",
                phone=settings.admin_bootstrap_phone,
                password_hash=hash_password(settings.admin_bootstrap_password),
                role=ROLE_ADMIN,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _bootstrap_admin()
    yield


app = FastAPI(title="Simhastha 360 API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(facilities.router)
app.include_router(zones.router)
app.include_router(reports.router)
app.include_router(incidents.router)
app.include_router(volunteers.router)
app.include_router(tasks.router)
app.include_router(field_team.router)
app.include_router(family.router)
app.include_router(health_card.router)
app.include_router(ai.router)
app.include_router(ivr.router)


@app.get("/health")
def health():
    return {"status": "ok"}
