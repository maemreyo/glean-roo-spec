---
description: Turn accepted brainstorm ideas into a concrete feature specification with optional UI/UX design.
handoffs:
  - label: Review Spec
    agent: zo.clarify
    prompt: Review this new specification.
  - label: Build Technical Plan
    agent: zo.plan
    prompt: Create a plan for the spec. I am building with...
---

## User Input

```text
$ARGUMENTS
```

**Context**: The user wants to convert specific ideas from a brainstorming session into a full Feature Specification.
**Format**: `$ARGUMENTS` typically contains "all" or specific idea IDs (e.g., "1, 3") and optionally:
- `--design` or `-d`: Generate design specification alongside the feature spec
- A brainstorm file path

## Outline

### 1. Context Loading

1.  Run the setup script to find the brainstorm file:
    ```bash
    .zo/scripts/bash/setup-specify-idea.sh --json $ARGUMENTS
    ```
2.  Parse JSON output to get `BRAINSTORM_FILE`, `SPEC_TEMPLATE`, `DESIGN_FILE`, and check for `--design` flag.
3.  **Read the content** of `BRAINSTORM_FILE` and `SPEC_TEMPLATE`.
4.  **Read** `DESIGN_FILE` if it exists (to understand existing design patterns).
5.  Parse `$ARGUMENTS` for design flag: `--design` or `-d` indicates user wants design specification.

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

2.  **Check for existing branches before creating new one**:

    a. Fetch all remote branches:
       ```bash
       git fetch --all --prune
       ```

    b. Find the highest feature number across ALL branches and specs:
       - Remote branches: `git ls-remote --heads origin | grep -E 'refs/heads/[0-9]{3}-'`
       - Local branches: `git branch | grep -E '^[* ]*[0-9]{3}-'`
       - Specs directories: Check for all directories matching `specs/[0-9]{3}-`

    c. Determine the next available number:
       - Extract all numbers from all three sources
       - Find the highest number N
       - Use N+1 for the new branch number

3.  **Create Branch**:
    *   Run `.zo/scripts/bash/create-feature-from-idea.sh --json --number N+1 --short-name "short-name" "Synthesized Description"`
    *   Parse JSON output to get `BRANCH_NAME` and `SPEC_FILE`.

### 4. Specification Generation

1.  **Load template**: Read `.zo/templates/spec-template.md` to understand required sections.

2.  **Drafting**: Write the specification to `SPEC_FILE`:
    *   **IMPORTANT**: The file is already initialized with `spec-from-idea.md`.
    *   Replace `[FEATURE NAME]` with a descriptive title covering the selected ideas.
    *   Replace `[FEATURE BRANCH]` with `BRANCH_NAME`.
    *   Replace `[DATE]` with today's date.
    *   **Source Context**: `Brainstorm: [BRAINSTORM_FILE] (Ideas: [Selected IDs])`

3.  **Follow this execution flow**:
    1. Parse synthesized feature description
    2. Extract key concepts: actors, actions, data, constraints
    3. For unclear aspects:
       - Make informed guesses based on brainstorm context and industry standards
       - Only mark with [NEEDS CLARIFICATION: specific question] if critical
       - **LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total**
       - Use brainstorm content to answer when possible
    4. Fill User Scenarios & Testing section
       - Convert each idea's "Proposal" into prioritized User Stories
    5. Generate Functional Requirements
       - Derive from detailed proposal text
       - Each requirement must be testable
    6. Define Success Criteria
       - Derive measurable outcomes from the "Benefit" sections
       - Must be technology-agnostic and verifiable
    7. Identify Key Entities (if data involved)
    8. Document Assumptions made from brainstorm context

### 5. Design System Integration (Optional)

If `--design` or `-d` flag was present in `$ARGUMENTS`:

1.  **Check if design is applicable**:
    *   Does the feature have UI components?
    *   Are there user interactions that need design?
    *   If NO UI/UX involved, skip to validation and inform user.

2.  **Initialize Design File**:
    *   Create `.zo/templates/design-template.md` if not exists
    *   Initialize `FEATURE_DIR/design.md` with the template

