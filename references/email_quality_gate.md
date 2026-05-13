# Outreach Email Quality Gate

Use this gate before writing any draft to the mail system.

## Must Pass

1. Human voice
   - The email should not read like a paper abstract, company brochure, or field merge.
   - Avoid empty phrases such as "highly aligned", "empower", "ecosystem", and "frontier exploration".

2. Open invitation
   - Do not assume the candidate is looking for a job.
   - Leave room for a technical conversation even if there is no immediate hiring intent.

3. Candidate-specific detail
   - Include at least one concrete project, research decision, engineering tradeoff, or artifact that could only come from reading the candidate's public work.

4. Real manufacturing connection
   - Connect the candidate's work to one concrete industrial scenario such as drawings, PLM, quotation, process planning, factory data, digital twins, tool use, long-horizon workflow, or industrial knowledge graphs.

5. No terminology pileup
   - Keep only the one or two technical details needed to create a real bridge.
   - Do not list multiple papers or benchmarks mechanically.

6. Subject consistency
   - If the project defines a fixed subject, use it exactly.

## Suggested Output Schema

```json
{
  "subject": "",
  "body": "",
  "quality_notes": {
    "human_voice": "",
    "candidate_specificity": "",
    "manufacturing_connection": "",
    "openness": ""
  },
  "risk_flags": []
}
```

Only save drafts that pass this gate.
