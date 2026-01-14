---
description: Create or update the feature specification from a natural language feature description with optional UI/UX design (Roo Tools Proof-of-Concept)
handoffs:
   - label: Build Technical Plan
     agent: zo.plan
     prompt: Create a plan for the spec. I am building with...
   - label: Clarify Spec Requirements
     agent: zo.clarify
     prompt: Clarify specification requirements
     send: true
---

> **Proof-of-Concept**: This command uses Roo Custom Tools instead of Python scripts for feature initialization.
>
> Uses tools:
> - `git_branch_detector`: Detect highest branch numbers from git and specs
> - `branch_name_generator`: Generate short names from descriptions
>
> **NOTE**: This is a proof-of-concept version. Original `zo.specify.md` remains unchanged.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

**Optional Design Flag**: If `$ARGUMENTS` contains `--design` or `-d`, generate design specification alongside the feature spec.

## Outline

The text the user typed after `/zo.specify.roo-tools` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `$ARGUMENTS` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, do this:

1. **Generate a concise short name** (2-4 words) for the branch:
    - Use `branch_name_generator` tool to generate from feature description
    - Use action-noun format when possible (e.g., "add-user-auth", "fix-payment-bug")
    - Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)
    - Keep it concise but descriptive enough to understand the feature at a glance

2. **Check for existing branches before creating new one**:

    a. Use `git_branch_detector` tool to find the highest feature number across:
       - Remote branches: `git ls-remote --heads origin | grep -E 'refs/heads/[0-9]{3}-'`
       - Local branches: `git branch | grep -E '^[* ]*[0-9]{3}-'`
       - Specs directories: Check for all directories matching `specs/[0-9]{3}-`

    b. Determine the next available number:
       - Extract all numbers from tool results
       - Find the highest number N
       - Use N+1 for the new branch number

3. **Create Branch and Feature Structure**:
    - Create git branch with pattern: `{next_number:03d}-{short_name}`
    - Create feature directory: `specs/{branch_name}/`
    - Copy spec template to: `specs/{branch_name}/spec.md`

4. **Generate Specification Content**:
    - Load `.zo/templates/spec-template.md`
    - Parse user description to extract key concepts (actors, actions, data, constraints)
    - Fill template with derived details
    - Handle [NEEDS CLARIFICATION] markers for unclear aspects (max 3)
    - Write to SPEC_FILE

5. Report completion with branch name, spec file path, and readiness for next phase.

**NOTE:** This proof-of-concept focuses on basic branch creation and spec initialization using Roo Tools.