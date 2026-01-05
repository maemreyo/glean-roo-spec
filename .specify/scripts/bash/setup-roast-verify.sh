#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
REPORT_ARG=""
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) 
            JSON_MODE=true 
            ;;
        --report=*)
            REPORT_ARG="${arg#*=}"
            ;;
        --help|-h) 
            echo "Usage: $0 [--json] [--report=path/to/report.md]"
            echo "  --json      Output results in JSON format"
            echo "  --report    Specify a specific roast report file"
            echo "  --help      Show this help message"
            exit 0 
            ;;
        *) 
            ARGS+=("$arg") 
            ;;
    esac
done

# Get script directory and load common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get all paths and variables from common functions
eval $(get_feature_paths)

# Check if we're on a proper feature branch (only for git repos)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

DOCS_DIR="$REPO_ROOT/docs/roasts"

# Determine Report File
if [[ -n "$REPORT_ARG" ]]; then
    if [[ -f "$REPORT_ARG" ]]; then
        REPORT_FILE="$REPORT_ARG"
    elif [[ -f "$REPO_ROOT/$REPORT_ARG" ]]; then
        REPORT_FILE="$REPO_ROOT/$REPORT_ARG"
    else
        echo "Error: Specified report file not found: $REPORT_ARG" >&2
        exit 1
    fi
else
    # Find the latest roast report for the current branch
    # Assumes format: roast-report-[branch]-YYYY-MM-DD-HHMM.md
    REPORT_FILE=$(find "$DOCS_DIR" -maxdepth 1 -name "roast-report-${CURRENT_BRANCH}-*.md" | sort -r | head -n 1)
    
    if [[ -z "$REPORT_FILE" ]]; then
        echo "Error: No roast report found for branch $CURRENT_BRANCH in $DOCS_DIR" >&2
        exit 1
    fi
fi

# Output results
if $JSON_MODE; then
    printf '{"REPORT_FILE":"%s","TASKS":"%s","BRANCH":"%s"}\n' \
        "$REPORT_FILE" "$TASKS" "$CURRENT_BRANCH"
else
    echo "REPORT_FILE: $REPORT_FILE"
    echo "TASKS: $TASKS"
    echo "BRANCH: $CURRENT_BRANCH"
fi
