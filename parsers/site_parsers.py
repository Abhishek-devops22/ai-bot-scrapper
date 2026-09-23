from __future__ import annotations

import os
import re
from typing import Iterable

import requests
from bs4 import BeautifulSoup

from .base import Job


def _salary_from_record(record: dict) -> str:
    salary = (
        record.get("salary")
        or record.get("salary_range")
        or record.get("compensation")
        or record.get("pay")
    )
    if isinstance(salary, dict):
        minimum = salary.get("min") or salary.get("minimum") or salary.get("minSalary")
        maximum = salary.get("max") or salary.get("maximum") or salary.get("maxSalary")
        currency = salary.get("currency") or salary.get("currencyCode") or ""
        if minimum and maximum:
            return f"{currency}{minimum} - {currency}{maximum}".strip()
        if minimum or maximum:
            return f"{currency}{minimum or maximum}".strip()
    if salary:
        return str(salary)
    description = str(record.get("description") or record.get("content") or "")
    match = re.search(
        r"(?i)(?:€|EUR|USD|\$|£)\s?\d[\d,]*(?:\s?(?:k|K))?(?:\s*[-–]\s*(?:€|EUR|USD|\$|£)?\s?\d[\d,]*(?:\s?(?:k|K))?)?",
        description,
    )
    return match.group(0) if match else "Not disclosed"


def _company_website(record: dict) -> str:
    return str(
        record.get("company_website")
        or record.get("company_url")
        or record.get("companyUrl")
        or record.get("website")
        or ""
    )


def _demo_jobs() -> list[Job]:
    jobs = [
        Job(
            source="greenhouse",
            company="Zalando",
            title="Senior DevOps Engineer",
            location="Berlin, Germany",
            salary="€110k - €140k",
            remote_policy="Hybrid",
            application_url="https://jobs.zalando.com/",
            company_website="https://www.zalando.com/",
            application_url_type="Company careers page",
            tech_stack=["AWS", "Kubernetes", "Terraform", "GitHub Actions", "Observability"],
            description=(
                "Design and operate AWS Kubernetes platforms, ship infrastructure as code with Terraform, "
                "drive CI/CD automation, and improve observability across production services."
            ),
        ),
        Job(
            source="lever",
            company="Delivery Hero",
            title="Platform Engineer",
            location="Munich, Germany",
            salary="€105k - €130k",
            remote_policy="Remote-first",
            application_url="https://careers.deliveryhero.com/",
            company_website="https://www.deliveryhero.com/",
            application_url_type="Company careers page",
            tech_stack=["AWS", "EKS", "Terraform", "GitHub Actions", "Prometheus", "Grafana"],
            description=(
                "Build secure cloud platform services using AWS and Kubernetes, automate with Terraform, "
                "and create production-grade observability pipelines and CI/CD workflows."
            ),
        ),
        Job(
            source="ashby",
            company="SAP",
            title="Site Reliability Engineer",
            location="Remote, Germany",
            salary="€100k - €120k",
            remote_policy="Remote",
            application_url="https://www.sap.com/about/careers.html",
            company_website="https://www.sap.com/",
            application_url_type="Company careers page",
            tech_stack=["Kubernetes", "Terraform", "Prometheus", "Grafana", "CI/CD"],
            description=(
                "Run resilient Kubernetes systems, improve incident response, set up observability, and "
                "ship automation for release and recovery workflows."
            ),
        ),
        Job(
            source="smartrecruiters",
            company="Siemens",
            title="Senior Cloud Engineer",
            location="Frankfurt, Germany",
            salary="€95k - €125k",
            remote_policy="Hybrid",
            application_url="https://www.siemens.com/global/en/company/jobs.html",
            company_website="https://www.siemens.com/",
            application_url_type="Company careers page",
            tech_stack=["AWS", "Terraform", "GitLab CI", "Observability", "Docker"],
            description=(
                "Own AWS infrastructure through IaC, automate deployment pipelines, and improve service reliability with "
                "observability tooling and production engineering best practices."
            ),
        ),
        Job(
            source="company-careers",
            company="Bosch",
            title="DevOps Engineer",
            location="Remote",
            salary="€90k - €115k",
            remote_policy="Remote",
            application_url="https://www.bosch.com/careers/",
            company_website="https://www.bosch.com/",
            application_url_type="Company careers page",
            tech_stack=["AWS", "Docker", "Kubernetes", "CI/CD", "Terraform"],
            description=(
                "Create a platform for microservices, collaborate with product teams, and maintain production "
                "quality setups using AWS, Kubernetes, Terraform, and modern CI/CD."
            ),
        ),
    ]

    additional_companies = [
        ("BMW Group", "Munich", "Cloud Platform Engineer", "https://www.bmwgroup.jobs/en.html"),
        ("Mercedes-Benz", "Berlin", "Senior DevOps Engineer", "https://group.mercedes-benz.com/careers/"),
        ("Deutsche Telekom", "Frankfurt", "Site Reliability Engineer", "https://www.telekom.com/en/careers"),
        ("HelloFresh", "Berlin", "Senior Cloud Infrastructure Engineer", "https://careers.hellofresh.com/"),
        ("Celonis", "Munich", "Cloud Platform Engineer", "https://www.celonis.com/careers/"),
        ("Personio", "Munich", "Senior DevOps Engineer", "https://www.personio.com/about-personio/careers/"),
        ("N26", "Berlin", "Platform Engineer", "https://n26.com/en-eu/careers"),
        ("GetYourGuide", "Berlin", "Senior SRE", "https://www.getyourguide.careers/"),
        ("Flix", "Munich", "Cloud Reliability Engineer", "https://www.flix.careers/"),
        ("SoundCloud", "Berlin", "Infrastructure Platform Engineer", "https://careers.soundcloud.com/"),
        ("AWS", "Berlin", "Senior Cloud DevOps Engineer", "https://www.amazon.jobs/en/locations/berlin-germany"),
        ("Google", "Munich", "Site Reliability Engineer", "https://www.google.com/about/careers/"),
        ("Microsoft", "Munich", "Cloud Platform Engineer", "https://jobs.careers.microsoft.com/"),
        ("Cloudflare", "Remote", "Senior SRE", "https://www.cloudflare.com/careers/jobs/"),
        ("GitLab", "Remote", "Senior DevOps Engineer", "https://about.gitlab.com/jobs/"),
        ("Elastic", "Remote", "Platform Engineer", "https://www.elastic.co/about/careers"),
        ("Datadog", "Remote", "Observability Platform Engineer", "https://careers.datadoghq.com/"),
        ("Grafana Labs", "Remote", "Senior SRE", "https://grafana.com/about/careers/"),
        ("Canonical", "Remote", "Infrastructure Engineer", "https://canonical.com/careers"),
        ("Red Hat", "Remote", "Cloud Platform Engineer", "https://www.redhat.com/en/jobs"),
    ]
    for index, (company, location, title, careers_url) in enumerate(additional_companies, start=1):
        jobs.append(
            Job(
                source="company-careers",
                company=company,
                title=title,
                location=f"{location}, Germany" if location != "Remote" else "Remote, Germany",
                salary=f"€{100 + index}k - €{125 + index}k",
                remote_policy="Remote" if location == "Remote" else "Hybrid",
                application_url=careers_url,
                company_website=careers_url,
                application_url_type="Company careers page",
                tech_stack=["AWS", "Kubernetes", "Terraform", "GitHub Actions", "Prometheus", "Grafana"],
                description=(
                    "English-speaking role for a senior DevOps and platform engineer. Operate AWS and Kubernetes, "
                    "manage Terraform infrastructure, improve CI/CD automation, and build production observability "
                    "with Prometheus and Grafana for a high-growth platform team."
                ),
            )
        )
    return jobs


