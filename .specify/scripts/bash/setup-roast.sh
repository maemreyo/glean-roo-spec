#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) 
            JSON_MODE=true 
            ;;
        --help|-h) 
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
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

# Handle optional feature directory argument
if [[ ${#ARGS[@]} -gt 0 ]]; then
    FEATURE_ARG="${ARGS[0]}"
    if [[ -d "$FEATURE_ARG" ]]; then
        # Resolve absolute path
        FEATURE_DIR="$(cd "$FEATURE_ARG" && pwd)"
        echo "Using specified feature directory: $FEATURE_DIR"
        
        # Override derived paths
        FEATURE_SPEC="$FEATURE_DIR/spec.md"
        IMPL_PLAN="$FEATURE_DIR/plan.md"
        TASKS="$FEATURE_DIR/tasks.md"
        
        # We might not be on the branch matching this folder, so extract name from folder
        FEATURE_NAME=$(basename "$FEATURE_DIR")
    elif [[ -d "$REPO_ROOT/$FEATURE_ARG" ]]; then
        FEATURE_DIR="$(cd "$REPO_ROOT/$FEATURE_ARG" && pwd)"
        echo "Using specified feature directory: $FEATURE_DIR"
        
        FEATURE_SPEC="$FEATURE_DIR/spec.md"
        IMPL_PLAN="$FEATURE_DIR/plan.md"
        TASKS="$FEATURE_DIR/tasks.md"
        
        FEATURE_NAME=$(basename "$FEATURE_DIR")
    else
        echo "Error: Directory '$FEATURE_ARG' not found."
        exit 1
    fi
else
    FEATURE_NAME="$CURRENT_BRANCH"
fi

# Check if we're on a proper feature branch (only for git repos)
# If explicit feature dir provided, skip branch check or warn?
if [[ ${#ARGS[@]} -eq 0 ]]; then
    check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1
fi

# Ensure the roast directory exists INSIDE the feature spec folder
DOCS_DIR="$FEATURE_DIR/roasts"
mkdir -p "$DOCS_DIR"

# Define Report Path
DATE_STR=$(date +%Y-%m-%d-%H%M)
REPORT_FILE="$DOCS_DIR/roast-report-${FEATURE_NAME}-${DATE_STR}.md"

# Copy template if it exists
TEMPLATE="$REPO_ROOT/.specify/templates/roast-template.md"
if [[ -f "$TEMPLATE" ]]; then
    # Start fresh for a new roast or append? 
    # User said "update a file report after each subtask review", implying we need a stable file during the run.
    # But usually a roast is a session. Let's create a fresh one if it doesn't exist, or overwrite if it's the same day?
    # User said "update a file report".
    
    # Let's overwrite to ensure a fresh session start, OR we rely on the agent to append.
    # But strictly following `setup-plan.sh`, we cp.
    cp "$TEMPLATE" "$REPORT_FILE"
    echo "Initialized Roast Report at $REPORT_FILE"
else
    echo "Warning: Roast template not found at $TEMPLATE"
    touch "$REPORT_FILE"
fi

# Output results
if $JSON_MODE; then
    printf '{"REPORT_FILE":"%s","TASKS":"%s","IMPL_PLAN":"%s","BRANCH":"%s"}\n' \
        "$REPORT_FILE" "$TASKS" "$IMPL_PLAN" "$CURRENT_BRANCH"
else
    echo "REPORT_FILE: $REPORT_FILE"
    echo "TASKS: $TASKS"
    echo "IMPL_PLAN: $IMPL_PLAN" 
    echo "BRANCH: $CURRENT_BRANCH"
fi
