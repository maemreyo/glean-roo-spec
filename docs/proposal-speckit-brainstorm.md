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
1. Analyze the current context (read `spec.md` and `plan.md`).
2. Identify areas for improvement based on the User Input (e.g., "performance", "UX", "security", or open-ended).
3. Generate a list of proposals.
4. For each proposal, provide:
   - **Benefit**: Value add.
   - **Cost**: Implementation effort (Small/Medium/Large).
   - **Risk**: Potential downsides.
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
