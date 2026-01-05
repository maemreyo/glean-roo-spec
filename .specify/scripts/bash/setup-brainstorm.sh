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
            echo "Usage: $0 [--json] [feature-dir]"
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
IS_FEATURE_SPECIFIC=false

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
        
        FEATURE_NAME=$(basename "$FEATURE_DIR")
        IS_FEATURE_SPECIFIC=true
    elif [[ -d "$REPO_ROOT/$FEATURE_ARG" ]]; then
        FEATURE_DIR="$(cd "$REPO_ROOT/$FEATURE_ARG" && pwd)"
        echo "Using specified feature directory: $FEATURE_DIR"
        
        FEATURE_SPEC="$FEATURE_DIR/spec.md"
        IMPL_PLAN="$FEATURE_DIR/plan.md"
        TASKS="$FEATURE_DIR/tasks.md"
        
        FEATURE_NAME=$(basename "$FEATURE_DIR")
        IS_FEATURE_SPECIFIC=true
    else
        echo "Error: Directory '$FEATURE_ARG' not found."
        exit 1
    fi
else
    # If no argument, but we are on a valid feature branch (and not main), use it?
    # Or default to global if no arg is explicit?
    # Let's check if CURRENT_BRANCH looks like a feature branch
    if [[ "$CURRENT_BRANCH" =~ ^[0-9]{3}- ]]; then
         FEATURE_NAME="$CURRENT_BRANCH"
         IS_FEATURE_SPECIFIC=true
    else
         # Fallback to global brainstorming if on main and no arg
         FEATURE_NAME="global"
    fi
fi

# Determine Output Directory and File
DATE_STR=$(date +%Y-%m-%d-%H%M)

if $IS_FEATURE_SPECIFIC; then
    # Save to the feature directory
    BRAINSTORM_DIR="$FEATURE_DIR/brainstorms"
    # Fallback to feature name if needed
    NAME_TAG="$FEATURE_NAME"
else
    # Save to global docs
    BRAINSTORM_DIR="$REPO_ROOT/docs/brainstorms"
    NAME_TAG="global"
fi

mkdir -p "$BRAINSTORM_DIR"
OUTPUT_FILE="$BRAINSTORM_DIR/brainstorm-${NAME_TAG}-${DATE_STR}.md"

# Use Template if available
TEMPLATE="$REPO_ROOT/.specify/templates/brainstorm-template.md"
if [[ -f "$TEMPLATE" ]]; then
    cp "$TEMPLATE" "$OUTPUT_FILE"
    # Replace placeholders
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # MacOS sed
        sed -i '' "s/{{DATE}}/$DATE_STR/g" "$OUTPUT_FILE"
        sed -i '' "s/{{FEATURE}}/$NAME_TAG/g" "$OUTPUT_FILE"
    else
        # Linux sed
        sed -i "s/{{DATE}}/$DATE_STR/g" "$OUTPUT_FILE"
        sed -i "s/{{FEATURE}}/$NAME_TAG/g" "$OUTPUT_FILE"
    fi
else
    # Fallback to empty file if template missing
    touch "$OUTPUT_FILE"
fi

# Output results
if $JSON_MODE; then
    printf '{"OUTPUT_FILE":"%s","FEATURE_SPEC":"%s","IMPL_PLAN":"%s","TASKS":"%s","FEATURE_DIR":"%s","BRANCH":"%s"}\n' \
        "$OUTPUT_FILE" "$FEATURE_SPEC" "$IMPL_PLAN" "$TASKS" "$FEATURE_DIR" "$CURRENT_BRANCH"
else
    echo "OUTPUT_FILE: $OUTPUT_FILE"
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "IMPL_PLAN: $IMPL_PLAN" 
    echo "TASKS: $TASKS"
fi
