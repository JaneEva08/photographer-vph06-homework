import asyncio
import json
import logging
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models
from .db import Base, SessionLocal, engine, get_db
from .migrations import run_migrations
from .security import (
    authenticate,
    bootstrap_ready,
    cookie_is_secure,
    create_access_token,
    get_current_admin,
    hash_password,
    matches_bootstrap_token,
)
from .sheets_sync import is_configured as sheets_is_configured
from .sheets_sync import retry_errors as retry_sheet_errors
from .sheets_sync import sync_one_pending, sync_reports


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
Base.metadata.create_all(bind=engine)
run_migrations(engine)

app = FastAPI(
    title="Photographer Website API",
    version="0.2.0",
    description="Website, CRM, admin and aggregated metrics for a photographer in Germany.",
)
BERLIN = ZoneInfo("Europe/Berlin")
SHOOT_STATUSES = {"planned", "in_progress", "completed", "cancelled"}
TASK_STATUSES = {"open", "in_progress", "done", "cancelled"}
APPLICATION_STATUSES = {"new", "contacted", "proposal_sent", "confirmed", "completed", "cancelled"}


class ServiceFields(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    category: str = Field(default="Other", min_length=2, max_length=60)
    name_en: str | None = Field(default=None, max_length=120)
    name_ru: str | None = Field(default=None, max_length=120)
    description_en: str | None = Field(default=None, max_length=2000)
    description_ru: str | None = Field(default=None, max_length=2000)
    min_price_eur: Decimal = Field(ge=0, max_digits=9, decimal_places=2)
    max_price_eur: Decimal = Field(ge=0, max_digits=9, decimal_places=2)
    active: bool = True

    @model_validator(mode="after")
    def validate_price_range(self):
        if self.max_price_eur < self.min_price_eur:
            raise ValueError("max_price_eur must be greater than or equal to min_price_eur")
        return self


class ServiceCreate(ServiceFields):
    pass


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, min_length=2, max_length=60)
    name_en: str | None = Field(default=None, max_length=120)
    name_ru: str | None = Field(default=None, max_length=120)
    description_en: str | None = Field(default=None, max_length=2000)
    description_ru: str | None = Field(default=None, max_length=2000)
    min_price_eur: Decimal | None = Field(default=None, ge=0, max_digits=9, decimal_places=2)
    max_price_eur: Decimal | None = Field(default=None, ge=0, max_digits=9, decimal_places=2)
    active: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_values(cls, values):
        nullable = {"name_en", "name_ru", "description_en", "description_ru"}
        if isinstance(values, dict):
            for key, value in values.items():
                if value is None and key not in nullable:
                    raise ValueError(f"{key} cannot be null")
        return values

    @model_validator(mode="after")
    def validate_price_range(self):
        if self.min_price_eur is not None and self.max_price_eur is not None:
            if self.max_price_eur < self.min_price_eur:
                raise ValueError("max_price_eur must be greater than or equal to min_price_eur")
        return self


class ServiceRead(ServiceFields):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class ApplicationCreate(BaseModel):
    service_id: int = Field(gt=0)
    full_name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    phone: str | None = Field(default=None, max_length=48)
    budget_eur: Decimal = Field(gt=0, max_digits=9, decimal_places=2)
    preferred_date: date | None = None
    message: str = Field(default="", max_length=4000)
    contact_consent: bool
    language: Literal["de", "en", "ru"] = "de"
    location: str | None = Field(default=None, max_length=180)
    person_type: str | None = Field(default=None, max_length=40)
    preferred_contact: str | None = Field(default=None, max_length=30)
    reference_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_contact_consent(self):
        if not self.contact_consent:
            raise ValueError("contact_consent must be true")
        return self


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    service_id: int
    service_name: str
    category: str
    full_name: str
    email: str
    phone: str | None
    budget_eur: Decimal
    preferred_date: date | None
    message: str
    contact_consent: bool
    contact_consent_at: datetime | None
    status: str
    language: str
    location: str | None
    person_type: str | None
    preferred_contact: str | None
    reference_url: str | None
    priority_score: int
    priority_label: str
    priority_reasons: list[str]
    client_id: int | None
    created_at: datetime

    @classmethod
    def from_row(cls, row: models.Application):
        values = {field: getattr(row, field) for field in cls.model_fields if hasattr(row, field)}
        values["service_name"] = row.service.name if row.service else ""
        values["category"] = row.service.category if row.service else "Other"
        values["priority_reasons"] = json.loads(row.priority_reasons or "[]")
        return cls.model_validate(values)


