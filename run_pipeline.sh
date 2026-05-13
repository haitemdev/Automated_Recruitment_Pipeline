#!/usr/bin/env bash
# =============================================================================
#  Automated Recruitment Pipeline — Bash Wrapper
# =============================================================================
#  Author  : Recruitment Engineering Team
#  Version : 1.0.0
#  Purpose : Scans the incoming_cvs/ directory for PDF resumes, runs the
#            Python parser on each file, archives processed files with a
#            timestamp prefix, and prints a summary report.
#
#  Usage   : chmod +x run_pipeline.sh && ./run_pipeline.sh
# =============================================================================

set -euo pipefail

# ── Configuration ───────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INCOMING_DIR="${SCRIPT_DIR}/incoming_cvs"
ARCHIVE_DIR="${SCRIPT_DIR}/archived_cvs"
PARSER_SCRIPT="${SCRIPT_DIR}/parser.py"

# ── ANSI Colors ─────────────────────────────────────────────────────────────
GREEN="\033[92m"
RED="\033[91m"
YELLOW="\033[93m"
CYAN="\033[96m"
BOLD="\033[1m"
DIM="\033[2m"
RESET="\033[0m"

# ── Banner ──────────────────────────────────────────────────────────────────
echo -e ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}${BOLD}║     RECRUITMENT PIPELINE — Batch Processor v1.0     ║${RESET}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════╝${RESET}"
echo -e ""

# ── Preflight Checks ───────────────────────────────────────────────────────
# Verify the Python parser script exists
if [[ ! -f "${PARSER_SCRIPT}" ]]; then
    echo -e "${RED}[ERROR]${RESET} Parser script not found: ${PARSER_SCRIPT}"
    echo -e "${DIM}        Ensure parser.py is in the same directory as this script.${RESET}"
    exit 1
fi

# Verify Python 3 is available
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[ERROR]${RESET} python3 is not installed or not in PATH."
    exit 1
fi

# Create directories if they don't exist
mkdir -p "${INCOMING_DIR}"
mkdir -p "${ARCHIVE_DIR}"

echo -e "${CYAN}[INFO]${RESET}  Incoming directory : ${INCOMING_DIR}"
echo -e "${CYAN}[INFO]${RESET}  Archive directory  : ${ARCHIVE_DIR}"
echo -e ""

# ── Scan for PDFs ──────────────────────────────────────────────────────────
# Use a safe globbing approach
shopt -s nullglob
PDF_FILES=("${INCOMING_DIR}"/*.pdf)
shopt -u nullglob

TOTAL=${#PDF_FILES[@]}

if [[ ${TOTAL} -eq 0 ]]; then
    echo -e "${YELLOW}[WARN]${RESET}  No PDF files found in ${INCOMING_DIR}/"
    echo -e "${DIM}        Drop .pdf resumes into incoming_cvs/ and re-run.${RESET}"
    echo -e ""
    exit 0
fi

echo -e "${CYAN}[INFO]${RESET}  Found ${BOLD}${TOTAL}${RESET} PDF file(s) to process."
echo -e "${DIM}────────────────────────────────────────────────────────${RESET}"
echo -e ""

# ── Processing Loop ────────────────────────────────────────────────────────
PASSED=0
FAILED=0
ERRORS=0
COUNT=0

for pdf_file in "${PDF_FILES[@]}"; do
    COUNT=$((COUNT + 1))
    filename="$(basename "${pdf_file}")"

    echo -e "${CYAN}${BOLD}[${COUNT}/${TOTAL}]${RESET} Processing: ${BOLD}${filename}${RESET}"
    echo -e "${DIM}─────────────────────────────────────────────${RESET}"

    # Run the parser and capture exit code
    set +e
    python3 "${PARSER_SCRIPT}" "${pdf_file}"
    EXIT_CODE=$?
    set -e

    # Interpret the exit code
    case ${EXIT_CODE} in
        0)
            PASSED=$((PASSED + 1))
            ;;
        1)
            FAILED=$((FAILED + 1))
            ;;
        *)
            ERRORS=$((ERRORS + 1))
            echo -e "${RED}[ERROR]${RESET} Parser returned exit code ${EXIT_CODE} for ${filename}"
            ;;
    esac

    # Archive the processed file with a timestamp prefix
    TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
    ARCHIVE_NAME="${TIMESTAMP}_${filename}"
    mv "${pdf_file}" "${ARCHIVE_DIR}/${ARCHIVE_NAME}"
    echo -e "${GREEN}[OK]${RESET}   Archived → ${DIM}archived_cvs/${ARCHIVE_NAME}${RESET}"
    echo -e ""

    # Small delay between files to avoid webhook rate limiting
    sleep 1
done

# ── Summary Report ──────────────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}${BOLD}║               PIPELINE SUMMARY REPORT                ║${RESET}"
echo -e "${CYAN}${BOLD}╠══════════════════════════════════════════════════════╣${RESET}"
echo -e "${CYAN}║${RESET}  📁 Total processed  : ${BOLD}${TOTAL}${RESET}                            ${CYAN}║${RESET}"
echo -e "${CYAN}║${RESET}  ${GREEN}✅ Passed${RESET}           : ${GREEN}${BOLD}${PASSED}${RESET}                            ${CYAN}║${RESET}"
echo -e "${CYAN}║${RESET}  ${RED}❌ Failed${RESET}           : ${RED}${BOLD}${FAILED}${RESET}                            ${CYAN}║${RESET}"
echo -e "${CYAN}║${RESET}  ${YELLOW}⚠️  Errors${RESET}           : ${YELLOW}${BOLD}${ERRORS}${RESET}                            ${CYAN}║${RESET}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════╝${RESET}"
echo -e ""
echo -e "${DIM}Pipeline completed at $(date '+%Y-%m-%d %H:%M:%S')${RESET}"
echo -e ""
