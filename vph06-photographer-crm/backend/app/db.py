import os
from pathlib import Path

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def _database_url() -> str:
    database_host = os.getenv("DATABASE_HOST")
    if not database_host:
        return os.getenv("DATABASE_URL", "sqlite:///./photo_vph06.db")

    password_file = Path(os.environ["DATABASE_PASSWORD_FILE"])
    password = password_file.read_text(encoding="utf-8").strip()
    return URL.create(
        "postgresql+psycopg",
        username=os.environ["DATABASE_USER"],
        password=password,
        host=database_host,
        port=int(os.getenv("DATABASE_PORT", "5432")),
        database=os.environ["DATABASE_NAME"],
    ).render_as_string(hide_password=False)


engine = create_engine(_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
