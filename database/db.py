from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable


class JobDatabase:
    def __init__(self, db_path: str | Path = "database/jobs.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.init()

    def init(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT,
                salary TEXT,
                remote_policy TEXT,
                application_url TEXT,
                company_website TEXT,
                application_url_type TEXT,
                tech_stack TEXT,
                description TEXT,
                dedupe_hash TEXT NOT NULL UNIQUE,
                ats_score INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(jobs)").fetchall()
        }
        if "company_website" not in columns:
            self.conn.execute("ALTER TABLE jobs ADD COLUMN company_website TEXT")
        if "application_url_type" not in columns:
            self.conn.execute("ALTER TABLE jobs ADD COLUMN application_url_type TEXT")
        self.conn.commit()

    def upsert_jobs(self, jobs: Iterable[dict]) -> list[dict]:
        inserted: list[dict] = []
        for job in jobs:
            payload = {
                "source": job.get("source", "manual"),
                "company": job.get("company", "Unknown"),
                "title": job.get("title", "Unknown role"),
                "location": job.get("location", "Remote"),
                "salary": job.get("salary") or "Not disclosed",
                "remote_policy": job.get("remote_policy") or "Unknown",
                "application_url": job.get("application_url") or "",
                "company_website": job.get("company_website") or "",
                "application_url_type": job.get("application_url_type") or "Job application",
                "tech_stack": json.dumps(job.get("tech_stack") or []),
                "description": job.get("description") or "",
                "dedupe_hash": job.get("dedupe_hash") or job.get("id") or f"{job.get('source')}-{job.get('company')}-{job.get('title')}",
                "ats_score": int(job.get("ats_score", 0)),
            }
            self.conn.execute(
                """
                INSERT INTO jobs (
                    source, company, title, location, salary, remote_policy, application_url, company_website,
                    application_url_type,
                    tech_stack, description, dedupe_hash, ats_score, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(dedupe_hash) DO UPDATE SET
                    source=excluded.source,
                    company=excluded.company,
                    title=excluded.title,
                    location=excluded.location,
                    salary=excluded.salary,
                    remote_policy=excluded.remote_policy,
                    application_url=excluded.application_url,
                    company_website=excluded.company_website,
                    application_url_type=excluded.application_url_type,
                    tech_stack=excluded.tech_stack,
                    description=excluded.description,
                    ats_score=excluded.ats_score,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    payload["source"],
                    payload["company"],
                    payload["title"],
                    payload["location"],
                    payload["salary"],
                    payload["remote_policy"],
                    payload["application_url"],
                    payload["company_website"],
                    payload["application_url_type"],
                    payload["tech_stack"],
                    payload["description"],
                    payload["dedupe_hash"],
                    payload["ats_score"],
                ),
            )
            inserted.append(payload)
        self.conn.commit()
        return inserted

    def fetch_recent(self, limit: int = 20) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM jobs ORDER BY ats_score DESC, updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        result: list[dict] = []
        for row in rows:
            result.append({
                "id": row["id"],
                "source": row["source"],
                "company": row["company"],
                "title": row["title"],
                "location": row["location"],
                "salary": row["salary"],
                "remote_policy": row["remote_policy"],
                "application_url": row["application_url"],
                "company_website": row["company_website"] or "",
                "application_url_type": row["application_url_type"] or "Job application",
                "tech_stack": json.loads(row["tech_stack"] or "[]"),
                "description": row["description"],
                "ats_score": row["ats_score"],
            })
        return result

    def close(self) -> None:
        self.conn.close()
