from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Service(Base):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint("min_price_eur >= 0", name="ck_services_min_price_nonnegative"),
        CheckConstraint("max_price_eur >= min_price_eur", name="ck_services_price_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(60), default="Other", index=True)
    name_en: Mapped[str | None] = mapped_column(String(120), nullable=True)
    name_ru: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_price_eur: Mapped[Decimal] = mapped_column(Numeric(9, 2))
    max_price_eur: Mapped[Decimal] = mapped_column(Numeric(9, 2))
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    applications: Mapped[list["Application"]] = relationship(back_populates="service")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        CheckConstraint("budget_eur >= 0", name="ck_applications_budget_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="RESTRICT"), index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(254), index=True)
    phone: Mapped[str | None] = mapped_column(String(48))
    budget_eur: Mapped[Decimal] = mapped_column(Numeric(9, 2))
    preferred_date: Mapped[date | None] = mapped_column(Date)
    message: Mapped[str] = mapped_column(Text, default="")
    contact_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    contact_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="new", index=True)
    language: Mapped[str] = mapped_column(String(5), default="de")
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(180), nullable=True)
    person_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    preferred_contact: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reference_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    priority_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    priority_label: Mapped[str] = mapped_column(String(12), default="cold", index=True)
    priority_reasons: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    service: Mapped[Service] = relationship(back_populates="applications")
    client: Mapped["Client | None"] = relationship(back_populates="applications")


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(48), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="de")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    applications: Mapped[list["Application"]] = relationship(back_populates="client")
    shoots: Mapped[list["Shoot"]] = relationship(back_populates="client")


class Shoot(Base):
    __tablename__ = "shoots"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="RESTRICT"), index=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), unique=True, nullable=True)
    category: Mapped[str] = mapped_column(String(60), default="Other")
    package_name: Mapped[str] = mapped_column(String(120), default="")
    shoot_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    duration_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="planned", index=True)
    contract_amount_eur: Mapped[Decimal] = mapped_column(Numeric(9, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    client: Mapped[Client] = relationship(back_populates="shoots")
    tasks: Mapped[list["Task"]] = relationship(back_populates="shoot")
    payments: Mapped[list["Payment"]] = relationship(back_populates="shoot")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    shoot_id: Mapped[int | None] = mapped_column(ForeignKey("shoots.id", ondelete="CASCADE"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(180))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(24), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    shoot: Mapped["Shoot | None"] = relationship(back_populates="tasks")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    shoot_id: Mapped[int] = mapped_column(ForeignKey("shoots.id", ondelete="CASCADE"), index=True)
    amount_eur: Mapped[Decimal] = mapped_column(Numeric(9, 2))
    kind: Mapped[str] = mapped_column(String(16), default="payment")
    paid_on: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    note: Mapped[str] = mapped_column(String(300), default="")
    shoot: Mapped["Shoot"] = relationship(back_populates="payments")


class BehaviorMetric(Base):
    __tablename__ = "behavior_metrics"
    __table_args__ = (UniqueConstraint("session_id", "event_key", name="uq_behavior_session_event"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    event_key: Mapped[str] = mapped_column(String(64))
    event_name: Mapped[str] = mapped_column(String(40), index=True)
    page_path: Mapped[str] = mapped_column(String(160), default="/")
    x_bucket: Mapped[int | None] = mapped_column(Integer, nullable=True)
    y_bucket: Mapped[int | None] = mapped_column(Integer, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class SheetsOutbox(Base):
    __tablename__ = "sheets_outbox"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
