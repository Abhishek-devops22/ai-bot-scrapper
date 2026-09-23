from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from database.db import JobDatabase
from emailer import generate_email_report, send_email_report
from matcher import build_candidate_profile, score_jobs
from parsers import collect_jobs


load_dotenv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI-powered DevOps job matching bot")
    parser.add_argument("--demo", action="store_true", help="Use the built-in sample jobs instead of live scraping")
    parser.add_argument("--out-dir", default="out", help="Directory for generated reports")
    parser.add_argument("--email", action="store_true", help="Send the generated email report via SMTP if configured")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile = build_candidate_profile()
    db = JobDatabase("database/jobs.db")

    # Build the working set of jobs.
    raw_jobs = collect_jobs() if not args.demo else []
    if args.demo:
        from parsers.site_parsers import _demo_jobs
        raw_jobs = _demo_jobs()

    scored_jobs = score_jobs(raw_jobs, profile)
    shortlisted = [
        job
        for job in scored_jobs
        if job["ats_score"] >= 80 and job["preferred_location"]
    ]

    db.upsert_jobs(shortlisted)

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = generate_email_report(shortlisted, profile, output_dir)

    if args.email:
        try:
            send_email_report(report["html_path"], report["pdf_path"], profile)
        except Exception as exc:
            print(f"Email delivery failed: {exc}")

    print(f"Matched {len(shortlisted)} qualified jobs to the profile and saved reports to {output_dir}.")
    print(f"HTML report: {report['html_path']}")
    print(f"PDF report: {report['pdf_path']}")

    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
