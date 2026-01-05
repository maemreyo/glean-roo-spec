# Proposal: New Command `/speckit.brainstorm`

You asked for a command to suggest improvements or brainstorm project direction. Based on the Speckit architecture, I recommend creating **`/speckit.brainstorm`**.

## 1. Command Definition

**Name**: `/speckit.brainstorm`
**Purpose**: leverages the existing context (Spec, Plan, Code) to generate new ideas, optimizations, or strategic pivots.

### Proposed `.roo/commands/speckit.brainstorm.md` Structure

```markdown
---
description: Brainstorm improvements, architectural evolutions, or new features based on current project state.
handoffs:
  - label: Specification
    agent: speckit.specify
    prompt: I like this idea. Let's specify it.
---

## User Input
$ARGUMENTS

## Instructions

1.  **Analyze Context**: Read `spec.md`, `plan.md`, and `tasks.md` to understand the project state.
2.  **Generate Candidates**: Internally generate a prioritized queue of **5 specific improvement ideas or strategic questions**.
    -   *Filtering*: Focus on high-impact areas (e.g., Performance improvement, Tech Debt reduction, UX enhancement, Security gap).
    -   *Prioritization*: Rank by Impact / Effort ratio.
3.  **Interactive Loop**:
    -   Present **EXACTLY ONE** idea at a time.
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
    -   Stop after 5 ideas or if user says "stop".
4.  **Completion**:
    -   Report summary of saved ideas.
    -   Suggest next steps (e.g., "Run `/speckit.specify` on the best idea to start building it").
```

## 2. Workflows & Scenarios

### Scenario A: Optimization Review
*User*: `/speckit.brainstorm "How can we make the User Profile check faster?"`
*Agent*: Reads `plan.md` (identifies DB schema), suggests Redis caching or Indexing.

### Scenario B: Feature Ideation
*User*: `/speckit.brainstorm "What social features would fit our current app?"`
*Agent*: Reads `spec.md` (understands core app), suggests "Friend Requests" or "Activity Feed" compatible with current data model.

## 3. Edge Cases

| Edge Case | Risk | Mitigation |
| :--- | :--- | :--- |
| **Context Overload** | The project is too large (many files), leading to token limit issues or "forgetting" details. | The command should prioritize reading high-level docs (`spec.md`, `plan.md`) first, and only read code files if specifically pointed to. |
| **Scope Creep** | Suggestions drift specifically away from the core `Constitution` or original vision. | Explicitly instruct the command to check suggestions against `.specify/memory/constitution.md`. |
| **Hallucinated Tech** | AI Suggests libraries that don't match the stack (e.g., suggesting a React library for a Vue project). | Mandatory "Tech Constraint Check" step reading `plan.md` before outputting ideas. |
| **Subjectivity** | "Improvement" is vague. AI might suggest style changes when user wants performance. | Prompt the user for a "Focus Area" (UX vs. Performance vs. Architecture) if prompt is too short. |
| **Obsolete Docs** | `spec.md` is out of sync with code. Brainstorming based on stale spec. | Recommendation to run `/speckit.analyze` first to ensure consistency. |
