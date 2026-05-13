# Automated Recruitment Pipeline

A production-ready prototype that automates resume intake, keyword screening, and webhook notifications for recruiter workflows. The goal is to prove Linux command-line automation, Python scripting, data parsing, and webhook/API integration skills.

## What it does

- Scans incoming PDF resumes from a folder.
- Extracts text from each PDF using a Python parser.
- Checks for required technical keywords (case-insensitive).
- Marks candidates as PASS if at least 3 required skills are found.
- Sends a webhook POST for PASS candidates to a mock Slack/Discord endpoint.
- Archives processed resumes to avoid double-processing.

## Why this saves recruiter time

- Eliminates manual resume triage by pre-filtering for core skills.
- Automates screening updates with a webhook signal.
- Keeps inboxes clean by archiving every processed resume.
- Standardizes evaluation with consistent keyword rules.

## Project structure

```
recruiter/
├─ incoming_cvs/        # Drop new PDF resumes here
├─ archived_cvs/        # Processed PDFs are moved here
├─ parser.py            # PDF parser + keyword evaluator + webhook sender
├─ run_pipeline.sh      # Bash wrapper for batch processing
├─ requirements.txt     # Python dependencies
└─ README.md
```

## Requirements

- Ubuntu 20.04+ (or any modern Linux)
- Python 3.8+
- pip

## Quick start (Ubuntu)

1. Install Python and pip:

```
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

2. Create and activate a virtual environment (recommended):

```
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```
pip install -r requirements.txt
```

4. Set your webhook URL (replace with a real Slack/Discord webhook when ready):

```
export WEBHOOK_URL="https://hooks.slack.com/services/XXX/YYY/ZZZ"
```

If you do not set `WEBHOOK_URL`, the script uses a mock URL (`https://example.com/mock-webhook`).

5. Make the pipeline script executable:

```
chmod +x run_pipeline.sh
```

6. Drop PDF resumes into `incoming_cvs/`:

```
cp /path/to/resume.pdf incoming_cvs/
```

7. Run the pipeline:

```
./run_pipeline.sh
```

## Example output

```
Processing: /path/recruiter/incoming_cvs/resume.pdf
Candidate result: PASS | Skills found: Linux, Bash, Python
Webhook sent.
Archived: /path/recruiter/incoming_cvs/resume.pdf
```

## Webhook payload

The parser posts a JSON payload like this when a candidate passes:

```
{
  "content": "\U0001F7E2 New Candidate Passed! Skills found: Linux, Bash, Python. Ready for screening."
}
```

Note: Discord accepts `content` as shown. For Slack, you can change `content` to `text` inside `parser.py`.

## Keyword rules

Default required keywords are defined in `parser.py`:

- Linux
- Bash
- Python
- English

A candidate passes when at least 3 of these skills are found in the PDF text. Adjust `REQUIRED_KEYWORDS` and `MIN_MATCHES` to match your screening policy.

## Exit codes

- `0` - PASS and webhook attempted
- `3` - FAIL (not enough keywords)
- `1` - processing error (PDF read or webhook error)
- `2` - usage error

`run_pipeline.sh` archives resumes only when the parser exits with `0` or `3`.

## Security and privacy notes

- Only keyword results are sent in the webhook message.
- Raw PDF text is not transmitted.
- Store webhook URLs in environment variables, not in code.

## Troubleshooting

- If PDFs are not being detected, confirm they are in `incoming_cvs/` and end with `.pdf`.
- If the webhook fails, verify your `WEBHOOK_URL` and network access.
- If text extraction is empty, the PDF may be scanned; consider OCR if needed.

## Next steps (optional enhancements)

- Add OCR for scanned documents.
- Store results in a database or CSV.
- Extend keyword rules per role.
- Add unit tests and CI checks.
