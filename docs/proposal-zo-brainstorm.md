# Proposal: New Command `/zo.brainstorm`

You asked for a command to suggest improvements or brainstorm project direction. Based on the Speckit architecture, I recommend creating **`/zo.brainstorm`**.

## 1. Command Definition

**Name**: `/zo.brainstorm`
**Purpose**: leverages the existing context (Spec, Plan, Code) to generate new ideas, optimizations, or strategic pivots.

### Proposed `.roo/commands/zo.brainstorm.md` Structure

```markdown
---
description: Brainstorm improvements, architectural evolutions, or new features based on current project state.
handoffs:
  - label: Specification
    agent: zo.specify
    prompt: I like this idea. Let's specify it.
---

## User Input
$ARGUMENTS

## Instructions

1.  **Context Loading**:
    -   Run `.specify/scripts/bash/check-prerequisites.sh --json` to get the absolute paths of active documents.
    -   Read the files returned in the JSON (specifically `spec.md` and `plan.md`. checking `tasks.md` is optional but recommended for progress context).
2.  **Generate Candidates**: Internally generate a prioritized queue of **8 specific improvement ideas** that balance **Creativity (Vibe)** and **Stability (Pro)**.
    -   *The Mix*: Ensure the list includes:
        -   3x **"Blue Sky" Features** (UX delight, new capabilities - *The Vibe Coder*).
        -   3x **"Bedrock" Improvements** (Refactoring, Security, Performance - *The Pro Dev*).
        -   2x **"Strategic" Question** (Market fit, Scalability - *The Architect*).
    -   *Compliance*: Run all "Blue Sky" ideas against the project `Constitution` to ensure they don't violate enterprise constraints (e.g., "Add gamification" is fine, but "Store user data in local storage" might violate a Security Principle).
3.  **Interactive Loop**:
    -   Present **EXACTLY ONE** idea at a time, clearly labeled by type.
    -   Format:
        ```text
        **Idea #N**: [Title]
        **Benefit**: [Why do this?]
        **Proposal**: [Brief description of change]

        Do you want to document this idea? (yes/no/refine)
        ```
    -   Wait for user response.
    -   **Action**:
        -   If `yes`: Append the idea to `docs/brainstorming.md`.
        -   If `refine`: Ask for specific feedback and update the idea before saving.
        -   If `no`: Discard and move to the next idea.
    -   Stop after 8 ideas or if user says "stop".
4.  **Completion**:
    -   Report summary of saved ideas.
    -   Suggest next steps (e.g., "Run `/zo.specify` on the best idea to start building it").
```

## 2. Workflows & Scenarios

### Scenario A: Optimization Review
*User*: `/zo.brainstorm "How can we make the User Profile check faster?"`
*Agent*: Reads `plan.md` (identifies DB schema), suggests Redis caching or Indexing.

### Scenario B: Feature Ideation
*User*: `/zo.brainstorm "What social features would fit our current app?"`
*Agent*: Reads `spec.md` (understands core app), suggests "Friend Requests" or "Activity Feed" compatible with current data model.

## 3. Edge Cases

| Edge Case | Risk | Mitigation |
| :--- | :--- | :--- |
| **Context Overload** | The project is too large (many files), leading to token limit issues or "forgetting" details. | The command should prioritize reading high-level docs (`spec.md`, `plan.md`) first, and only read code files if specifically pointed to. |
| **Scope Creep** | Suggestions drift specifically away from the core `Constitution` or original vision. | Explicitly instruct the command to check suggestions against `.specify/memory/constitution.md`. |
| **Hallucinated Tech** | AI Suggests libraries that don't match the stack (e.g., suggesting a React library for a Vue project). | Mandatory "Tech Constraint Check" step reading `plan.md` before outputting ideas. |
| **Subjectivity** | "Improvement" is vague. AI might suggest style changes when user wants performance. | Prompt the user for a "Focus Area" (UX vs. Performance vs. Architecture) if prompt is too short. |
| **Obsolete Docs** | `spec.md` is out of sync with code. Brainstorming based on stale spec. | Recommendation to run `/zo.analyze` first to ensure consistency. |

## 4. Philosophy: Vibe vs. Professional

To satisfy both the "Vibe Coder" and the "Large Enterprise Dev", this command operates on a **"Safe Creativity"** principle:

1.  **For the Vibe Coder**: The command encourages wild, creative ideas in the generation phase. It looks for "Delighters" and "UX Magic" that standard specs might miss.
2.  **For the Pro Dev**: It enforces the **Constitution** as a hard filter. A creative idea is only suggested if it *can* be built professionally.
    -   *Example*: A Vibe Coder wants "Instant Search".
    -   *The Command*: Suggests "Optimistic UI updates with a Redis-backed search index" (Vibe goal + Pro implementation).

This ensures innovation doesn't create technical debt.
