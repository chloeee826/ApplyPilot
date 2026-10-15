"""Additive v1 ownership upgrade for the previously schema-less local MVP.

Legacy rows deliberately stay unowned. No first-user auto-claim, drop or overwrite.
"""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy import Uuid


def upgrade_ownership(engine: Engine) -> None:
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(81015001)"))
        for table in ("jobs", "candidate_profiles"):
            columns = {column["name"] for column in inspect(connection).get_columns(table)}
            if "owner_id" not in columns:
                column_type = Uuid().compile(dialect=engine.dialect)
                connection.exec_driver_sql(
                    f'ALTER TABLE "{table}" ADD COLUMN owner_id {column_type} REFERENCES users(id)')
            connection.exec_driver_sql(f'CREATE INDEX IF NOT EXISTS ix_{table}_owner_id ON "{table}" (owner_id)')
