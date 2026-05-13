---
name: blacklake-ai-talent-sourcing
description: Run a privacy-safe daily AI talent sourcing workflow for manufacturing AI roles, including sent/reply checks, candidate deduplication, public-source sourcing, outreach draft generation, Feishu-style table updates, and AliMail-style draft persistence with local verification. Use when asked to source candidates for AI + manufacturing engineering software, CAD/CAE/CAM/PLM, multimodal, LLM, Agent, RAG, spatial reasoning, or industrial workflow automation roles.
---

# BlackLake AI Talent Sourcing

Use this skill to run a daily sourcing loop for AI talent in manufacturing engineering scenarios.

The workflow is intentionally conservative: never mark a message as sent, replied, or drafted unless there is local or API evidence. If evidence is incomplete, keep the record pending and write the uncertainty into notes.

## Sensitive Data Rule

Do not hardcode secrets, account identifiers, private paths, candidate lists, company tokens, or personal email addresses in the skill or public outputs.

Use environment variables for all credentials and machine-specific values. See [configuration.md](references/configuration.md).

## Target Profile

Prioritize candidates who combine AI/modeling capability with manufacturing engineering software scenarios:

- LLM, multimodal models, Agent systems, RAG, knowledge graphs, spatial/geometric reasoning, vision models, program generation, workflow orchestration, memory systems.
- Manufacturing or engineering software context such as CAD drawings, 2D/3D retrieval, PLM, quotation, sheet-metal estimation, CAM/toolpaths, machining-time estimation, engineering workflow digitization, AutoCAD/SolidWorks/Siemens NX frontends, or factory data workflows.

Hard gate: a candidate must show AI/model capability connected to engineering/manufacturing scenarios. Pure CAD/PLM/CAM software experience without model or intelligent-system work should be downgraded or skipped.

## Workflow

1. Load prior run memory.
   - Read the automation or project memory file if one exists.
   - Avoid repeating candidates, duplicate failures, and already-known blocked paths.

2. Check sent mail before sourcing.
   - Query the local mail database for previously tracked candidate email addresses.
   - If a sent record clearly matches recipient and subject, update the tracking table to `发送状态=已发送`.
   - Include evidence such as sent timestamp, recipient, subject, and message id in notes.

3. Check replies.
   - Pull tracked rows where `发送状态=已发送` and `回复状态=未回复`.
   - Query local inbox/all-mail for messages from that candidate after the sent timestamp.
   - Update `回复状态=已回复` only when the sender and timestamp evidence are clear.

4. Build the dedup baseline.
   - Pull all tracked names and emails from the tracking table.
   - Include local reports from recent runs as a fallback if the table is unavailable.
   - Do not use old Notion exports or private notes as the source of truth unless the user explicitly asks.

5. Source new candidates from public sources.
   - Search public sources such as papers, GitHub, project pages, personal pages, Hugging Face paper pages, conference pages, and official lab pages.
   - Produce 15 candidates per daily run.
   - Rate candidates as `★★★`, `★★`, or `★`.
   - Capture source URLs and uncertainty, especially around identity and email reliability.

6. Generate outreach drafts.
   - Use the fixed subject if the project has one; otherwise define one stable subject for the run.
   - Draft only for `★★★` and `★★` candidates with reliable public email addresses.
   - Follow [email_quality_gate.md](references/email_quality_gate.md).
   - If the preferred LLM is unavailable, write drafts manually and still apply the quality gate.

7. Save email drafts.
   - Use the mail provider API or local authenticated API, not UI paste automation.
   - Verify each saved draft against local mail storage: recipient, subject, body length, and body opening.
   - Mark `草稿状态=已存草稿` only after verification.
   - If the API returns a draft id but local verification fails, keep `草稿状态=待建草稿` and write the draft id into notes as unverified evidence.

8. Write tracking table updates.
   - Fields: `姓名`, `邮箱`, `机构`, `方向`, `代表工作`, `评级`, `来源`, `邮件主题`, `草稿状态`, `发送状态`, `回复状态`, `发现日期`, `备注`.
   - New rows default to `发送状态=未发送`, `回复状态=未回复`.
   - Candidates without reliable emails use `草稿状态=无邮箱跳过`.

9. Produce a local report.
   - Include sent backfill count, reply count, new candidates, verified drafts, unverified drafts, skipped no-email count, tracking table identifiers, and backup paths.
   - Remind the user that drafts need human review before sending.

## Evidence Standard

- Clear sent evidence: local sent folder or provider API row matching recipient and subject.
- Clear reply evidence: local inbox/all-mail or provider API row from candidate email after the sent timestamp.
- Clear draft evidence: draft folder row matching draft id or recipient, exact subject, non-empty body, and expected body opening.

When evidence is unclear, keep the status pending.

## Bundled Scripts

- `scripts/feishu_bitable.py`: generic Bitable-style table client using environment variables.
- `scripts/alimail_draft.py`: generic AliMail-style draft saver using environment variables and local verification.

Read [configuration.md](references/configuration.md) before running either script.
