"""Email delivery service using Gmail SMTP.

Sends analysis reports (with optional PDF attachment) via Gmail's SMTP server.
Uses Python's built-in ``smtplib`` + ``email.mime`` — no extra packages needed.

How Gmail App Passwords work:
  - Google blocks regular passwords from third-party apps for security.
  - An "App Password" is a special 16-character password that bypasses this.
  - You must enable 2-Step Verification first, then generate one at:
    https://myaccount.google.com/apppasswords

How SMTP works (simplified):
  1. Our code opens a TCP connection to smtp.gmail.com on port 465.
  2. The connection is encrypted with TLS from the very start (SMTP_SSL).
  3. We authenticate with the sender's email + App Password.
  4. We hand the server a "MIME message" — an envelope containing:
     - Headers: From, To, Subject
     - Body: the plain-text analysis summary
     - Attachment: the PDF report (base64-encoded)
  5. Gmail's server delivers the email to the recipient.
"""

from __future__ import annotations

import smtplib                        # Python's built-in SMTP client
from email import encoders            # For base64-encoding attachments
from email.mime.base import MIMEBase  # Generic MIME part (for the PDF)
from email.mime.multipart import MIMEMultipart  # The "envelope" that holds everything
from email.mime.text import MIMEText  # A text part (the email body)
from pathlib import Path

from tahalilai.config import get_settings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def send_report_email(
    recipient_email: str,
    subject: str,
    body_text: str,
    pdf_path: str | Path | None = None,
) -> dict[str, str]:
    """Send an email with an optional PDF attachment via Gmail SMTP.

    This function NEVER raises exceptions to the caller. Instead, it
    returns a dict with ``"status"`` = ``"sent"`` or ``"error"``.
    This pattern is the same as other TahalilAI services.

    Args:
        recipient_email: Where to send (e.g. ``"patient@example.com"``).
        subject: Email subject line.
        body_text: Plain-text body (the analysis summary).
        pdf_path: Optional path to a PDF file to attach.

    Returns:
        ``{"status": "sent"}`` on success, or
        ``{"status": "error", "message": "..."}`` on failure.
    """
    settings = get_settings()

    # ── Guard: credentials must be set in .env ──
    if not settings.smtp_sender_email or not settings.smtp_app_password:
        return {
            "status": "error",
            "message": "SMTP_SENDER_EMAIL and SMTP_APP_PASSWORD must be set in .env",
        }

    # ── Guard: if a PDF was requested, it must exist ──
    if pdf_path is not None:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            print(f"Email: PDF not found at {pdf_path}")
            return {"status": "error", "message": "PDF report not found. Please regenerate it."}

    try:
        # Step 1: Build the MIME message (envelope + body + attachment)
        msg = _build_message(
            sender=settings.smtp_sender_email,
            recipient=recipient_email,
            subject=subject,
            body_text=body_text,
            pdf_path=pdf_path,
        )

        # Step 2: Connect to Gmail and send it
        _send_via_smtp(
            host=settings.smtp_host,
            port=settings.smtp_port,
            sender=settings.smtp_sender_email,
            password=settings.smtp_app_password,
            recipient=recipient_email,
            message=msg,
        )

        print(f"Email sent to {recipient_email}")
        return {"status": "sent"}

    except smtplib.SMTPAuthenticationError:
        # Wrong App Password or account issue
        return {
            "status": "error",
            "message": "SMTP authentication failed. Check your App Password.",
        }
    except Exception as exc:
        # Catch-all: network errors, DNS issues, etc.
        return {"status": "error", "message": f"Failed to send email: {exc}"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_message(
    sender: str,
    recipient: str,
    subject: str,
    body_text: str,
    pdf_path: Path | None,
) -> MIMEMultipart:
    """Construct a MIME message with optional PDF attachment.

    MIME = Multipurpose Internet Mail Extensions. Think of it as a
    container format: one "envelope" (MIMEMultipart) can hold multiple
    "parts" — a text body, an HTML body, file attachments, etc.
    """
    # The "envelope"
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    # The text body — MIMEText wraps a string into a MIME-compatible part
    # "plain" = plain text (vs "html" for HTML emails)
    # "utf-8" = character encoding (supports Arabic, French, etc.)
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    # The PDF attachment (optional)
    if pdf_path is not None:
        attachment = _make_pdf_attachment(pdf_path)
        msg.attach(attachment)

    return msg


def _make_pdf_attachment(pdf_path: Path) -> MIMEBase:
    """Read a PDF file and return it as a base64-encoded MIME part.

    Why base64? Email was originally designed for text only (ASCII).
    Binary files (like PDFs) must be encoded as text to travel through
    email servers. base64 converts binary -> text safely.
    """
    # Create a generic MIME part with type "application/octet-stream"
    # (means "this is a binary file, download it")
    part = MIMEBase("application", "octet-stream")

    # Read the raw PDF bytes into the MIME part
    part.set_payload(pdf_path.read_bytes())

    # Encode the binary payload as base64 text
    encoders.encode_base64(part)

    # Tell the email client to show this as a downloadable file
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="{pdf_path.name}"',
    )
    return part


def _send_via_smtp(
    host: str,
    port: int,
    sender: str,
    password: str,
    recipient: str,
    message: MIMEMultipart,
) -> None:
    """Open an SSL connection to the SMTP server and send the message.

    SMTP_SSL connects on port 465 with TLS encryption from the start.
    The alternative (SMTP + STARTTLS on port 587) starts unencrypted
    then upgrades — slightly more complex for no real benefit.

    The ``with`` statement ensures the connection is properly closed
    even if an error occurs (context manager pattern).
    """
    with smtplib.SMTP_SSL(host, port) as server:
        server.login(sender, password)   # Authenticate with App Password
        server.sendmail(
            sender,          # From
            [recipient],     # To (list of recipients)
            message.as_string(),  # The full MIME message as text
        )
