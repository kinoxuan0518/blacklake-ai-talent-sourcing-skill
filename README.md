# AI Talent Sourcing Skill

A privacy-safe Codex skill for running a daily AI talent sourcing workflow in manufacturing engineering software scenarios.

The skill is designed for roles at the intersection of:

- LLMs, multimodal models, Agents, RAG, knowledge graphs, spatial reasoning, vision models, program generation, workflow orchestration, or memory systems.
- CAD/CAE/CAM/PLM, engineering drawings, 2D/3D retrieval, quotation, process planning, sheet-metal estimation, toolpath generation, machining-time estimation, and manufacturing R&D workflows.

The core rule is conservative evidence handling: never mark outreach as sent, replied, or drafted unless there is local or API evidence.

## What It Does

- Checks sent mail and backfills confirmed `发送状态=已发送`.
- Checks candidate replies and backfills confirmed `回复状态=已回复`.
- Builds a dedup baseline from a tracking table and local run reports.
- Sources 15 public-source candidates per daily run.
- Rates candidates as `★★★`, `★★`, or `★`.
- Generates personalized outreach drafts for high-priority candidates with reliable public email addresses.
- Saves drafts through a mail API and verifies them against local mail storage before marking them as saved.
- Writes a local report with counts, evidence, uncertainty, and next actions.

## Repository Layout

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── configuration.md
│   └── email_quality_gate.md
└── scripts/
    ├── alimail_draft.py
    └── feishu_bitable.py
```

## Installation

Clone or copy this folder into your Codex skills directory:

```bash
mkdir -p "$CODEX_HOME/skills"
git clone https://github.com/kinoxuan0518/blacklake-ai-talent-sourcing-skill \
  "$CODEX_HOME/skills/blacklake-ai-talent-sourcing"
```

Then invoke it in Codex with:

```text
Use $blacklake-ai-talent-sourcing to run today’s manufacturing AI talent sourcing workflow.
```

## Configuration

All secrets and machine-specific values must be provided through environment variables. Do not hardcode tokens, table ids, personal email addresses, or local database paths.

Tracking table:

```bash
export FEISHU_APP_ID="..."
export FEISHU_APP_SECRET="..."
export FEISHU_APP_TOKEN="..."
export FEISHU_TABLE_ID="..."
```

Mail drafts:

```bash
export ALIMAIL_USER_EMAIL="..."
export ALIMAIL_USER_NAME="..."
export ALIMAIL_APPDATA_ROOT="$HOME/Library/Application Support/alimail-standard/appdata"
```

See [references/configuration.md](references/configuration.md) for the full list of required and optional settings.

## Script Usage

Check the tracking table dedup baseline:

```bash
python3 scripts/feishu_bitable.py dedup
```

Upsert candidates from a JSON file:

```bash
python3 scripts/feishu_bitable.py upsert candidates.json
```

Update a candidate status by email:

```bash
python3 scripts/feishu_bitable.py update-status \
  --email "candidate@example.com" \
  --发送状态 "已发送" \
  --备注 "local sent-mail evidence"
```

Save and verify a draft:

```bash
python3 scripts/alimail_draft.py \
  --email-json draft.json \
  --recipient-email "candidate@example.com" \
  --recipient-name "Candidate Name" \
  --verify
```

The draft JSON should use:

```json
{
  "subject": "Your subject",
  "body": "Your plain text email body"
}
```

## Candidate JSON Shape

```json
[
  {
    "姓名": "Candidate Name",
    "邮箱": "candidate@example.com",
    "机构": "Institution or company",
    "方向": "LLM + manufacturing engineering scenario",
    "代表工作": "Representative public work",
    "评级": "★★★",
    "来源": "Public source URLs",
    "邮件主题": "Outreach subject",
    "草稿状态": "待建草稿",
    "发送状态": "未发送",
    "回复状态": "未回复",
    "发现日期": "YYYY-MM-DD",
    "备注": "Evidence, uncertainty, or verification notes"
  }
]
```

## Safety Rules

- Use only public candidate sources unless the user explicitly provides another data source.
- Do not publish private candidate data, outreach logs, tokens, local paths, or account identifiers.
- Keep uncertain records pending instead of forcing a successful status.
- If a mail API returns a draft id but local verification fails, keep `草稿状态=待建草稿` and record the draft id as unverified evidence.
- Human review is required before sending outreach drafts.

## Privacy Scan Before Publishing

Run a scan like this before pushing changes:

```bash
rg -n --hidden --glob '!.git/**' \
  '(gho_|github_pat_|tenant_access_token|refresh_token|APP_SECRET|/Users/|draftMailId=|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})' .
```

Expected results should contain only placeholders, environment variable names, or documented example values.
