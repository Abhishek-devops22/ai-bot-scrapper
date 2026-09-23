from __future__ import annotations

import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_email_report(jobs: list[dict], candidate: dict, output_dir: str | Path) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    template_dir = Path(__file__).resolve().parent / "templates"
    environment = Environment(loader=FileSystemLoader(str(template_dir)))
    template = environment.get_template("email_report.html")
    html = template.render(
        candidate=candidate,
        jobs=jobs,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    html_path = output_dir / "daily-job-report.html"
    html_path.write_text(html, encoding="utf-8")

    pdf_path = output_dir / "daily-job-report.pdf"
    _generate_pdf_summary(pdf_path, jobs)

    return {"html_path": str(html_path), "pdf_path": str(pdf_path)}


def _generate_pdf_summary(pdf_path: Path, jobs: list[dict]) -> None:
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.setTitle("DevOps Job Matching Report")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 760, "AI DevOps Job Matching Bot")
    c.setFont("Helvetica", 10)
    c.drawString(50, 742, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    y = 700
    for index, job in enumerate(jobs[:12], start=1):
        line = (
            f"{index}. {job.get('company', 'Unknown')} - {job.get('title', 'Unknown title')} "
            f"| ATS {job.get('ats_score', 0)} | Salary: {job.get('salary', 'Not disclosed')}"
        )
        if y < 60:
            c.showPage()
            y = 760
        c.drawString(50, y, line)
        y -= 20
        c.setFont("Helvetica", 8)
        c.drawString(62, y, f"Company: {job.get('company_website') or 'Not provided'}")
        y -= 14
        c.drawString(
            62,
            y,
            f"{job.get('application_url_type', 'Job application')}: "
            f"{job.get('application_url') or 'Not provided'}",
        )
        c.setFont("Helvetica", 10)
        y -= 24

    c.save()


def send_email_report(html_path: str, pdf_path: str, candidate: dict) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("EMAIL_TO")
    if not all([smtp_host, smtp_user, smtp_password, recipient]):
        raise ValueError("SMTP configuration is incomplete. Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and EMAIL_TO.")

    message = EmailMessage()
    message["Subject"] = f"Daily DevOps Job Matching Report for {candidate.get('name', 'Candidate')}"
    message["From"] = os.getenv("SMTP_FROM", smtp_user)
    message["To"] = recipient

    message.set_content("Your generated email report is attached.")
    message.add_alternative(Path(html_path).read_text(encoding="utf-8"), subtype="html")

    with open(pdf_path, "rb") as pdf_file:
        message.add_attachment(
            pdf_file.read(),
            maintype="application",
            subtype="pdf",
            filename="daily-job-report.pdf",
        )

    with smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", "587"))) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)
