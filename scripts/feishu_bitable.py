#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date
from typing import Any

import requests


BASE_URL = os.environ.get("FEISHU_BASE_URL", "https://open.feishu.cn/open-apis")

FIELDS = [
    "姓名",
    "邮箱",
    "机构",
    "方向",
    "代表工作",
    "评级",
    "来源",
    "邮件主题",
    "草稿状态",
    "发送状态",
    "回复状态",
    "发现日期",
    "备注",
]


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"missing environment variable: {name}")
    return value


def normalize_email(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_name(value: Any) -> str:
    return str(value or "").strip()


def record_fields(record: dict[str, Any]) -> dict[str, Any]:
    return record.get("fields", {}) or {}


class BitableClient:
    def __init__(self) -> None:
        self.app_id = env("FEISHU_APP_ID")
        self.app_secret = env("FEISHU_APP_SECRET")
        self.app_token = env("FEISHU_APP_TOKEN")
        self.table_id = env("FEISHU_TABLE_ID")
        self._token = ""
        self._expires_at = 0.0

    def tenant_token(self) -> str:
        if self._token and time.time() < self._expires_at - 60:
            return self._token
        resp = requests.post(
            f"{BASE_URL}/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"token failed: {json.dumps(data, ensure_ascii=False)}")
        self._token = data["tenant_access_token"]
        self._expires_at = time.time() + int(data.get("expire", 7200))
        return self._token

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.tenant_token()}",
            "Content-Type": "application/json",
        }

    def list_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        page_token = None
        while True:
            params: dict[str, Any] = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token
            resp = requests.get(
                f"{BASE_URL}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records",
                headers=self.headers(),
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(f"list records failed: {json.dumps(data, ensure_ascii=False)}")
            page = data.get("data", {})
            records.extend(page.get("items", []))
            if not page.get("has_more"):
                return records
            page_token = page.get("page_token")

    def batch_create(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        created: list[dict[str, Any]] = []
        for start in range(0, len(records), 500):
            chunk = records[start : start + 500]
            resp = requests.post(
                f"{BASE_URL}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/batch_create",
                headers=self.headers(),
                json={"records": chunk},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != 0:
                raise RuntimeError(f"create records failed: {json.dumps(data, ensure_ascii=False)}")
            created.extend(data.get("data", {}).get("records", []))
        return created

    def update_record(self, record_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        resp = requests.put(
            f"{BASE_URL}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}",
            headers=self.headers(),
            json={"fields": fields},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"update record failed: {json.dumps(data, ensure_ascii=False)}")
        return data.get("data", {}).get("record", {})


def candidate_to_fields(candidate: dict[str, Any]) -> dict[str, Any]:
    fields = {key: candidate.get(key, "") for key in FIELDS}
    fields["发送状态"] = fields.get("发送状态") or "未发送"
    fields["回复状态"] = fields.get("回复状态") or "未回复"
    fields["发现日期"] = fields.get("发现日期") or date.today().isoformat()
    if fields.get("邮箱"):
        fields["草稿状态"] = fields.get("草稿状态") or "待建草稿"
    else:
        fields["草稿状态"] = fields.get("草稿状态") or "无邮箱跳过"
    return fields


def load_candidates(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("candidates"), list):
        return payload["candidates"]
    raise ValueError("candidate JSON must be a list or an object with a candidates list")


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_indexes(records: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_email: dict[str, dict[str, Any]] = {}
    by_name: dict[str, dict[str, Any]] = {}
    for record in records:
        fields = record_fields(record)
        email = normalize_email(fields.get("邮箱"))
        name = normalize_name(fields.get("姓名"))
        if email and email not in by_email:
            by_email[email] = record
        if name and name not in by_name:
            by_name[name] = record
    return by_email, by_name


def cmd_dedup(client: BitableClient, _args: argparse.Namespace) -> int:
    records = client.list_records()
    names = sorted({normalize_name(record_fields(r).get("姓名")) for r in records if normalize_name(record_fields(r).get("姓名"))})
    emails = sorted({normalize_email(record_fields(r).get("邮箱")) for r in records if normalize_email(record_fields(r).get("邮箱"))})
    print_json({"record_count": len(records), "name_count": len(names), "email_count": len(emails), "names": names, "emails": emails})
    return 0


def cmd_upsert(client: BitableClient, args: argparse.Namespace) -> int:
    candidates = load_candidates(args.file)
    existing = client.list_records()
    by_email, by_name = build_indexes(existing)
    created_payload: list[dict[str, Any]] = []
    skipped = []
    for candidate in candidates:
        fields = candidate_to_fields(candidate)
        name = normalize_name(fields.get("姓名"))
        email = normalize_email(fields.get("邮箱"))
        match = by_email.get(email) if email else None
        if not match and name:
            match = by_name.get(name)
        if match:
            skipped.append({"姓名": name, "邮箱": email, "record_id": match.get("record_id")})
            continue
        created_payload.append({"fields": fields})
    created = [] if args.dry_run else client.batch_create(created_payload)
    print_json(
        {
            "input_count": len(candidates),
            "created_count": len(created_payload),
            "skipped_duplicate_count": len(skipped),
            "dry_run": args.dry_run,
            "created_record_ids": [r.get("record_id") for r in created],
            "skipped_duplicates": skipped,
        }
    )
    return 0


def cmd_update_status(client: BitableClient, args: argparse.Namespace) -> int:
    if not args.record_id and not args.email and not args.name:
        raise ValueError("provide --record-id, --email, or --name")
    target = None
    for record in client.list_records():
        fields = record_fields(record)
        if args.record_id and record.get("record_id") == args.record_id:
            target = record
            break
        if args.email and normalize_email(fields.get("邮箱")) == normalize_email(args.email):
            target = record
            break
        if args.name and normalize_name(fields.get("姓名")) == normalize_name(args.name):
            target = record
            break
    if not target:
        raise RuntimeError("record not found")
    updates: dict[str, Any] = {}
    for field in ["发送状态", "回复状态", "草稿状态", "邮件主题", "备注"]:
        value = getattr(args, field)
        if value is not None:
            updates[field] = value
    if not updates:
        raise ValueError("no fields to update")
    updated = client.update_record(target["record_id"], updates)
    print_json({"record_id": target["record_id"], "updated_fields": updates, "record": updated})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generic AI talent tracking table client")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("dedup")
    upsert_parser = subparsers.add_parser("upsert")
    upsert_parser.add_argument("file")
    upsert_parser.add_argument("--dry-run", action="store_true")
    update_parser = subparsers.add_parser("update-status")
    update_parser.add_argument("--record-id")
    update_parser.add_argument("--email")
    update_parser.add_argument("--name")
    update_parser.add_argument("--发送状态", dest="发送状态")
    update_parser.add_argument("--回复状态", dest="回复状态")
    update_parser.add_argument("--草稿状态", dest="草稿状态")
    update_parser.add_argument("--邮件主题", dest="邮件主题")
    update_parser.add_argument("--备注", dest="备注")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    client = BitableClient()
    commands = {
        "dedup": cmd_dedup,
        "upsert": cmd_upsert,
        "update-status": cmd_update_status,
    }
    return commands[args.command](client, args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
