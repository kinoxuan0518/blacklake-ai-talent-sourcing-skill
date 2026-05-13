#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


class MailDraftError(RuntimeError):
    pass


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default or "").strip()
    if not value:
        raise MailDraftError(f"missing environment variable: {name}")
    return value


def user_db() -> Path:
    root = Path(env("ALIMAIL_APPDATA_ROOT", str(Path.home() / "Library/Application Support/alimail-standard/appdata"))).expanduser()
    return root / f"user/{env('ALIMAIL_USER_EMAIL')}/db/user.db"


def mail_db() -> Path:
    root = Path(env("ALIMAIL_APPDATA_ROOT", str(Path.home() / "Library/Application Support/alimail-standard/appdata"))).expanduser()
    return root / f"user/{env('ALIMAIL_USER_EMAIL')}/db/v1/mail.db"


def post_form(url: str, data: dict[str, str], headers: dict[str, str] | None = None) -> dict:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Language": "zh-CN",
            **(headers or {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8", "replace")
    except Exception as exc:
        raise MailDraftError(f"request failed: {url}: {exc}") from exc
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise MailDraftError(f"invalid JSON response from {url}: {payload[:200]}") from exc


def get_app_config(key: str) -> str:
    db_path = user_db()
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("select value from AppConfig where key = ?", (key,)).fetchone()
    if not row or row[0] is None:
        raise MailDraftError(f"missing AppConfig key: {key}")
    return row[0] if isinstance(row[0], str) else row[0].decode("utf-8")


def set_app_config(key: str, value: str) -> None:
    db_path = user_db()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "insert into AppConfig(key, value) values(?, ?) "
            "on conflict(key) do update set value = excluded.value",
            (key, value),
        )


def refresh_access_token() -> str:
    refresh_key = env("ALIMAIL_REFRESH_TOKEN_KEY", "RefreshToken")
    refresh_token = get_app_config(refresh_key)
    data = post_form(
        env("ALIMAIL_TOKEN_URL", "https://mailsso.mxhichina.com/oauth2/v2.0/token.json"),
        {
            "grant_type": "refresh_token",
            "client_id": env("ALIMAIL_CLIENT_ID", "alimail_standard_redcoast_mac"),
            "refresh_token": refresh_token,
        },
    )
    access_token = data.get("access_token")
    next_refresh_token = data.get("refresh_token")
    if not access_token or not next_refresh_token:
        raise MailDraftError(f"refresh token response missing fields: {sorted(data)}")
    set_app_config(refresh_key, next_refresh_token)
    return access_token


def webmail_rpc(access_token: str, path: str, data: dict[str, str]) -> dict:
    base = env("ALIMAIL_WEBMAIL_BASE", "https://qiye.aliyun.com/alimail/")
    resp = post_form(
        urllib.parse.urljoin(base, path),
        data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    status = resp.get("status")
    if status not in (None, 0, 200):
        raise MailDraftError(f"{path} failed: {resp}")
    return resp


def text_to_html(body: str) -> str:
    blocks: list[str] = []
    for raw in body.strip().splitlines():
        line = raw.strip()
        if line:
            blocks.append(f'<div style="clear: both;">{html.escape(line)}</div>')
        else:
            blocks.append('<div style="clear: both;"><br></div>')
    return '<div style="font-family: Tahoma, Arial, STHeitiSC-Light, SimSun">' + "".join(blocks) + "</div>"


def save_draft(recipient_email: str, recipient_name: str, subject: str, body: str, draft_mail_id: str | None) -> dict:
    access_token = refresh_access_token()
    used_mail_ids = [draft_mail_id] if draft_mail_id else []
    start_resp = webmail_rpc(
        access_token,
        "ajax/mail/startDraft.txt",
        {"mailIds": json.dumps(used_mail_ids, ensure_ascii=False)},
    )
    draft_session_id = start_resp.get("draftSessionId")
    if not draft_session_id:
        raise MailDraftError(f"startDraft response missing draftSessionId: {start_resp}")

    mail_json_data = {
        "to": [{"email": recipient_email, "name": recipient_name}],
        "cc": [],
        "bcc": [],
        "subject": subject,
        "body": text_to_html(body),
        "html": True,
        "saveToSendFolder": True,
        "separatedSend": False,
        "highPriority": False,
        "from": {"email": env("ALIMAIL_USER_EMAIL"), "name": env("ALIMAIL_USER_NAME")},
        "replyto": [{"email": env("ALIMAIL_USER_EMAIL"), "name": env("ALIMAIL_USER_NAME")}],
        "attachList": [],
        "bigAttachList": [],
        "resourceList": [],
        "guid": str(uuid.uuid4()),
        "draftSessionId": draft_session_id,
        "extData": {},
    }
    if draft_mail_id:
        mail_json_data["mailId"] = draft_mail_id

    save_resp = webmail_rpc(
        access_token,
        "ajax/mail/saveMail.txt",
        {"mailJsonData": json.dumps(mail_json_data, ensure_ascii=False)},
    )
    data = save_resp.get("data") or {}
    saved = data.get("data") or data
    draft_id = saved.get("mailId")
    if not draft_id:
        raise MailDraftError(f"saveMail response missing mailId: {save_resp}")
    return {"draftMailId": draft_id, "subject": subject, "recipient": recipient_email}


def verify_draft(draft_mail_id: str, recipient_email: str, subject: str, body_opening: str) -> dict | None:
    folder_id = env("ALIMAIL_DRAFT_FOLDER_ID", "5")
    sql = (
        "select itemId, `to`, subject, length(bodyHTML), bodyHTML "
        "from storage_mail where folderId = ? and itemId = ?"
    )
    with sqlite3.connect(mail_db()) as conn:
        row = conn.execute(sql, (folder_id, draft_mail_id)).fetchone()
    if not row:
        return None
    item_id, to_field, row_subject, body_len, body_html = row
    decoded = html.unescape(body_html or "")
    if recipient_email.lower() not in (to_field or "").lower():
        return None
    if row_subject != subject:
        return None
    if not body_len or body_len < 50:
        return None
    if body_opening and body_opening not in decoded:
        return None
    return {"itemId": item_id, "subject": row_subject, "bodyHTMLLength": body_len}


def main() -> int:
    parser = argparse.ArgumentParser(description="Save and optionally verify an AliMail-style draft")
    parser.add_argument("--email-json", required=True, type=Path)
    parser.add_argument("--recipient-email", required=True)
    parser.add_argument("--recipient-name", required=True)
    parser.add_argument("--draft-mail-id")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--verify-timeout", type=int, default=120)
    args = parser.parse_args()

    email_data = json.loads(args.email_json.read_text(encoding="utf-8"))
    subject = email_data["subject"].strip()
    body = email_data["body"].strip()
    result = save_draft(args.recipient_email, args.recipient_name, subject, body, args.draft_mail_id)

    if args.verify:
        first_line = body.splitlines()[0].strip() if body else ""
        deadline = time.time() + args.verify_timeout
        verification = None
        while time.time() < deadline:
            verification = verify_draft(result["draftMailId"], args.recipient_email, subject, first_line)
            if verification:
                break
            time.sleep(5)
        result["verified"] = bool(verification)
        result["verification"] = verification

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MailDraftError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