class AdminRegister(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=12, max_length=200)
    bootstrap_token: str = Field(min_length=32, max_length=200)


class ApplicationUpdate(BaseModel):
    status: str

    @model_validator(mode="after")
    def validate_status(self):
        if self.status not in APPLICATION_STATUSES:
            raise ValueError("Unsupported application status")
        return self


class BehaviorMetricCreate(BaseModel):
    session_id: str = Field(min_length=16, max_length=64)
    event_key: str = Field(min_length=16, max_length=64)
    event_name: Literal["page_view", "cursor", "heartbeat", "page_end", "form_start", "form_submit", "service_view"]
    page_path: str = Field(default="/", max_length=160)
    x_bucket: int | None = Field(default=None, ge=0, le=19)
    y_bucket: int | None = Field(default=None, ge=0, le=11)
    analytics_consent: bool

    @model_validator(mode="after")
    def require_analytics_consent(self):
        if not self.analytics_consent:
            raise ValueError("Analytics consent is required for behavior metrics")
        if self.event_name == "cursor" and (self.x_bucket is None or self.y_bucket is None):
            raise ValueError("Cursor events require coarse coordinate buckets")
        return self


class AnalyticsWithdraw(BaseModel):
    session_id: str = Field(min_length=16, max_length=64)


class TaskCreate(BaseModel):
    client_id: int = Field(gt=0)
    shoot_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=2, max_length=180)
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    due_date: date | None = None
    status: str | None = None

    @model_validator(mode="after")
    def validate_patch(self):
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        if self.status is not None and self.status not in TASK_STATUSES:
            raise ValueError("Unsupported task status")
        return self


class PaymentCreate(BaseModel):
    amount_eur: Decimal = Field(gt=0, max_digits=9, decimal_places=2)
    kind: Literal["deposit", "final", "refund"]
    paid_on: date
    note: str = Field(default="", max_length=300)


class PaymentUpdate(BaseModel):
    amount_eur: Decimal | None = Field(default=None, gt=0, max_digits=9, decimal_places=2)
    kind: Literal["deposit", "final", "refund"] | None = None
    paid_on: date | None = None
    note: str | None = Field(default=None, max_length=300)


class ShootUpdate(BaseModel):
    package_name: str | None = Field(default=None, max_length=120)
    shoot_date: date | None = None
    duration_hours: Decimal | None = Field(default=None, gt=0, max_digits=5, decimal_places=2)
    status: Literal["planned", "in_progress", "completed", "cancelled"] | None = None
    contract_amount_eur: Decimal | None = Field(default=None, ge=0, max_digits=9, decimal_places=2)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    shoot_id: int
    amount_eur: Decimal
    kind: str
    paid_on: date
    note: str


class DemoSeedResult(BaseModel):
    created: int
    priorities: dict[str, int]


def enqueue_sheet_sync(db: Session, entity_type: str, entity_id: int) -> None:
    db.add(models.SheetsOutbox(entity_type=entity_type, entity_id=entity_id))


