#!/usr/bin/env python3
"""
=============================================================================
  Automated Recruitment Pipeline — CV/Resume Parser
=============================================================================
  Author  : Recruitment Engineering Team
  Version : 1.0.0
  Purpose : Parses a PDF resume, matches technical keywords against a
            configurable checklist, and notifies recruiters via webhook
            when a candidate passes the screening threshold.

  Exit Codes:
      0 — Candidate PASSED keyword screening
      1 — Candidate FAILED keyword screening
      2 — Runtime error (file not found, parse failure, bad arguments)
=============================================================================
"""

import sys
import os
import json
import datetime

try:
    import pdfplumber
except ImportError:
    print("\033[91m[ERROR]\033[0m pdfplumber is not installed.")
    print("       Run: pip install pdfplumber")
    sys.exit(2)

try:
    import requests
except ImportError:
    print("\033[91m[ERROR]\033[0m requests is not installed.")
    print("       Run: pip install requests")
    sys.exit(2)


# =============================================================================
#  CONFIGURATION — Adjust these values to match the target job role
# =============================================================================

# Technical keywords to search for (all lowercase)
REQUIRED_KEYWORDS = [
    "linux",
    "bash",
    "python",
    "english",
    "networking",
    "docker",
    "git",
    "ssh",
    "automation",
    "scripting",
]

# Minimum number of keywords a candidate must match to pass
PASS_THRESHOLD = 3

# Discord / Slack Webhook URL
# Replace with your actual webhook endpoint
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"


# =============================================================================
#  ANSI COLOR HELPERS
# =============================================================================

class Color:
    """ANSI escape codes for colored terminal output."""
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RESET  = "\033[0m"


def print_banner():
    """Print a styled banner to the terminal."""
    print(f"""
{Color.CYAN}{Color.BOLD}╔══════════════════════════════════════════════════════╗
║        AUTOMATED RECRUITMENT PIPELINE v1.0           ║
║              CV / Resume Scanner                     ║
╚══════════════════════════════════════════════════════╝{Color.RESET}
""")


def print_result_box(filename, status, matched, total_keywords):
    """Print a formatted result box for a single candidate."""
    if status == "PASS":
        color = Color.GREEN
        icon = "✅"
        label = "PASSED"
    else:
        color = Color.RED
        icon = "❌"
        label = "FAILED"

    matched_str = ", ".join(matched) if matched else "None"

    print(f"{color}{Color.BOLD}┌─────────────────────────────────────────────────┐{Color.RESET}")
    print(f"{color}{Color.BOLD}│  {icon}  RESULT: {label:<39} │{Color.RESET}")
    print(f"{color}{Color.BOLD}├─────────────────────────────────────────────────┤{Color.RESET}")
    print(f"{color}│  📄 File     : {filename:<33}│{Color.RESET}")
    print(f"{color}│  🔍 Matched  : {len(matched)}/{total_keywords} keywords{' ' * (24 - len(str(len(matched))) - len(str(total_keywords)))}│{Color.RESET}")
    print(f"{color}│  🛠️  Skills   : {matched_str:<32}│{Color.RESET}")
    print(f"{color}{Color.BOLD}└─────────────────────────────────────────────────┘{Color.RESET}")
    print()


# =============================================================================
#  CORE FUNCTIONS
# =============================================================================

