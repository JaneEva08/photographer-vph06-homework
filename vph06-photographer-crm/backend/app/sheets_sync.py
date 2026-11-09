import logging
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .db import SessionLocal


logger = logging.getLogger(__name__)
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
SHEETS: dict[str, tuple[str, list[str]]] = {
    # Keep direct identifiers and free text in PostgreSQL/admin only. Linked IDs
    # remain pseudonymous operational references, not anonymous data.
    "application": ("Leads", ["lead_id", "created_at", "language", "category", "service", "requested_date", "budget_eur", "status", "priority", "score", "score_reasons", "client_id"]),
    "service": ("Services", ["service_id", "category", "name_de", "name_en", "name_ru", "min_eur", "max_eur", "active", "description_de"]),
    "client": ("Clients", ["client_id", "created_at", "language", "shoot_count"]),
    "shoot": ("Shoots", ["shoot_id", "client_id", "lead_id", "category", "package", "date", "duration_hours", "status", "contract_amount_eur"]),
    "task": ("Tasks", ["task_id", "client_id", "shoot_id", "due_date", "status"]),
    "payment": ("Payments", ["payment_id", "shoot_id", "amount_eur", "kind", "paid_on"]),
}
REPORT_TABS = {
    "Monthly report": ["month", "category", "shoot_count", "contracted_eur", "received_eur", "outstanding_eur"],
    "Website metrics": ["month", "sessions", "average_seconds", "page_views", "cursor_events", "form_starts", "form_submits"],
}


def is_configured() -> bool:
    credentials_file = Path(os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "/run/secrets/google_service_account.json"))
    return bool(os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")) and credentials_file.is_file()


def _api():
    spreadsheet_id = os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"]
    credentials_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "/run/secrets/google_service_account.json")
    credentials = service_account.Credentials.from_service_account_file(credentials_file, scopes=SCOPE)
    return build("sheets", "v4", credentials=credentials, cache_discovery=False), spreadsheet_id


def _ensure_sheet(service, spreadsheet_id: str, title: str, headers: list[str]) -> None:
    metadata = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets.properties.title",
    ).execute()
    titles = {sheet["properties"]["title"] for sheet in metadata.get("sheets", [])}
    if title not in titles:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": title}}}]},
        ).execute()
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{title}'!A1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, (Decimal, date)):
        return str(value)
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return value


def _record(db: Session, entity_type: str, entity_id: int) -> list:
    if entity_type == "application":
        row = db.get(models.Application, entity_id)
        if row is None:
            raise ValueError("Application was removed before sync")
        service = db.get(models.Service, row.service_id)
        return [row.id, row.created_at.isoformat(), row.language, service.category if service else "Other",
                service.name if service else "", _cell(row.preferred_date), _cell(row.budget_eur), row.status,
                row.priority_label, row.priority_score, row.priority_reasons, row.client_id]
    if entity_type == "service":
        row = db.get(models.Service, entity_id)
        if row is None:
            return [entity_id, "", "[deleted]", "", "", "", "", "FALSE", ""]
        return [row.id, row.category, row.name, row.name_en, row.name_ru, _cell(row.min_price_eur),
                _cell(row.max_price_eur), _cell(row.active), row.description]
    if entity_type == "client":
        row = db.get(models.Client, entity_id)
        if row is None:
            raise ValueError("Client was removed before sync")
        return [row.id, row.created_at.isoformat(), row.language, len(row.shoots)]
    if entity_type == "shoot":
        row = db.get(models.Shoot, entity_id)
        if row is None:
            raise ValueError("Shoot was removed before sync")
        return [row.id, row.client_id, row.application_id, row.category, row.package_name, _cell(row.shoot_date),
                _cell(row.duration_hours), row.status, _cell(row.contract_amount_eur)]
    if entity_type == "task":
        row = db.get(models.Task, entity_id)
        if row is None:
            raise ValueError("Task was removed before sync")
        return [row.id, row.client_id, row.shoot_id, _cell(row.due_date), row.status]
    if entity_type == "payment":
        row = db.get(models.Payment, entity_id)
        if row is None:
            raise ValueError("Payment was removed before sync")
        return [row.id, row.shoot_id, _cell(row.amount_eur), row.kind, _cell(row.paid_on)]
    raise ValueError("Unknown entity type")


def _upsert_row(service, spreadsheet_id: str, title: str, values: list) -> None:
    ids = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{title}'!A:A",
        majorDimension="COLUMNS",
    ).execute().get("values", [[]])[0]
    record_id = str(values[0])
    try:
        row_number = next(index for index, value in enumerate(ids, start=1) if str(value) == record_id)
    except (StopIteration, ValueError):
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"'{title}'!A:A",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [[_cell(value) for value in values]]},
        ).execute()
        return
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{title}'!A{row_number}",
        valueInputOption="RAW",
        body={"values": [[_cell(value) for value in values]]},
    ).execute()