def _lead_score(payload: ApplicationCreate, service: models.Service) -> tuple[int, str, list[str]]:
    score = 0
    reasons: list[str] = []
    today = datetime.now(BERLIN).date()
    if payload.preferred_date:
        days = (payload.preferred_date - today).days
        if 0 <= days <= 21:
            score += 30
            reasons.append("Wunschtermin liegt innerhalb von drei Wochen (+30)")
        elif 22 <= days <= 90:
            score += 20
            reasons.append("Wunschtermin liegt innerhalb von drei Monaten (+20)")
        elif 91 <= days <= 180:
            score += 10
            reasons.append("Wunschtermin liegt innerhalb von sechs Monaten (+10)")
        else:
            reasons.append("Wunschtermin liegt weiter in der Zukunft (+0)")

    midpoint = (service.min_price_eur + service.max_price_eur) / Decimal("2")
    if payload.budget_eur >= service.max_price_eur * Decimal("0.9"):
        score += 25
        reasons.append("Budget liegt nahe am oberen Rand der Leistungsspanne (+25)")
    elif payload.budget_eur >= midpoint:
        score += 15
        reasons.append("Budget liegt mindestens in der Mitte der Leistungsspanne (+15)")
    else:
        score += 5
        reasons.append("Budget liegt innerhalb der gewählten Leistungsspanne (+5)")

    if len(payload.message.strip()) >= 100:
        score += 20
        reasons.append("Ausführliches Briefing (+20)")
    elif len(payload.message.strip()) >= 40:
        score += 10
        reasons.append("Briefing enthält hilfreiche Details (+10)")
    else:
        reasons.append("Briefing ist kurz oder leer (+0)")

    if payload.location:
        score += 5
        reasons.append("Ort/Region angegeben (+5)")
    if payload.reference_url:
        score += 10
        reasons.append("Referenzlink angegeben (+10)")
    if payload.phone:
        score += 5
        reasons.append("Telefonnummer angegeben (+5)")

    label = "hot" if score >= 60 else "warm" if score >= 35 else "cold"
    return score, label, reasons


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/auth/registration-status", tags=["authentication"])
def registration_status(db: Session = Depends(get_db)) -> dict[str, bool]:
    return {"enabled": db.scalar(select(models.Admin.id).limit(1)) is None and bootstrap_ready()}


@app.post("/auth/register", status_code=201, tags=["authentication"])
def register_admin(payload: AdminRegister, db: Session = Depends(get_db)) -> dict[str, str]:
    if not matches_bootstrap_token(payload.bootstrap_token):
        raise HTTPException(status_code=403, detail="Invalid or unavailable setup token")
    try:
        with db.begin():
            if engine.dialect.name == "postgresql":
                db.execute(text("SELECT pg_advisory_xact_lock(91452231)"))
            if db.scalar(select(models.Admin.id).limit(1)) is not None:
                raise HTTPException(status_code=409, detail="Admin registration is closed")
            admin = models.Admin(username=payload.username, password_hash=hash_password(payload.password))
            db.add(admin)
            db.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Admin could not be created") from exc
    logging.info("Initial administrator registered")
    return {"status": "registered"}