def _parse_generic_job_listing(html: str, source: str) -> list[Job]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[Job] = []
    for card in soup.select("article, .job, .posting, li"):
        title_tag = card.select_one("h2, h3, .title, a")
        company_tag = card.select_one(".company, .employer, span.company")
        if not title_tag:
            continue
        title = title_tag.get_text(" ", strip=True)
        company = company_tag.get_text(" ", strip=True) if company_tag else "Unknown company"
        jobs.append(
            Job(
                source=source,
                company=company,
                title=title,
                location="Remote",
                salary="Not disclosed",
                remote_policy="Unknown",
                application_url=title_tag.get("href", "") or "",
                company_website="",
                tech_stack=["AWS", "Kubernetes", "Terraform"],
                description=(
                    "Candidate generated from HTML payload; real parser should extract the full job description."
                ),
            )
        )
    return jobs


def _fetch_live_jobs() -> list[Job]:
    pages: list[tuple[str, str]] = [
        ("greenhouse", "https://boards-api.greenhouse.io/v1/boards/greenhouse/jobs?content=true"),
        ("lever", "https://api.lever.co/v0/postings/companyname?mode=json"),
        ("smartrecruiters", "https://api.smartrecruiters.com/companies/"),
    ]

    jobs: list[Job] = []
    for source, url in pages:
        try:
            response = requests.get(url, timeout=12)
            response.raise_for_status()
            payload = response.json()
            candidates = payload.get("jobs", []) if isinstance(payload, dict) else payload
            for record in candidates[:3]:
                title = record.get("title") or record.get("name") or "Unknown role"
                company = record.get("company_name") or record.get("company") or "Unknown company"
                description = record.get("description") or ""
                location = record.get("location") or record.get("office_location") or "Remote"
                jobs.append(
                    Job(
                        source=source,
                        company=str(company),
                        title=str(title),
                        location=str(location),
                        salary=_salary_from_record(record),
                        remote_policy="Unknown",
                        application_url=str(record.get("absolute_url") or ""),
                        company_website=_company_website(record),
                        tech_stack=["AWS", "Kubernetes", "Terraform"],
                        description=str(description),
                    )
                )
        except Exception:
            continue
    return jobs


def collect_jobs() -> list[Job]:
    """Return the best available candidate jobs, falling back to demo data when live fetches fail."""
    if os.getenv("DISABLE_NETWORK", "false").lower() == "true":
        return _demo_jobs()

    live_jobs = _fetch_live_jobs()
    if live_jobs:
        return live_jobs
    return _demo_jobs()
