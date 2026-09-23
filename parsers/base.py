from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any


@dataclass
class Job:
    source: str
    company: str
    title: str
    location: str
    salary: str = "Not disclosed"
    remote_policy: str = "Unknown"
    application_url: str = ""
    company_website: str = ""
    application_url_type: str = "Job application"
    tech_stack: list[str] = field(default_factory=list)
    description: str = ""
    job_url: str = ""
    dedupe_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.dedupe_hash = sha256(
            f"{self.source}|{self.company}|{self.title}|{self.application_url or self.job_url}".encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "company": self.company,
            "title": self.title,
            "location": self.location,
            "salary": self.salary,
            "remote_policy": self.remote_policy,
            "application_url": self.application_url,
            "company_website": self.company_website,
            "application_url_type": self.application_url_type,
            "tech_stack": self.tech_stack,
            "description": self.description,
            "job_url": self.job_url,
            "dedupe_hash": self.dedupe_hash,
        }
