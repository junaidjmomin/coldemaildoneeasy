from __future__ import annotations

import base64
from email.message import EmailMessage
from pathlib import Path


SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def get_gmail_service(client_secret_path: Path, token_path: Path):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Gmail dependencies are missing. Run: pip install -r requirements.txt"
        ) from exc

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secret_path.exists():
                raise FileNotFoundError(
                    f"Gmail OAuth client secret not found: {client_secret_path}. "
                    "Download a desktop OAuth client JSON from Google Cloud."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def create_gmail_draft(service, *, to: str, subject: str, body: str) -> dict:
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    payload = {"message": {"raw": raw}}
    return service.users().drafts().create(userId="me", body=payload).execute()
