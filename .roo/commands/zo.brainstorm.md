---
description: Brainstorm improvements, architectural evolutions, or new features based on current project state (8 ideas, mixed creativity/stability).
handoffs:
  - label: Specification
    agent: zo.specify
    prompt: I like this idea. Let's specify it.
  - label: Tasks
    agent: zo.tasks
    prompt: Let's turn this idea into tasks.
---

## User Input

```text
$ARGUMENTS
```

## Instructions

### 1. Context Loading

First, establish the project context by finding the correct specification and planning documents.

1.  Run the prerequisite check script to get absolute file paths:
    ```bash
    .specify/scripts/bash/check-prerequisites.sh --json
    ```
2.  Parse the JSON output to find the `AVAILABLE_DOCS` and paths for `FEATURE_SPEC` (spec.md) and `IMPL_PLAN` (plan.md).
3.  **Read the content** of `spec.md` and `plan.md`. If `tasks.md` exists in the list, read it as well to see current progress.

### 2. Analysis & Generation

Based on the loaded context and the User Input (`$ARGUMENTS`), internally (hidden thought process) generate **8 prioritized improvement ideas**.

**CRITICAL: You must maintain this exact mix of ideas:**

*   **3x "Blue Sky" Features (The Vibe Coder)**: Focus on UX delight, "wow" factors, and novel capabilities. Be creative.
*   **3x "Bedrock" Improvements (The Pro Dev)**: Focus on refactoring, security hardening, performance optimization, and technical debt reduction. Be rigorous.
*   **2x "Strategic" Questions (The Architect)**: Focus on long-term scalability, market fit, or high-level architectural pivots.

**Compliance Check**:
Before presenting, mentally check your "Blue Sky" ideas against the project's `Constitution` (usually in `.specify/memory/constitution.md` or implicitly defined in `plan.md`'s constraints). Ensure innovation doesn't violate core security or architectural principles.

### 3. Interactive Presentation Loop

**DO NOT dump all ideas at once.** You must present them one by one to allow the user to focus.

For EACH of the 8 ideas, follow this sequence:

1.  **Display the Idea**:
    ```text
    ---
    **Candidate #N/8** [Type: Blue Sky / Bedrock / Strategic]
    **Title**: [Idea Title]
    **Benefit**: [Why should we do this?]
    **Proposal**: [Brief description of the change]
    **Cost/Risk**: [Estimated effort and potential downsides]
    ---
    
    Do you want to document this idea? (yes / no / refine / stop)
    ```

2.  **Wait for User Response**:
    *   **If 'yes'**: Append the idea to `docs/brainstorming.md` (create the file if it doesn't exist).
    *   **If 'refine'**: Ask the user for specific feedback, update the idea details, and then ask again (Keep/Discard).
    *   **If 'no'**: Discard the idea and proceed to the next candidate immediately.
    *   **If 'stop'**: Terminate the loop immediately.

3.  **Repeat** until all 8 ideas are processed or user says stop.

### 4. Completion

After the loop ends:
1.  List the titles of all ideas that were saved to `docs/brainstorming.md`.
2.  Suggest the next logical step (e.g., "Run `/zo.specify` on [Saved Idea] to start building it").
