from __future__ import annotations

from typing import Any


def build_candidate_profile() -> dict[str, Any]:
    return {
        "name": "Abhishek",
        "title": "Senior DevOps Engineer",
        "years_experience": 8,
        "preferred_locations": ["Berlin", "Munich", "Frankfurt", "Remote"],
        "core_technologies": [
            "AWS",
            "Kubernetes",
            "Terraform",
            "CI/CD",
            "Observability",
            "Platform engineering",
            "SRE",
        ],
    }


def _normalize(value: str | None) -> str:
    return (value or "").lower().replace("/", " ")


def _has_keyword(text: str, *keywords: str) -> bool:
    return any(keyword in text for keyword in keywords)


def calculate_ats(job: dict[str, Any]) -> int:
    text = " ".join(
        [
            job.get("title", ""),
            job.get("company", ""),
            job.get("description", ""),
            " ".join(job.get("tech_stack", [])),
            job.get("location", ""),
        ]
    )
    normalized = _normalize(text)

    score = 0

    if _has_keyword(
        normalized, "aws", "eks", "cloudformation", "iam", "gcp", "azure", "cloud platform", "cloud infrastructure"
    ):
        score += 15
    if _has_keyword(normalized, "kubernetes", "k8s", "helm", "docker", "containers", "container orchestration"):
        score += 15
    if _has_keyword(normalized, "terraform", "terragrunt", "infrastructure as code", "iac", "pulumi"):
        score += 20
    if _has_keyword(
        normalized,
        "ci/cd",
        "github actions",
        "gitlab ci",
        "jenkins",
        "argo cd",
        "buildkite",
        "circleci",
        "continuous integration",
        "continuous delivery",
        "continuous deployment",
        "gitops",
    ):
        score += 15
    if _has_keyword(
        normalized,
        "observability",
        "prometheus",
        "grafana",
        "datadog",
        "cloudwatch",
        "opentelemetry",
        "monitoring",
        "logging",
        "tracing",
        "metrics",
    ):
        score += 15
    if _has_keyword(
        normalized,
        "startup",
        "platform engineering",
        "platform",
        "sre",
        "devops",
        "site reliability",
        "reliability engineer",
        "infrastructure engineer",
    ):
        score += 10
    if (
        _has_keyword(normalized, "english", "english speaking", "remote")
        or "germany" in normalized
        or "berlin" in normalized
        or "munich" in normalized
        or "frankfurt" in normalized
    ):
        score += 10

    return min(score, 100)


def score_jobs(jobs: list[dict | Any], profile: dict[str, Any]) -> list[dict]:
    scored: list[dict] = []
    for job in jobs:
        if hasattr(job, "to_dict"):
            payload = job.to_dict()
        else:
            payload = dict(job)

        ats_score = calculate_ats(payload)
        payload["ats_score"] = ats_score
        payload["fit_reason"] = _fit_reason(payload)
        payload["preferred_location"] = any(
            location.lower() in payload.get("location", "").lower()
            for location in profile.get("preferred_locations", [])
        )
        scored.append(payload)

    return sorted(scored, key=lambda item: item.get("ats_score", 0), reverse=True)


def _fit_reason(job: dict[str, Any]) -> str:
    reasons: list[str] = []
    text = " ".join([
        job.get("title", ""),
        job.get("description", ""),
        " ".join(job.get("tech_stack", [])),
    ]).lower()

    if "aws" in text or "kubernetes" in text:
        reasons.append("AWS/Kubernetes fit")
    if "terraform" in text:
        reasons.append("Terraform fit")
    if "github actions" in text or "jenkins" in text or "ci/cd" in text:
        reasons.append("CI/CD fit")
    if "observability" in text or "grafana" in text or "prometheus" in text:
        reasons.append("Observability fit")
    if not reasons:
        reasons.append("Strong platform engineering alignment")
    return "; ".join(reasons)
