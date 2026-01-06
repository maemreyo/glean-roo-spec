---
description: Design the UI/UX for a feature using the UI/UX Pro Max skill.
handoffs:
  - label: Review Design
    agent: zo.clarify
    prompt: Review this design specification.
  - label: Plan Implementation
    agent: zo.plan
    prompt: Create a plan based on spec and design.
---

## User Input

```text
$ARGUMENTS
```

**Context**: The user wants to create a detailed UI/UX Design Specification (`design.md`) for the current feature.

## Instructions

### 1. Context Loading

1.  Run the setup script:
    ```bash
    .specify/scripts/bash/setup-design.sh --json $ARGUMENTS
    ```
2.  Parse JSON output only to get `DESIGN_FILE` and `FEATURE_SPEC`.
3.  **Read** `FEATURE_SPEC` to understand the product type, target audience, and key functionalities.
4.  **Read** `DESIGN_FILE` (it may be a fresh template or existing draft).

### 2. Design Intelligence Process (UI/UX Pro Max)

You **MUST** use the `ui-ux-pro-max` skill to gather data. Do not guess styles.

**Step 2.1: Analyze & Search**

Based on the feature requirements in `spec.md`, execute the following search sequence using the skill's scripts.
*Replace `<keyword>` with relevant terms from the spec (e.g., "fintech dashboard", "medical appointment").*

1.  **Product Type**:
    ```bash
    python3 .roo/skills/ui-ux-pro-max/scripts/search.py "<feature type>" --domain product
    ```
2.  **Style & Aesthetics**:
    ```bash
    python3 .roo/skills/ui-ux-pro-max/scripts/search.py "<desired mood>" --domain style
    ```
3.  **Typography**:
    ```bash
    python3 .roo/skills/ui-ux-pro-max/scripts/search.py "<mood>" --domain typography
    ```
4.  **Color Palette**:
    ```bash
    python3 .roo/skills/ui-ux-pro-max/scripts/search.py "<features/industry>" --domain color
    ```
5.  **Component Patterns** (if applicable):
    ```bash
    python3 .roo/skills/ui-ux-pro-max/scripts/search.py "<component name>" --domain ux
    ```

**Step 2.2: Synthesize & Document**

Use the data gathered to fill out `DESIGN_FILE`.

1.  **Design System**: Fill in the Color Palette (choose specific hex codes from search results), Typography (Font names + sizes), and UI Element rules.
2.  **Component Guidelines**: Define specific visual rules for the key components mentioned in `spec.md`.
3.  **Page Layouts**: Describe the layout structure based on "product" search results (e.g., Dashboard layout vs Landing page).
4.  **UX Rules**: Add specific accessibility or interaction rules found during the "ux" domain search.

### 3. Verification

Before finishing, review the generated `design.md` against the **Common Rules** from the skill:

-   [ ] **Colors**: Are contrast ratios legible? (No low-contrast gray-on-gray).
-   [ ] **Icons**: Did you specify an icon set (e.g., Lucide/Heroicons)? No emojis as icons.
-   [ ] **Typography**: Is the font pairing harmonious?
-   [ ] **Completeness**: Are all sections of the template filled?

### 4. Completion

Report completion:
*   "Generated Design Specification at `DESIGN_FILE`."
*   "Selected Style: [Style Name] with [Font Name]."
*   "Run `/zo.plan` to create the technical implementation plan."