def extract_text_from_pdf(filepath):
    """
    Extract all text content from a PDF file using pdfplumber.

    Args:
        filepath (str): Absolute or relative path to the PDF file.

    Returns:
        str: The concatenated text from all pages of the PDF.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        Exception: If pdfplumber cannot parse the file.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    extracted_text = ""

    with pdfplumber.open(filepath) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text + "\n"
            else:
                print(f"{Color.YELLOW}[WARN]{Color.RESET} Page {page_number}: No extractable text found.")

    if not extracted_text.strip():
        print(f"{Color.YELLOW}[WARN]{Color.RESET} The PDF appears to contain no extractable text.")
        print(f"{Color.DIM}       This may be a scanned/image-based PDF.{Color.RESET}")

    return extracted_text


def match_keywords(text, keywords):
    """
    Perform case-insensitive keyword matching against extracted text.

    Args:
        text     (str):  The full text extracted from the resume.
        keywords (list): A list of lowercase keyword strings to search for.

    Returns:
        list: Keywords that were found in the text.
    """
    text_lower = text.lower()
    matched = [kw for kw in keywords if kw in text_lower]
    return matched


def send_webhook_notification(filename, matched_keywords):
    """
    Send a formatted notification to a Discord/Slack webhook.

    Args:
        filename         (str):  Name of the processed PDF file.
        matched_keywords (list): List of keywords the candidate matched.

    Returns:
        bool: True if the webhook was sent successfully, False otherwise.
    """
    if "YOUR_WEBHOOK" in WEBHOOK_URL:
        print(f"{Color.YELLOW}[WARN]{Color.RESET} Webhook URL is not configured — skipping notification.")
        print(f"{Color.DIM}       Edit WEBHOOK_URL in parser.py to enable notifications.{Color.RESET}")
        return False

    skills_list = ", ".join(kw.capitalize() for kw in matched_keywords)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "content": (
            f"🟢 **New Candidate Passed!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📄 **File:** `{filename}`\n"
            f"🛠️ **Skills found:** {skills_list}\n"
            f"📊 **Match count:** {len(matched_keywords)} / {len(REQUIRED_KEYWORDS)}\n"
            f"🕐 **Scanned at:** {timestamp}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ **Ready for screening.**"
        )
    }

    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code in (200, 204):
            print(f"{Color.GREEN}[OK]{Color.RESET}   Webhook notification sent successfully.")
            return True
        else:
            print(f"{Color.RED}[ERROR]{Color.RESET} Webhook returned HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"{Color.RED}[ERROR]{Color.RESET} Webhook request failed: {e}")
        return False


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================

def main():
    """Main execution flow for the CV parser."""
    print_banner()

    # ── Validate CLI arguments ──────────────────────────────────────────
    if len(sys.argv) != 2:
        print(f"{Color.RED}[ERROR]{Color.RESET} Usage: python parser.py <path_to_resume.pdf>")
        print(f"{Color.DIM}        Example: python parser.py incoming_cvs/john_doe.pdf{Color.RESET}")
        sys.exit(2)

    filepath = sys.argv[1]
    filename = os.path.basename(filepath)

    # ── Validate file exists and is a PDF ───────────────────────────────
    if not os.path.isfile(filepath):
        print(f"{Color.RED}[ERROR]{Color.RESET} File not found: {filepath}")
        sys.exit(2)

    if not filepath.lower().endswith(".pdf"):
        print(f"{Color.RED}[ERROR]{Color.RESET} File is not a PDF: {filepath}")
        sys.exit(2)

    print(f"{Color.CYAN}[INFO]{Color.RESET}  Processing: {Color.BOLD}{filename}{Color.RESET}")
    print(f"{Color.DIM}        Path: {filepath}{Color.RESET}")
    print()

    # ── Extract text from the PDF ───────────────────────────────────────
    try:
        text = extract_text_from_pdf(filepath)
    except FileNotFoundError as e:
        print(f"{Color.RED}[ERROR]{Color.RESET} {e}")
        sys.exit(2)
    except Exception as e:
        print(f"{Color.RED}[ERROR]{Color.RESET} Failed to parse PDF: {e}")
        sys.exit(2)

    # ── Match keywords ──────────────────────────────────────────────────
    matched = match_keywords(text, REQUIRED_KEYWORDS)

    print(f"{Color.CYAN}[INFO]{Color.RESET}  Keywords checked: {len(REQUIRED_KEYWORDS)}")
    print(f"{Color.CYAN}[INFO]{Color.RESET}  Keywords matched: {len(matched)}")
    print(f"{Color.CYAN}[INFO]{Color.RESET}  Pass threshold : {PASS_THRESHOLD}")
    print()

    # ── Determine result ────────────────────────────────────────────────
    if len(matched) >= PASS_THRESHOLD:
        status = "PASS"
        print_result_box(filename, status, matched, len(REQUIRED_KEYWORDS))

        # Send webhook notification for passing candidates
        send_webhook_notification(filename, matched)

        sys.exit(0)
    else:
        status = "FAIL"
        print_result_box(filename, status, matched, len(REQUIRED_KEYWORDS))
        sys.exit(1)


if __name__ == "__main__":
    main()