def _replace_report(service, spreadsheet_id: str, title: str, headers: list[str], rows: list[list]) -> None:
    _ensure_sheet(service, spreadsheet_id, title, headers)
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=f"'{title}'!A2:Z",
        body={},
    ).execute()
    if rows:
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{title}'!A2",
            valueInputOption="RAW",
            body={"values": [[_cell(value) for value in row] for row in rows]},
        ).execute()


def _write_reports(service, spreadsheet_id: str) -> None:
    """Write compact account and analytics summaries, excluding visitor identifiers."""
    from collections import defaultdict
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    berlin = ZoneInfo("Europe/Berlin")
    with SessionLocal() as db:
        shoots = db.scalars(select(models.Shoot).order_by(models.Shoot.id)).all()
        payments = db.scalars(select(models.Payment).order_by(models.Payment.id)).all()
        metrics = db.scalars(select(models.BehaviorMetric).order_by(models.BehaviorMetric.id)).all()

        payment_by_shoot: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for payment in payments:
            amount = Decimal(payment.amount_eur)
            payment_by_shoot[payment.shoot_id] += -amount if payment.kind == "refund" else amount
        report: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
            lambda: {"count": 0, "contracted": Decimal("0.00"), "received": Decimal("0.00")}
        )
        for shoot in shoots:
            if shoot.status == "cancelled":
                continue
            month = shoot.shoot_date.strftime("%Y-%m") if shoot.shoot_date else "Unscheduled"
            key = (month, shoot.category)
            aggregate = report[key]
            aggregate["count"] += 1
            aggregate["contracted"] += Decimal(shoot.contract_amount_eur)
            aggregate["received"] += payment_by_shoot[shoot.id]
        report_rows = [
            [month, category, values["count"], values["contracted"], values["received"], values["contracted"] - values["received"]]
            for (month, category), values in sorted(report.items())
        ]

        by_month: dict[str, dict] = defaultdict(lambda: {"sessions": set(), "times": defaultdict(list), "events": defaultdict(int)})
        for metric in metrics:
            stamp = metric.occurred_at
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            month = stamp.astimezone(berlin).strftime("%Y-%m")
            aggregate = by_month[month]
            aggregate["sessions"].add(metric.session_id)
            aggregate["times"][metric.session_id].append(stamp)
            aggregate["events"][metric.event_name] += 1
        metric_rows = []
        for month, values in sorted(by_month.items()):
            durations = [max(0, int((max(times) - min(times)).total_seconds())) for times in values["times"].values() if times]
            metric_rows.append([
                month, len(values["sessions"]), round(sum(durations) / len(durations)) if durations else 0,
                values["events"]["page_view"], values["events"]["cursor"],
                values["events"]["form_start"], values["events"]["form_submit"],
            ])

    _replace_report(service, spreadsheet_id, "Monthly report", REPORT_TABS["Monthly report"], report_rows)
    _replace_report(service, spreadsheet_id, "Website metrics", REPORT_TABS["Website metrics"], metric_rows)


def sync_one_pending() -> bool:
    if not is_configured():
        return False
    with SessionLocal() as db:
        event = db.scalar(
            select(models.SheetsOutbox)
            .where(models.SheetsOutbox.status == "pending")
            .order_by(models.SheetsOutbox.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if event is None:
            return False
        event.status = "processing"
        db.commit()
        event_id, entity_type, entity_id = event.id, event.entity_type, event.entity_id

    try:
        service, spreadsheet_id = _api()
        title, headers = SHEETS[entity_type]
        _ensure_sheet(service, spreadsheet_id, title, headers)
        with SessionLocal() as db:
            values = _record(db, entity_type, entity_id)
        _upsert_row(service, spreadsheet_id, title, values)
    except Exception as exc:  # Network/API errors remain recoverable via the admin retry action.
        http_status = exc.resp.status if isinstance(exc, HttpError) else None
        logger.warning(
            "Google Sheets sync failed for event_id=%s error_type=%s http_status=%s",
            event_id,
            type(exc).__name__,
            http_status,
        )
        with SessionLocal() as db:
            row = db.get(models.SheetsOutbox, event_id)
            if row:
                row.status = "error"
                row.attempts += 1
                row.last_error = type(exc).__name__[:500]
                db.commit()
        return True

    with SessionLocal() as db:
        row = db.get(models.SheetsOutbox, event_id)
        if row:
            row.status = "done"
            row.attempts += 1
            row.last_error = None
            db.commit()
    return True


def sync_reports() -> None:
    """Refresh account and analytics summaries once after the outbox drains."""
    if not is_configured():
        return
    service, spreadsheet_id = _api()
    _write_reports(service, spreadsheet_id)


def retry_errors(db: Session) -> int:
    rows = db.scalars(select(models.SheetsOutbox).where(models.SheetsOutbox.status == "error")).all()
    for row in rows:
        row.status = "pending"
        row.last_error = None
    return len(rows)
