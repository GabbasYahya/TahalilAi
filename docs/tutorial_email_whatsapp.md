# Tutorial: Email & WhatsApp Integration in TahalilAI

This document explains everything about how we added email and WhatsApp
delivery to TahalilAI. It's written so you can build similar features
from scratch in future projects.

---

## Table of Contents

1. [Part 1: How Email Works (Gmail SMTP)](#part-1-how-email-works-gmail-smtp)
2. [Part 2: How WhatsApp Cloud API Works](#part-2-how-whatsapp-cloud-api-works)
3. [Part 3: Configuration & Environment Variables](#part-3-configuration--environment-variables)
4. [Part 4: FastAPI Endpoints & Background Tasks](#part-4-fastapi-endpoints--background-tasks)
5. [Part 5: Testing with Mocks](#part-5-testing-with-mocks)
6. [Appendix A: Complete Setup Checklist](#appendix-a-complete-setup-checklist)
7. [Appendix B: Quick Reference](#appendix-b-quick-reference)

---

## Part 1: How Email Works (Gmail SMTP)

### 1.1 What is SMTP?

SMTP (Simple Mail Transfer Protocol) is the standard protocol for sending
emails. Think of it like the postal service for the internet:

```
Your App  --SMTP-->  Gmail Server  --delivers-->  Recipient's Inbox
```

Python has a built-in `smtplib` module that speaks SMTP. No extra packages
needed.

### 1.2 Gmail App Passwords

Google blocks third-party apps from using your regular Gmail password
(for security). Instead, you create an "App Password":

**Steps:**
1. Go to your Google Account settings
2. Enable **2-Step Verification** (required first)
3. Go to https://myaccount.google.com/apppasswords
4. Select "Mail" as the app
5. Click "Generate" — you get a 16-character password like `abcd efgh ijkl mnop`
6. Put it in your `.env` file as `SMTP_APP_PASSWORD`

**Why App Passwords are safer:**
- They only grant email access (not your full Google account)
- You can revoke one App Password without affecting others
- They don't expire unless you revoke them

### 1.3 The MIME Format (How Emails Are Structured)

Emails aren't just text — they're structured documents called MIME
(Multipurpose Internet Mail Extensions). Think of it like a folder:

```
MIMEMultipart (the envelope)
  |
  +-- MIMEText (the letter — your email body)
  |
  +-- MIMEBase (the attachment — the PDF file, base64-encoded)
```

Here's what each part does in our code:

```python
# 1. Create the envelope
msg = MIMEMultipart()
msg["From"] = "you@gmail.com"      # Who sent it
msg["To"] = "patient@example.com"  # Who receives it
msg["Subject"] = "Your Lab Report" # Subject line

# 2. Add the text body
body = MIMEText("Hello, here are your results...", "plain", "utf-8")
msg.attach(body)

# 3. Add the PDF attachment
part = MIMEBase("application", "octet-stream")  # "this is a binary file"
part.set_payload(open("report.pdf", "rb").read())  # read the PDF bytes
encoders.encode_base64(part)  # convert binary to text (email needs text)
part.add_header("Content-Disposition", 'attachment; filename="report.pdf"')
msg.attach(part)
```

**Why base64?** Email was designed in the 1970s for text only (ASCII).
Binary files (PDFs, images) must be encoded as text characters to travel
through email servers. base64 does this encoding.

### 1.4 Sending the Email

```python
# SMTP_SSL = encrypted connection from the start (port 465)
with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login("you@gmail.com", "your-app-password")
    server.sendmail("you@gmail.com", ["patient@example.com"], msg.as_string())
```

**What happens step by step:**
1. `SMTP_SSL(host, 465)` — Opens a TCP connection to Gmail, encrypted with TLS
2. `login()` — Authenticates with your App Password
3. `sendmail()` — Hands the MIME message to Gmail for delivery
4. `with` block ends — Connection is automatically closed

**Port 465 vs 587:**
- Port 465 (SMTP_SSL): Encrypted from the start. Simpler.
- Port 587 (STARTTLS): Starts unencrypted, then upgrades. More complex for no benefit.
- We use 465 because it's simpler and equally secure.

### 1.5 Error Handling

```python
try:
    _send_via_smtp(...)
except smtplib.SMTPAuthenticationError:
    # Wrong App Password or account issue
    return {"status": "error", "message": "Check your App Password"}
except Exception as exc:
    # Network error, DNS failure, firewall, etc.
    return {"status": "error", "message": f"Failed: {exc}"}
```

We **never raise exceptions** to the caller. This is a TahalilAI
convention — all services return dicts with `"status"` keys.

---

## Part 2: How WhatsApp Cloud API Works

### 2.1 Architecture

```
Your Server                     Meta's Servers              Patient
    |                               |                         |
    |---POST JSON (HTTPS)---------->|                         |
    |                               |---WhatsApp message----->|
    |<--JSON response (message ID)--|                         |
```

It's a REST API: you send a POST request with JSON, Meta delivers the
message, and returns a confirmation.

### 2.2 Authentication

Every request needs two things:
- **Phone Number ID**: Identifies YOUR WhatsApp Business number
- **Access Token**: A secret string that proves you own that number

They go in the HTTP request like this:
```
URL: https://graph.facebook.com/v19.0/{phone_number_id}/messages
Header: Authorization: Bearer {access_token}
```

### 2.3 Sending a Text Message

The JSON payload for a text message:

```json
{
    "messaging_product": "whatsapp",
    "to": "213555000000",
    "type": "text",
    "text": {
        "body": "Hello! Your lab results are ready..."
    }
}
```

- `messaging_product`: Always `"whatsapp"` (Meta uses this to route correctly)
- `to`: Phone number in international format (digits only, no `+`)
- `type`: `"text"` for text messages, `"document"` for files
- `text.body`: The actual message (max 4096 characters)

### 2.4 Sending a Document

```json
{
    "messaging_product": "whatsapp",
    "to": "213555000000",
    "type": "document",
    "document": {
        "link": "https://your-server.com/uploads/report.pdf",
        "filename": "lab_report.pdf",
        "caption": "Your lab results"
    }
}
```

**Important**: The `link` must be a **public HTTPS URL** that Meta's servers
can download. During development, use tools like **ngrok** to expose
your localhost, or upload the PDF to cloud storage first.

### 2.5 Using urllib.request (Python's Built-in HTTP Client)

We use `urllib.request` instead of the `requests` library. Here's why:
- **No new dependency** — `urllib` is built into Python
- **Educational** — you learn how HTTP really works under the hood

Here's the flow, step by step:

```python
import json
import urllib.request

# 1. Build the URL
url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"

# 2. Convert the Python dict to JSON bytes
#    (HTTP sends bytes over the wire, not Python objects)
data = json.dumps(payload).encode("utf-8")

# 3. Set HTTP headers
headers = {
    "Authorization": f"Bearer {token}",  # Proves who we are
    "Content-Type": "application/json",   # Tells server what format we're sending
}

# 4. Create the request object (not sent yet!)
req = urllib.request.Request(url, data=data, headers=headers, method="POST")

# 5. Actually send it and read the response
with urllib.request.urlopen(req, timeout=30) as resp:
    body = json.loads(resp.read().decode("utf-8"))
    print(body)  # {"messages": [{"id": "wamid.abc123"}]}
```

**Compare with the `requests` library** (which does the same but simpler):
```python
import requests
resp = requests.post(url, json=payload, headers=headers, timeout=30)
body = resp.json()
```

Both work fine. We chose `urllib` for learning purposes and zero dependencies.

### 2.6 Error Handling

```python
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        ...
except urllib.error.HTTPError as exc:
    # Server returned 400, 401, 403, etc.
    error_body = exc.read().decode("utf-8")
    # Meta returns: {"error": {"message": "Invalid token", "type": "OAuthException"}}
    detail = json.loads(error_body)["error"]["message"]
except Exception as exc:
    # Network timeout, DNS failure, etc.
    ...
```

---

## Part 3: Configuration & Environment Variables

### 3.1 The Pydantic Settings Pattern

TahalilAI uses `pydantic-settings` to manage configuration. Here's how it works:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # These field names AUTOMATICALLY map to environment variables:
    # smtp_sender_email  -->  SMTP_SENDER_EMAIL in .env
    # smtp_app_password  -->  SMTP_APP_PASSWORD in .env
    smtp_sender_email: str = ""    # Empty default = optional
    smtp_app_password: str = ""
```

**How it loads values (in priority order):**
1. Environment variables (highest priority)
2. `.env` file values
3. Default values in the class (lowest priority)

**Why empty defaults for secrets?**
So the app can start without email/WhatsApp configured.
The service functions check if credentials exist before trying to send.

### 3.2 The .env File

```bash
# .env (NEVER commit this file — it's in .gitignore)
SMTP_SENDER_EMAIL=your.email@gmail.com
SMTP_APP_PASSWORD=abcd-efgh-ijkl-mnop
WHATSAPP_ACCESS_TOKEN=EAABs...long-token
WHATSAPP_PHONE_NUMBER_ID=123456789
```

**Security rule**: The `.env` file contains secrets. It's listed in
`.gitignore` so it's never pushed to GitHub. The `.env.example` file
shows the format with placeholder values.

---

## Part 4: FastAPI Endpoints & Background Tasks

### 4.1 The Background Task Pattern

Sending an email takes 2-5 seconds (network round-trip to Gmail).
We don't want the user's browser to freeze, so we use FastAPI's
`BackgroundTasks`:

```python
@app.post("/send-email")
async def send_email_endpoint(
    request: EmailRequest,
    background_tasks: BackgroundTasks,  # FastAPI injects this automatically
):
    # 1. Validate the request (fast — milliseconds)
    job = _jobs.get(request.job_id)
    if not job:
        return {"status": "error", "message": "Job not found"}

    # 2. Define what to do in the background
    def _email_task():
        result = send_report_email(...)
        print(f"Email result: {result}")

    # 3. Schedule it (doesn't run yet!)
    background_tasks.add_task(_email_task)

    # 4. Return immediately (the user sees "sending" instantly)
    return {"status": "sending", "message": "Email is being sent."}

    # 5. AFTER this response is sent, FastAPI runs _email_task()
```

**Timeline:**
```
0ms      User clicks "Send Email"
10ms     Server validates request
15ms     Server returns {"status": "sending"}  <-- User sees this
15ms+    Browser shows "Email is being sent"
2000ms   Background: Gmail connection opens, email sends
2500ms   Background: print("Email: {'status': 'sent'}")
```

### 4.2 Request Validation with Pydantic

```python
class EmailRequest(BaseModel):
    job_id: str = Field(..., description="UUID of the completed analysis job")
    recipient_email: str = Field(..., min_length=5, description="Recipient email")
```

When someone sends `POST /send-email` with JSON like:
```json
{"job_id": "abc-123", "recipient_email": "patient@example.com"}
```

FastAPI automatically:
1. Parses the JSON body
2. Validates `min_length=5` on `recipient_email`
3. Returns 422 error if validation fails
4. Creates an `EmailRequest` object if everything is valid

You never need to write validation code manually.

---

## Part 5: Testing with Mocks

### 5.1 Why We Mock External Services

**Never send real emails or call real APIs in tests.** Why?
- Tests would be slow (network calls)
- Tests would fail without internet
- You'd spam real inboxes
- API rate limits would break your CI

Instead, we **mock** (fake) the external parts:

```python
from unittest.mock import patch, MagicMock

# @patch replaces the REAL smtplib with a FAKE one during this test
@patch("tahalilai.services.email_sender.smtplib")
def test_send_email(mock_smtplib):
    # Create a fake SMTP server that does nothing
    mock_server = MagicMock()
    mock_smtplib.SMTP_SSL.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtplib.SMTP_SSL.return_value.__exit__ = MagicMock(return_value=False)

    # Now call the real function — it will use our fake smtplib
    result = send_report_email("patient@example.com", "Subject", "Body")

    # Verify it tried to send (without actually sending)
    assert result["status"] == "sent"
    mock_server.login.assert_called_once()
    mock_server.sendmail.assert_called_once()
```

### 5.2 The _mock_settings() Pattern

Every test file has a helper to create fake settings:

```python
def _mock_settings(*, sender="test@gmail.com", password="fake-pass"):
    s = MagicMock()
    s.smtp_host = "smtp.gmail.com"
    s.smtp_port = 465
    s.smtp_sender_email = sender
    s.smtp_app_password = password
    return s
```

Then in tests:
```python
with patch("tahalilai.services.email_sender.get_settings") as mock:
    mock.return_value = _mock_settings(sender="", password="")
    result = send_report_email(...)
assert result["status"] == "error"  # Missing creds!
```

### 5.3 Testing Error Paths

Always test what happens when things go **wrong**:

```python
def test_missing_credentials(self):
    """Empty SMTP creds → error dict, no connection attempt."""
    ...

def test_pdf_not_found(self):
    """PDF path doesn't exist → error before trying to send."""
    ...

def test_authentication_error(self):
    """Wrong password → SMTPAuthenticationError → clean error message."""
    ...

def test_network_error(self):
    """Can't reach Gmail → ConnectionRefusedError → clean error message."""
    ...
```

**Rule of thumb**: For every "happy path" test, write 2-3 "error path" tests.
Most bugs live in error handling, not in the happy path.

---

## Appendix A: Complete Setup Checklist

### Gmail SMTP Setup
- [ ] Enable 2-Step Verification on your Google account
- [ ] Generate an App Password at https://myaccount.google.com/apppasswords
- [ ] Add to `.env`:
  ```
  SMTP_SENDER_EMAIL=your.email@gmail.com
  SMTP_APP_PASSWORD=your-16-char-password
  ```

### WhatsApp Cloud API Setup
- [ ] Create a Meta Developer account at https://developers.facebook.com
- [ ] Create a new Business app
- [ ] Add the WhatsApp product to your app
- [ ] Go to WhatsApp > API Setup
- [ ] Copy your Phone Number ID and Access Token
- [ ] Add to `.env`:
  ```
  WHATSAPP_ACCESS_TOKEN=your-token
  WHATSAPP_PHONE_NUMBER_ID=your-phone-id
  ```
- [ ] (Optional) Add a test phone number in the sandbox

### Running Tests
```bash
cd backend
python -m pytest tests/unit/test_email_sender.py -v
python -m pytest tests/unit/test_whatsapp.py -v
```

---

## Appendix B: Quick Reference

### New Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SMTP_HOST` | Gmail SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `465` |
| `SMTP_SENDER_EMAIL` | Your Gmail address | `you@gmail.com` |
| `SMTP_APP_PASSWORD` | 16-char App Password | `abcd-efgh-ijkl-mnop` |
| `WHATSAPP_ACCESS_TOKEN` | Meta API token | `EAABs...` |
| `WHATSAPP_PHONE_NUMBER_ID` | Your WhatsApp number ID | `123456789` |
| `WHATSAPP_API_VERSION` | Graph API version | `v19.0` |

### New API Endpoints

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/send-email` | `{"job_id": "...", "recipient_email": "..."}` | `{"status": "sending"}` |
| POST | `/send-whatsapp` | `{"job_id": "...", "to_phone": "213..."}` | `{"status": "sending"}` |

### New Files

| File | Lines | What it does |
|------|-------|--------------|
| `services/email_sender.py` | ~160 | Gmail SMTP: build MIME message, attach PDF, send via SSL |
| `services/whatsapp.py` | ~180 | WhatsApp Cloud API: POST JSON to Meta Graph API via urllib |
| `tests/unit/test_email_sender.py` | ~140 | 10 tests: credentials, PDF, SMTP, auth errors |
| `tests/unit/test_whatsapp.py` | ~150 | 12 tests: truncation, API calls, HTTP errors |
