---
description: Turn accepted brainstorm ideas into a concrete feature specification.
handoffs:
  - label: Review Spec
    agent: zo.clarify
    prompt: Review this new specification.
---

## User Input

```text
$ARGUMENTS
```

**Context**: The user wants to convert specific ideas from a brainstorming session into a full Feature Specification.
**Format**: `$ARGUMENTS` typically contains "all" or specific idea IDs (e.g., "1, 3") and optionally a brainstorm file path.

## Outline

### 1. Context Loading

1.  Run the setup script to find the brainstorm file:
    ```bash
    .specify/scripts/bash/setup-specify-idea.sh --json $ARGUMENTS
    ```
2.  Parse JSON output to get `BRAINSTORM_FILE` and `SPEC_TEMPLATE`.
3.  **Read the content** of `BRAINSTORM_FILE` and `SPEC_TEMPLATE`.

### 2. Idea Extraction & Synthesis

1.  **Parse Selection**: Analyze `$ARGUMENTS` to determine which ideas to select:
    *   If "all" or empty: Select ALL ideas marked as "Accepted" or specifically documented in the file.
    *   If numbers (e.g., "1, 2"): Select only the ideas matching those IDs in the session log.
    
2.  **Synthesize Feature Description**:
    *   Construct a comprehensive "Feature Description" string by combining the `Title`, `Benefit`, and `Proposal` of all selected ideas.
    *   *Virtual Prompt*: "Implement [Idea 1] and [Idea 2]. [Idea 1 Details]. [Idea 2 Details]. The goal is [Combined Benefits]."
    *   **Treat this synthesized description exactly as you would the user input in `/zo.specify`.**

### 3. Feature Initialization (Strict Protocol)

Given the synthesized feature description:

1.  **Generate a concise short name** (2-4 words) for the branch (e.g., "idea-name", "feature-set").

2.  **Create Branch**:
    *   Run `.specify/scripts/bash/create-feature-from-idea.sh --json --short-name "short-name" "Synthesized Description"`
    *   Parse JSON output to get `BRANCH_NAME` and `SPEC_FILE`.

### 4. Specification Generation

1.  **Drafting**: Write the specification to `SPEC_FILE`.
    *   **IMPORTANT**: The file is already initialized with `spec-from-idea.md`.
    *   Replace `[FEATURE NAME]` with a descriptive title covering the selected ideas.
    *   Replace `[FEATURE BRANCH]` with `BRANCH_NAME`.
    *   Replace `[DATE]` with today's date.
    *   **Source Context**: `Brainstorm: [BRAINSTORM_FILE] (Ideas: [Selected IDs])`
    *   **User Stories**: Convert each idea's "Proposal" into prioritized User Stories.
    *   **Requirements**: Derive functional requirements from the detailed proposal text.
    *   **Success Criteria**: Derive measurable outcomes from the "Benefit" sections.

### 5. Specification Quality Validation (Mandatory)

After writing the initial draft, you **MUST** validate it against the quality criteria.

1.  **Create Spec Quality Checklist**: Generate `FEATURE_DIR/checklists/requirements.md` with:

    ```markdown
    # Specification Quality Checklist: [FEATURE NAME]
    
    **Purpose**: Validate specification completeness and quality before proceeding.
    **Source**: Derived from Brainstorm Ideas [IDs]
    
    ## Content Quality
    - [ ] No implementation details (languages, frameworks, APIs)
    - [ ] Focused on user value and business needs
    - [ ] All mandatory sections completed
    
    ## Requirement Completeness
    - [ ] No [NEEDS CLARIFICATION] markers remain
    - [ ] Requirements are testable and unambiguous
    - [ ] Success criteria are measurable and technology-agnostic
    - [ ] All acceptance scenarios are defined
    - [ ] Edge cases are identified
    ```

2.  **Run Validation Check**:
    *   Review the spec against each item.
    *   **If items fail**: Update the spec to address them. Re-run validation (max 3 iterations).
    *   **If [NEEDS CLARIFICATION] markers remain**:
        *   Since this comes from a brainstorm, you might not have the user available to answer immediately.
        *   **Strategy**: If the brainstorm content implies an answer, use it. If not, make a reasonable assumption and document it in "Assumptions".
        *   **Limit**: Do not stop for clarification unless the blocker prevents defining the core specifictaion.

3.  **Update Checklist**: Mark items as passed/failed.

### 6. Completion

1.  Report completion with:
    *   Branch: `BRANCH_NAME`
    *   Spec: `SPEC_FILE`
    *   Source: Ideas [IDs] from `BRAINSTORM_FILE`
    *   Readiness: "Spec generated and validated. Ready for review."
