from pathlib import Path

from sqlalchemy import Engine, text


MIGRATIONS_DIR = Path(__file__).with_name("migrations")


def run_migrations(engine: Engine) -> None:
    """Apply checked-in, ordered SQL migrations once per database."""
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version VARCHAR(80) PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
        )
        applied = set(connection.execute(text("SELECT version FROM schema_migrations")).scalars())
        for migration_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = migration_path.stem
            if version in applied:
                continue
            sql = migration_path.read_text(encoding="utf-8")
            for statement in (part.strip() for part in sql.split(";")):
                if statement:
                    connection.exec_driver_sql(statement)
            connection.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": version},
            )