@app.post("/auth/token", tags=["authentication"])
def login(
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    admin = authenticate(db, form.username, form.password)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(admin.username)
    response.set_cookie(
        "photographer_admin_session",
        token,
        httponly=True,
        secure=cookie_is_secure(),
        samesite="strict",
        max_age=30 * 60,
        path="/",
    )
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/logout", tags=["authentication"])
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie("photographer_admin_session", path="/")
    return {"status": "logged out"}


@app.get("/auth/me", tags=["authentication"])
def current_admin(admin: models.Admin = Depends(get_current_admin)) -> dict[str, str]:
    return {"username": admin.username}


@app.get("/services", response_model=list[ServiceRead], tags=["services"])
def list_services(db: Session = Depends(get_db)) -> list[models.Service]:
    statement = select(models.Service).where(models.Service.active.is_(True)).order_by(models.Service.category, models.Service.id)
    return db.scalars(statement).all()


@app.get("/admin/services", response_model=list[ServiceRead], tags=["admin services"])
def list_all_services(
    db: Session = Depends(get_db), admin: models.Admin = Depends(get_current_admin)
) -> list[models.Service]:
    return db.scalars(select(models.Service).order_by(models.Service.category, models.Service.id)).all()


@app.post("/admin/services", response_model=ServiceRead, status_code=201, tags=["admin services"])
def create_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> models.Service:
    row = models.Service(**payload.model_dump())
    db.add(row)
    try:
        db.flush()
        enqueue_sheet_sync(db, "service", row.id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Service with this name already exists") from exc
    db.refresh(row)
    logging.info("Created service id=%s", row.id)
    return row


@app.patch("/admin/services/{service_id}", response_model=ServiceRead, tags=["admin services"])
def update_service(
    service_id: int,
    payload: ServiceUpdate,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> models.Service:
    row = db.get(models.Service, service_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Service not found")
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="At least one field is required")
    min_price = updates.get("min_price_eur", row.min_price_eur)
    max_price = updates.get("max_price_eur", row.max_price_eur)
    if max_price < min_price:
        raise HTTPException(status_code=422, detail="max_price_eur must be greater than or equal to min_price_eur")
    for field, value in updates.items():
        setattr(row, field, value)
    try:
        db.flush()
        enqueue_sheet_sync(db, "service", row.id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Service with this name already exists") from exc
    db.refresh(row)
    return row


@app.delete("/admin/services/{service_id}", status_code=204, tags=["admin services"])
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> Response:
    row = db.get(models.Service, service_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Service not found")
    # Keep historical references stable; inactive offers disappear from the public catalogue.
    row.active = False
    db.flush()
    enqueue_sheet_sync(db, "service", row.id)
    db.commit()
    return Response(status_code=204)


@app.post("/applications", response_model=ApplicationRead, status_code=201, tags=["applications"])
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)) -> ApplicationRead:
    service = db.get(models.Service, payload.service_id)
    if service is None or not service.active:
        raise HTTPException(status_code=404, detail="Service not found or unavailable")
    if not service.min_price_eur <= payload.budget_eur <= service.max_price_eur:
        raise HTTPException(status_code=422, detail="Budget must be within the selected service price range")

    client = db.scalar(select(models.Client).where(models.Client.email == payload.email))
    if client is None:
        client = models.Client(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            language=payload.language,
        )
        db.add(client)
        db.flush()
        enqueue_sheet_sync(db, "client", client.id)

    score, label, reasons = _lead_score(payload, service)
    row = models.Application(
        **payload.model_dump(),
        client_id=client.id,
        contact_consent_at=datetime.now(timezone.utc),
        priority_score=score,
        priority_label=label,
        priority_reasons=json.dumps(reasons, ensure_ascii=False),
    )
    db.add(row)
    db.flush()
    enqueue_sheet_sync(db, "application", row.id)
    db.commit()
    db.refresh(row)
    logging.info("Created application id=%s priority=%s", row.id, label)
    return ApplicationRead.from_row(row)


@app.get("/admin/applications", response_model=list[ApplicationRead], tags=["admin applications"])
def list_applications(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> list[ApplicationRead]:
    statement = select(models.Application).order_by(models.Application.priority_score.desc(), models.Application.id.desc()).limit(limit)
    return [ApplicationRead.from_row(row) for row in db.scalars(statement).all()]


@app.post("/admin/demo/seed-priorities", response_model=DemoSeedResult, tags=["admin applications"])
def seed_priority_demo(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> DemoSeedResult:
    """Create the homework's synthetic 4/3/3 lead set through the real scorer."""
    marker = "VPh06 synthetic priority demo"
    existing = db.scalar(select(func.count()).select_from(models.Application).where(models.Application.message.like(f"{marker}%"))) or 0
    if existing:
        raise HTTPException(status_code=409, detail="Synthetic priority demo already exists")
    service = next(
        (row for row in db.scalars(select(models.Service).where(models.Service.active.is_(True)).order_by(models.Service.id)).all()
         if row.max_price_eur - row.min_price_eur >= Decimal("0.10")),
        None,
    )
    if service is None:
        raise HTTPException(status_code=409, detail="Create at least one active service first")

    cases: list[tuple[str, Decimal, date, str, str | None, str | None]] = []
    midpoint = (service.max_price_eur + service.min_price_eur) / Decimal("2")
    for index in range(4):
        cases.append((f"Demo Hot {index + 1}", service.max_price_eur, datetime.now(BERLIN).date() + timedelta(days=7 + index),
                      f"{marker} hot {index + 1}. Detailed synthetic enquiry with schedule, location and references.", "Berlin", "https://example.invalid/reference"))
    for index in range(3):
        cases.append((f"Demo Warm {index + 1}", min(service.max_price_eur, midpoint + Decimal("0.01")), datetime.now(BERLIN).date() + timedelta(days=45 + index),
                      f"{marker} warm {index + 1}.", None, None))
    for index in range(3):
        cases.append((f"Demo Cold {index + 1}", max(service.min_price_eur, Decimal("0.01")), datetime.now(BERLIN).date() + timedelta(days=220 + index),
                      f"{marker} cold {index + 1}.", None, None))

    counts = {"hot": 0, "warm": 0, "cold": 0}
    for index, (name, budget, requested_date, message, location, reference) in enumerate(cases):
        budget = budget.quantize(Decimal("0.01"))
        payload = ApplicationCreate(
            service_id=service.id,
            full_name=name,
            email=f"vph06-demo-{index + 1}@example.invalid",
            budget_eur=budget,
            preferred_date=requested_date,
            message=message,
            contact_consent=True,
            language="de",
            location=location,
            reference_url=reference,
        )
        score, label, reasons = _lead_score(payload, service)
        client = models.Client(full_name=name, email=payload.email, language="de")
        db.add(client)
        db.flush()
        row = models.Application(
            **payload.model_dump(), client_id=client.id, priority_score=score, priority_label=label,
            contact_consent_at=datetime.now(timezone.utc),
            priority_reasons=json.dumps(reasons, ensure_ascii=False),
        )
        db.add(row)
        db.flush()
        enqueue_sheet_sync(db, "client", client.id)
        enqueue_sheet_sync(db, "application", row.id)
        counts[label] += 1
    db.commit()
    return DemoSeedResult(created=sum(counts.values()), priorities=counts)


@app.get("/admin/applications/{application_id}", response_model=ApplicationRead, tags=["admin applications"])
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> ApplicationRead:
    row = db.get(models.Application, application_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationRead.from_row(row)


@app.patch("/admin/applications/{application_id}", response_model=ApplicationRead, tags=["admin applications"])
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> ApplicationRead:
    row = db.get(models.Application, application_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    row.status = payload.status
    if payload.status == "confirmed":
        client = db.get(models.Client, row.client_id) if row.client_id else None
        service = db.get(models.Service, row.service_id)
        if client is None:
            client = models.Client(full_name=row.full_name, email=row.email, phone=row.phone, language=row.language)
            db.add(client)
            db.flush()
            row.client_id = client.id
            enqueue_sheet_sync(db, "client", client.id)
        shoot = db.scalar(select(models.Shoot).where(models.Shoot.application_id == row.id))
        if shoot is None:
            shoot = models.Shoot(
                client_id=client.id,
                application_id=row.id,
                category=service.category if service else "Other",
                package_name=service.name if service else "",
                shoot_date=row.preferred_date,
                status="planned",
                # A customer's budget is not the photographer's agreed contract price.
                contract_amount_eur=Decimal("0.00"),
            )
            db.add(shoot)
            db.flush()
            enqueue_sheet_sync(db, "shoot", shoot.id)
    db.flush()
    enqueue_sheet_sync(db, "application", row.id)
    db.commit()
    db.refresh(row)
    return ApplicationRead.from_row(row)


@app.get("/admin/clients", tags=["CRM"])
def list_clients(
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> list[dict]:
    rows = db.scalars(select(models.Client).order_by(models.Client.created_at.desc()).limit(limit)).all()
    return [
        {"id": row.id, "full_name": row.full_name, "email": row.email, "phone": row.phone, "language": row.language, "created_at": row.created_at}
        for row in rows
    ]


@app.get("/admin/shoots", tags=["CRM"])
def list_shoots(
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> list[dict]:
    rows = db.scalars(select(models.Shoot).order_by(models.Shoot.shoot_date, models.Shoot.id).limit(limit)).all()
    return [
        {"id": row.id, "client_id": row.client_id, "application_id": row.application_id, "category": row.category,
         "package_name": row.package_name, "shoot_date": row.shoot_date, "duration_hours": row.duration_hours,
         "status": row.status, "contract_amount_eur": row.contract_amount_eur}
        for row in rows
    ]


@app.patch("/admin/shoots/{shoot_id}", tags=["CRM"])
def update_shoot(
    shoot_id: int,
    payload: ShootUpdate,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> dict:
    row = db.get(models.Shoot, shoot_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Shoot not found")
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="At least one field is required")
    for field, value in updates.items():
        setattr(row, field, value)
    db.flush()
    enqueue_sheet_sync(db, "shoot", row.id)
    db.commit()
    return {"id": row.id, "client_id": row.client_id, "application_id": row.application_id, "category": row.category,
            "package_name": row.package_name, "shoot_date": row.shoot_date, "duration_hours": row.duration_hours,
            "status": row.status, "contract_amount_eur": row.contract_amount_eur}


@app.get("/admin/tasks", tags=["CRM"])
def list_tasks(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> list[dict]:
    rows = db.scalars(select(models.Task).order_by(models.Task.due_date, models.Task.id)).all()
    return [{"id": row.id, "client_id": row.client_id, "shoot_id": row.shoot_id, "title": row.title, "due_date": row.due_date, "status": row.status} for row in rows]


@app.post("/admin/tasks", status_code=201, tags=["CRM"])
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> dict:
    if db.get(models.Client, payload.client_id) is None:
        raise HTTPException(status_code=404, detail="Client not found")
    row = models.Task(**payload.model_dump())
    db.add(row)
    db.flush()
    enqueue_sheet_sync(db, "task", row.id)
    db.commit()
    return {"id": row.id, "client_id": row.client_id, "shoot_id": row.shoot_id, "title": row.title, "due_date": row.due_date, "status": row.status}


@app.patch("/admin/tasks/{task_id}", tags=["CRM"])
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> dict:
    row = db.get(models.Task, task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.flush()
    enqueue_sheet_sync(db, "task", row.id)
    db.commit()
    return {"id": row.id, "client_id": row.client_id, "shoot_id": row.shoot_id, "title": row.title, "due_date": row.due_date, "status": row.status}


@app.get("/admin/shoots/{shoot_id}/payments", response_model=list[PaymentRead], tags=["CRM"])
def list_payments(
    shoot_id: int,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> list[models.Payment]:
    if db.get(models.Shoot, shoot_id) is None:
        raise HTTPException(status_code=404, detail="Shoot not found")
    return db.scalars(select(models.Payment).where(models.Payment.shoot_id == shoot_id).order_by(models.Payment.paid_on)).all()


@app.post("/admin/shoots/{shoot_id}/payments", response_model=PaymentRead, status_code=201, tags=["CRM"])
def create_payment(
    shoot_id: int,
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> models.Payment:
    if db.get(models.Shoot, shoot_id) is None:
        raise HTTPException(status_code=404, detail="Shoot not found")
    row = models.Payment(shoot_id=shoot_id, **payload.model_dump())
    db.add(row)
    db.flush()
    enqueue_sheet_sync(db, "payment", row.id)
    db.commit()
    db.refresh(row)
    return row


@app.patch("/admin/payments/{payment_id}", response_model=PaymentRead, tags=["CRM"])
def update_payment(
    payment_id: int,
    payload: PaymentUpdate,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> models.Payment:
    row = db.get(models.Payment, payment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="At least one field is required")
    for field, value in updates.items():
        setattr(row, field, value)
    db.flush()
    enqueue_sheet_sync(db, "payment", row.id)
    db.commit()
    db.refresh(row)
    return row


@app.get("/admin/finance-summary", tags=["CRM"])
def finance_summary(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> dict:
    contracted = db.scalar(
        select(func.coalesce(func.sum(models.Shoot.contract_amount_eur), 0)).where(models.Shoot.status != "cancelled")
    ) or Decimal("0.00")
    payments = db.scalars(select(models.Payment)).all()
    received = sum(((-row.amount_eur if row.kind == "refund" else row.amount_eur) for row in payments), Decimal("0.00"))
    return {"contracted_eur": contracted, "received_eur": received, "outstanding_eur": contracted - received}


@app.post("/metrics", status_code=202, tags=["behavior metrics"])
def collect_metric(payload: BehaviorMetricCreate, db: Session = Depends(get_db)) -> dict[str, str]:
    row = models.BehaviorMetric(**payload.model_dump(exclude={"analytics_consent"}))
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"status": "duplicate ignored"}
    return {"status": "accepted"}


@app.post("/metrics/withdraw", status_code=200, tags=["behavior metrics"])
def withdraw_analytics(payload: AnalyticsWithdraw, db: Session = Depends(get_db)) -> dict[str, int]:
    result = db.execute(delete(models.BehaviorMetric).where(models.BehaviorMetric.session_id == payload.session_id))
    db.commit()
    return {"deleted": result.rowcount or 0}


@app.get("/admin/metrics", tags=["behavior metrics"])
def read_metrics(
    period: Literal["day", "week", "month"] = "day",
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> dict:
    now_local = datetime.now(BERLIN)
    if period == "day":
        start_local = datetime.combine(now_local.date(), time.min, tzinfo=BERLIN)
    elif period == "week":
        start_local = datetime.combine(now_local.date() - timedelta(days=now_local.weekday()), time.min, tzinfo=BERLIN)
    else:
        start_local = datetime.combine(now_local.date().replace(day=1), time.min, tzinfo=BERLIN)
    start_utc = start_local.astimezone(timezone.utc)
    rows = db.scalars(select(models.BehaviorMetric).where(models.BehaviorMetric.occurred_at >= start_utc)).all()

    sessions: dict[str, list[datetime]] = {}
    heat: dict[tuple[int, int], int] = {}
    events: dict[str, int] = {}
    for row in rows:
        sessions.setdefault(row.session_id, []).append(row.occurred_at)
        events[row.event_name] = events.get(row.event_name, 0) + 1
        if row.event_name == "cursor" and row.x_bucket is not None and row.y_bucket is not None:
            key = (row.x_bucket, row.y_bucket)
            heat[key] = heat.get(key, 0) + 1
    durations = [max(0, int((max(times) - min(times)).total_seconds())) for times in sessions.values() if times]
    return {
        "period": period,
        "sessions": len(sessions),
        "average_seconds": round(sum(durations) / len(durations)) if durations else 0,
        "events": events,
        "heatmap": [{"x": x, "y": y, "count": count} for (x, y), count in sorted(heat.items())],
    }


@app.get("/admin/sheets-status", tags=["Google Sheets"])
def sheets_status(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> dict:
    pending = db.scalar(select(func.count()).select_from(models.SheetsOutbox).where(models.SheetsOutbox.status.in_(["pending", "processing"]))) or 0
    failed = db.scalar(select(func.count()).select_from(models.SheetsOutbox).where(models.SheetsOutbox.status == "error")) or 0
    done = db.scalar(select(func.count()).select_from(models.SheetsOutbox).where(models.SheetsOutbox.status == "done")) or 0
    return {"enabled": sheets_is_configured(), "pending": pending, "errors": failed, "synced_events": done}


@app.post("/admin/sheets-sync/retry", tags=["Google Sheets"])
def retry_sheets_sync(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> dict[str, int]:
    count = retry_sheet_errors(db)
    db.commit()
    return {"queued": count}


@app.post("/admin/sheets-sync/bootstrap", tags=["Google Sheets"])
def bootstrap_sheets_sync(
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin),
) -> dict[str, int]:
    if not sheets_is_configured():
        raise HTTPException(status_code=503, detail="Google Sheets connector is not configured")
    count = 0
    for entity_type, model in (("service", models.Service), ("client", models.Client), ("application", models.Application),
                               ("shoot", models.Shoot), ("task", models.Task), ("payment", models.Payment)):
        for entity_id in db.scalars(select(model.id)):
            enqueue_sheet_sync(db, entity_type, entity_id)
            count += 1
    db.commit()
    return {"queued": count}


async def _sheets_worker() -> None:
    reports_dirty = False
    while True:
        try:
            if sheets_is_configured():
                worked = await asyncio.to_thread(sync_one_pending)
                if worked:
                    reports_dirty = True
                    continue
                if reports_dirty:
                    await asyncio.to_thread(sync_reports)
                    reports_dirty = False
        except Exception as exc:
            logging.warning("Sheets background worker error_type=%s", type(exc).__name__)
            await asyncio.sleep(15)
            continue
        await asyncio.sleep(15)


@app.on_event("startup")
async def start_sheets_worker() -> None:
    app.state.sheets_worker = asyncio.create_task(_sheets_worker())


@app.on_event("shutdown")
async def stop_sheets_worker() -> None:
    worker = getattr(app.state, "sheets_worker", None)
    if worker:
        worker.cancel()
        try:
            await worker
        except asyncio.CancelledError:
            pass
