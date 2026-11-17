"""
Entry point. Start-up order:
1. make sure PostGIS exists and tables are created
2. create the first admin user from .env
3. plug every router into the app under /api
"""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

import app.models  # noqa: F401  (registers all tables)
from app.api import auth, datasets, locations, traffic, videos
from app.core.config import settings
from app.core.security import hash_password
from app.database.session import Base, SessionLocal, engine, get_db
from app.models import User


@asynccontextmanager
async def lifespan(_: FastAPI):
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == settings.ADMIN_USERNAME).first():
            db.add(User(username=settings.ADMIN_USERNAME,
                        hashed_password=hash_password(settings.ADMIN_PASSWORD), role="admin"))
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origin_list,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

for r in (auth.router, locations.router, datasets.router, videos.router, traffic.router):
    app.include_router(r, prefix="/api")


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    postgis = db.execute(text("SELECT postgis_version()")).scalar()
    return {"status": "ok", "database": "connected", "postgis": postgis}