3.  **Use UI/UX Pro Max Skill** for design intelligence:

    **Step 5.1: Analyze & Search**

    Based on the feature requirements in `spec.md`, execute the following search sequence:
    *Replace `<keyword>` with relevant terms from the spec and brainstorm ideas.*

    a. **Product Type**:
       ```bash
       python3 .zo/system/ui-ux-pro-max/scripts/search.py "<feature type>" --domain product
       ```
    b. **Style & Aesthetics**:
       ```bash
       python3 .zo/system/ui-ux-pro-max/scripts/search.py "<desired mood>" --domain style
       ```
    c. **Typography**:
       ```bash
       python3 .zo/system/ui-ux-pro-max/scripts/search.py "<mood>" --domain typography
       ```
    d. **Color Palette**:
       ```bash
       python3 .zo/system/ui-ux-pro-max/scripts/search.py "<features/industry>" --domain color
       ```
    e. **Component Patterns** (if applicable):
       ```bash
       python3 .zo/system/ui-ux-pro-max/scripts/search.py "<component name>" --domain ux
       ```

    **Step 5.2: Synthesize & Document**

    Use the data gathered to fill out `FEATURE_DIR/design.md`:
    1.  **Design System**: Fill in Color Palette (specific hex codes), Typography (Font names + sizes), UI Element rules
    2.  **Component Guidelines**: Define visual rules for key components from spec
    3.  **Page Layouts**: Describe layout structure based on product search results
    4.  **UX Rules**: Add accessibility/interaction rules from UX domain search

    **Step 5.3: Verification**

    Review generated `design.md` against quality rules:
    - [ ] **Colors**: Specific hex codes (no "blue", "red"), adequate contrast ratios (≥4.5:1)
    - [ ] **Icons**: Icon set specified by name (Lucide/Heroicons/other), no emoji placeholders
    - [ ] **Typography**: Harmonious font pairing, complete type scale with sizes/weights
    - [ ] **Components**: All UI elements from spec have guidelines with specific measurements
    - [ ] **Interactions**: Hover, focus, active, disabled states defined
    - [ ] **Animations**: Timings specified in milliseconds (not "fast", "slow")
    - [ ] **Accessibility**: Touch targets ≥44×44px, keyboard navigation, ARIA support
    - [ ] **Responsive**: Breakpoints defined for mobile/tablet/desktop
    - [ ] **Completeness**: All template sections filled with specific values

### 6. Specification Quality Validation (Mandatory)

After writing the initial draft, you **MUST** validate it against the quality criteria.

1.  **Create Spec Quality Checklist**: Generate `FEATURE_DIR/checklists/requirements.md` with:

    ```markdown
    # Specification Quality Checklist: [FEATURE NAME]

    **Purpose**: Validate specification completeness and quality before proceeding
    **Created**: [DATE]
    **Feature**: [Link to spec.md]
    **Source**: Derived from Brainstorm Ideas [IDs]

    ## Content Quality

    - [ ] No implementation details (languages, frameworks, APIs)
    - [ ] Focused on user value and business needs
    - [ ] Written for non-technical stakeholders
    - [ ] All mandatory sections completed

    ## Requirement Completeness

    - [ ] No [NEEDS CLARIFICATION] markers remain
    - [ ] Requirements are testable and unambiguous
    - [ ] Success criteria are measurable
    - [ ] Success criteria are technology-agnostic (no implementation details)
    - [ ] All acceptance scenarios are defined
    - [ ] Edge cases are identified
    - [ ] Scope is clearly bounded
    - [ ] Dependencies and assumptions identified

    ## Feature Readiness

    - [ ] All functional requirements have clear acceptance criteria
    - [ ] User scenarios cover primary flows
    - [ ] Feature meets measurable outcomes defined in Success Criteria
    - [ ] No implementation details leak into specification

    ## Design Integration (if --design flag used)

    - [ ] Design specification created at design.md
    - [ ] Color palette has specific hex codes (no generic names)
    - [ ] Color contrast ratios meet WCAG AA (≥4.5:1 for normal text)
    - [ ] Typography system is harmonious (heading + body font pairing)
    - [ ] Font weights and sizes are specified for all text scales
    - [ ] Component guidelines cover all UI elements from spec
    - [ ] Icon set specified with library name (Lucide/Heroicons/other, no emojis)
    - [ ] Interactive states defined (hover, focus, active, disabled)
    - [ ] Animation timings specified (duration in ms)
    - [ ] Touch targets meet minimum size (44×44px for mobile)
    - [ ] Responsive breakpoints defined (mobile, tablet, desktop)
    - [ ] Accessibility considered (keyboard nav, ARIA labels, semantic HTML)

    ## Notes

    - Items marked incomplete require spec updates before `/zo.clarify` or `/zo.plan`
    - Design integration can be added later with `/zo.design` if not done now
    ```

