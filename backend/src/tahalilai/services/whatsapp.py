"""WhatsApp messaging service via Meta Cloud API.

Sends analysis summaries to patients through WhatsApp Business.
Uses only Python's built-in ``urllib.request`` — no extra packages needed.

How the WhatsApp Cloud API works (simplified):
  1. You register a WhatsApp Business app on Meta's developer portal.
  2. Meta gives you two things:
     - Phone Number ID: identifies YOUR WhatsApp Business number
     - Access Token:    proves you're authorized to send from that number
  3. To send a message, you POST a JSON payload to:
     https://graph.facebook.com/v19.0/{phone_number_id}/messages
  4. Meta's servers deliver the message to the recipient's WhatsApp.
  5. The API responds with a message ID (``wamid.xxx``) confirming delivery.

Setup steps:
  1. Create a Meta Developer account at https://developers.facebook.com
  2. Create a new Business app > Add the WhatsApp product
  3. Go to WhatsApp > API Setup to find your credentials
  4. Add them to .env as WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID
"""

from __future__ import annotations

import json                    # For building/parsing JSON payloads
import urllib.error            # HTTP error handling
import urllib.request          # Python's built-in HTTP client

from tahalilai.config import get_settings

# WhatsApp text messages have a hard limit of 4096 characters.
# If the analysis is longer, we truncate and add "..." at the end.
_MAX_MESSAGE_LENGTH = 4096


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def send_whatsapp_message(
    to_phone: str,
    message_text: str,
) -> dict[str, str]:
    """Send a text message via WhatsApp Cloud API.

    Args:
        to_phone: Recipient phone number in international format.
            Digits only, no '+' prefix (e.g. ``"213XXXXXXXXX"``).
        message_text: Message body. Truncated to 4096 chars if longer.

    Returns:
        ``{"status": "sent", "message_id": "wamid.xxx"}`` on success, or
        ``{"status": "error", "message": "..."}`` on failure.
    """
    settings = get_settings()

    # ── Guard: credentials must be set in .env ──
    if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
        return {
            "status": "error",
            "message": (
                "WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID "
                "must be set in .env"
            ),
        }

    # The JSON payload that Meta's API expects for a text message.
    # "messaging_product": "whatsapp" is required by Meta to route correctly.
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": _truncate_message(message_text)},
    }

    return _call_messages_api(settings, payload)


def send_whatsapp_document(
    to_phone: str,
    document_url: str,
    filename: str = "report.pdf",
    caption: str = "",
) -> dict[str, str]:
    """Send a document (e.g. PDF) via WhatsApp Cloud API.

    The document must be at a **public HTTPS URL** that Meta's servers
    can download. For local development, you'd need a tool like ngrok
    to expose your localhost, or upload the file to cloud storage first.

    Args:
        to_phone: Recipient phone (international format, digits only).
        document_url: Public HTTPS URL of the document.
        filename: Display name in the WhatsApp chat.
        caption: Optional caption text (max 1024 chars).

    Returns:
        ``{"status": "sent", "message_id": "wamid.xxx"}`` on success, or
        ``{"status": "error", "message": "..."}`` on failure.
    """
    settings = get_settings()

    if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
        return {
            "status": "error",
            "message": (
                "WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID "
                "must be set in .env"
            ),
        }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "document",
        "document": {
            "link": document_url,
            "filename": filename,
            "caption": caption[:1024] if caption else "",
        },
    }

    return _call_messages_api(settings, payload)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _truncate_message(text: str) -> str:
    """Truncate text to WhatsApp's 4096-character limit.

    If the text is short enough, return it unchanged.
    If it's too long, cut it and append "..." so the patient knows
    the message was trimmed.
    """
    if len(text) <= _MAX_MESSAGE_LENGTH:
        return text
    return text[: _MAX_MESSAGE_LENGTH - 3] + "..."


def _call_messages_api(settings, payload: dict) -> dict[str, str]:
    """POST a JSON payload to the WhatsApp Cloud API messages endpoint.

    This function uses ``urllib.request`` (Python's built-in HTTP client)
    instead of the popular ``requests`` library. Here's what each part does:

    1. Build the URL: ``https://graph.facebook.com/v19.0/{phone_id}/messages``
    2. Encode the payload dict as JSON bytes (APIs expect bytes, not strings)
    3. Create a Request object with:
       - The URL
       - The JSON body
       - Headers: Authorization (Bearer token) + Content-Type (JSON)
       - Method: POST
    4. Send it with ``urlopen()`` and read the response
    """
    url = (
        f"https://graph.facebook.com/{settings.whatsapp_api_version}"
        f"/{settings.whatsapp_phone_number_id}/messages"
    )

    # json.dumps() converts a Python dict to a JSON string.
    # .encode("utf-8") converts the string to bytes (HTTP sends bytes).
    data = json.dumps(payload).encode("utf-8")

    # HTTP headers tell the server what we're sending and who we are.
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }

    # urllib.request.Request = an HTTP request object (not sent yet)
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        # urlopen() actually sends the request and waits for a response.
        # ``with`` ensures the connection is closed afterward.
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        message_id = _extract_message_id(body)
        print(f"WhatsApp message sent: {message_id}")
        return {"status": "sent", "message_id": message_id}

    except urllib.error.HTTPError as exc:
        # The server returned an error (400, 401, 403, etc.)
        # We read the error body to get Meta's human-readable error message.
        error_body = exc.read().decode("utf-8", errors="replace")
        error_detail = _parse_api_error(error_body)
        return {"status": "error", "message": f"WhatsApp API error: {error_detail}"}

    except Exception as exc:
        # Network timeout, DNS failure, etc.
        return {"status": "error", "message": f"Failed to send WhatsApp message: {exc}"}


def _extract_message_id(response_body: dict) -> str:
    """Pull the message ID (``wamid.xxx``) from the API success response.

    Meta's success response looks like:
    ``{"messages": [{"id": "wamid.HBgLMjEzNTU1..."}]}``
    """
    try:
        return response_body["messages"][0]["id"]
    except (KeyError, IndexError):
        return "unknown"


def _parse_api_error(raw: str) -> str:
    """Extract a human-readable error from Meta's error response.

    Meta's error response looks like:
    ``{"error": {"message": "Invalid OAuth access token.", "type": "OAuthException"}}``
    """
    try:
        data = json.loads(raw)
        error = data.get("error", {})
        return error.get("message", raw)
    except (json.JSONDecodeError, AttributeError):
        return raw
