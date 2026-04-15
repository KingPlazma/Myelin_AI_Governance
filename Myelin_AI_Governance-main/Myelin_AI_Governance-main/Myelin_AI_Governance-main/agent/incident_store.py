import json
import os
import sqlite3
from typing import List

from schemas import IncidentRecord


class IncidentStore:
    def __init__(self, database_path: str):
        self.database_path = database_path
        directory = os.path.dirname(database_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    request_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    route TEXT NOT NULL,
                    model TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    user_prompt TEXT NOT NULL,
                    bot_response TEXT,
                    remediated_response TEXT,
                    audit_report TEXT NOT NULL,
                    alert_email TEXT
                )
                """
            )
            connection.commit()

    def append(self, incident: IncidentRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO incidents (
                    request_id,
                    timestamp,
                    route,
                    model,
                    decision,
                    risk_level,
                    risk_score,
                    user_prompt,
                    bot_response,
                    remediated_response,
                    audit_report,
                    alert_email
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.request_id,
                    incident.timestamp,
                    incident.route,
                    incident.model,
                    incident.decision,
                    incident.risk_level,
                    incident.risk_score,
                    incident.user_prompt,
                    incident.bot_response,
                    incident.remediated_response,
                    json.dumps(incident.audit_report),
                    incident.alert_email
                )
            )
            connection.commit()

    def recent(self, limit: int = 20) -> List[IncidentRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    request_id,
                    timestamp,
                    route,
                    model,
                    decision,
                    risk_level,
                    risk_score,
                    user_prompt,
                    bot_response,
                    remediated_response,
                    audit_report,
                    alert_email
                FROM incidents
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()

        return [
            IncidentRecord(
                request_id=row["request_id"],
                timestamp=row["timestamp"],
                route=row["route"],
                model=row["model"],
                decision=row["decision"],
                risk_level=row["risk_level"],
                risk_score=row["risk_score"],
                user_prompt=row["user_prompt"],
                bot_response=row["bot_response"],
                remediated_response=row["remediated_response"],
                audit_report=json.loads(row["audit_report"]),
                alert_email=row["alert_email"]
            )
            for row in rows
        ]