2.  **Run Validation Check**:
    *   Review the spec against each checklist item
    *   Document specific issues found (quote relevant spec sections)

3.  **Handle Validation Results**:

    - **If all items pass**: Mark checklist complete and proceed to completion

    - **If items fail (excluding [NEEDS CLARIFICATION])**:
      1. List the failing items and specific issues
      2. Update the spec to address each issue
      3. Re-run validation until all items pass (max 3 iterations)
      4. If still failing after 3 iterations, document remaining issues in checklist notes

    - **If [NEEDS CLARIFICATION] markers remain**:
      1. Extract all [NEEDS CLARIFICATION: ...] markers from the spec
      2. **LIMIT CHECK**: If more than 3 markers exist, keep only the 3 most critical (by scope/security/UX impact)
      3. Use brainstorm content to answer when possible
      4. For remaining clarifications (max 3), make informed assumptions and document in Assumptions section
      5. Re-run validation after all clarifications are resolved

4.  **Update Checklist**: Mark items as passed/failed after each validation iteration.

### 7. Completion

Report completion with:
*   Branch: `BRANCH_NAME`
*   Spec: `SPEC_FILE`
*   Design: `FEATURE_DIR/design.md` (if --design was used)
*   Source: Ideas [IDs] from `BRAINSTORM_FILE`
*   Checklist: `FEATURE_DIR/checklists/requirements.md`
*   Readiness: "Spec generated and validated. Ready for `/zo.clarify` or `/zo.plan`."

## General Guidelines

### Quick Guidelines

- Focus on **WHAT** users need and **WHY**
- Avoid HOW to implement (no tech stack, APIs, code structure)
- Written for business stakeholders, not developers
- Leverage brainstorm content to answer clarification questions
- DO NOT create checklists that are embedded in the spec

### Section Requirements

- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation from Brainstorm

When creating this spec from brainstorm ideas:

1. **Use brainstorm context**: Ideas often contain rich context for filling gaps
2. **Synthesize multiple ideas**: When selecting multiple ideas, combine them coherently
3. **Document assumptions**: Record reasonable defaults in the Assumptions section
4. **Limit clarifications**: Maximum 3 [NEEDS CLARIFICATION] markers - use brainstorm content first
5. **Prioritize clarifications**: scope > security/privacy > user experience > technical details
6. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist

### Success Criteria Guidelines

Success criteria must be:

1. **Measurable**: Include specific metrics (time, percentage, count, rate)
2. **Technology-agnostic**: No mention of frameworks, languages, databases, or tools
3. **User-focused**: Describe outcomes from user/business perspective
4. **Verifiable**: Can be tested/validated without knowing implementation details

**Good examples**:

- "Users can complete checkout in under 3 minutes"
- "System supports 10,000 concurrent users"
- "95% of searches return results in under 1 second"
- "Task completion rate improves by 40%"

**Bad examples** (implementation-focused):

- "API response time is under 200ms"
- "Database can handle 1000 TPS"
- "React components render efficiently"
- "Redis cache hit rate above 80%"

### Design Integration Guidelines

When using the `--design` flag:

1. **Assess applicability**: Not all features need UI/UX design (API-only features, backend refactors)
2. **Use the skill**: Always use UI/UX Pro Max search scripts - don't guess design patterns
3. **Be specific with values**:
   - Colors: Use specific hex codes (#3B82F6), not generic names (blue, red)
   - Typography: Specify font names (Space Grotesk), weights (400, 700), sizes (16px, 1.5rem)
   - Spacing: Use specific values (12px, 1rem), not "small", "large"
   - Timings: Use milliseconds (200ms, 300ms), not "fast", "slow"
4. **Verify accessibility**:
   - Contrast ratios ≥4.5:1 for normal text, ≥3:1 for large text
   - Touch targets minimum 44×44px for mobile
   - Keyboard navigation and focus states defined
   - ARIA labels for interactive elements
5. **Document all states**:
   - Interactive elements: hover, focus, active, disabled
   - Error, warning, success, info states
   - Loading and empty states
6. **Consider responsive design**:
   - Define breakpoints (mobile <640px, tablet 640-1023px, desktop ≥1024px)
   - Layout adaptations for each breakpoint
   - Touch-friendly controls on mobile
7. **Iterate if needed**: If design search doesn't yield good results, refine search terms with more specific keywords
