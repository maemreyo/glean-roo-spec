# Speckit & Roo Integration Guide

This document outlines the integration between **Speckit** (referring to [GitHub Spec Kit](https://github.com/github/spec-kit)) and **Roo Code**. This integration facilitates **Spec-Driven Development (SDD)**, allowing for a structured, high-quality development workflow driven by clear specifications and AI agents.

## Overview

**Spec-Driven Development** allows you to define the *what* and *why* of a feature before generating the code. By creating a single source of truth (the Spec), you reduce ambiguity and guide the AI (Roo Code) to produce more accurate and consistent results.

## Workflow

The integration typically follows this cycle:

1.  **Specify**: Define the feature's requirements and context.
2.  **Plan**: Create a technical implementation plan.
3.  **Tasks**: Break the plan down into actionable tasks for the agent.
4.  **Implement**: The agent executes the tasks to build the feature.

This workflow ensures that code is not just "vibe coded" but is built against a rigorous standard.

## Project Structure

This project uses the standard Spec Kit structure:

-   **`.specify/`**: The core directory for Spec Kit.
    -   **`templates/`**: Templates for generating specific types of documents (Constitutions, Specs, Tasks).
    -   **`rules/`**: Rules that guide the AI's behavior and code generation.
    -   **`memory/`**: (Optional) For maintaining context across sessions.

## Commands (Slash Commands)

When using Roo Code with this integration, you drive the workflow using specific slash commands. These commands trigger scripts or templates found in the `.specify` directory.

### Core Commands

| Command | Description | Usage |
| :--- | :--- | :--- |
| **`/speckit.specify`** | **Generate Specification**<br>Converts a feature description into a structured `spec.md`. Validates requirements against quality criteria. | `/speckit.specify "feature description"` |
| **`/speckit.clarify`** | **Refine Specification**<br>Interactive Q&A session to reduce ambiguity in the Spec. Updates `spec.md` directly. | `/speckit.clarify` |
| **`/speckit.plan`** | **Create Technical Plan**<br>Generates `plan.md` (architecture, stack), `data-model.md`, and API contracts based on the Spec. | `/speckit.plan` |
| **`/speckit.checklist`**| **Validate Requirements**<br>Generates "unit tests for English" (e.g., `checklists/ux.md`) to verify spec quality/completeness before coding. | `/speckit.checklist "UX focus"` |
| **`/speckit.tasks`** | **Generate Task List**<br>Converts Spec and Plan into an actionable `tasks.md`, organized by user story and phases. | `/speckit.tasks` |
| **`/speckit.analyze`** | **Consistency Check**<br>Read-only analysis of `spec.md`, `plan.md`, and `tasks.md` to find inconsistencies or "Constitution" violations. | `/speckit.analyze` |
| **`/speckit.implement`**| **Execute Code**<br>Verifies checklists and project setup, then executes tasks from `tasks.md` phase-by-phase. | `/speckit.implement` |

### Utility & Configuration

| Command | Description |
| :--- | :--- |
| **`/speckit.constitution`** | **Update Constitution**<br>Updates the project principles in `.specify/memory/constitution.md`. |
| **`/speckit.taskstoissues`**| **Export to GitHub**<br>Converts items in `tasks.md` into actual GitHub Issues (requires remote to match). |

## Getting Started

1.  **Define a Feature**: Start by running `/speckit.specify` and describing what you want to build.
2.  **Review the Spec**: Roo will generate a markdown file (usually in `specs/`). Review and refine it.
3.  **Plan**: Run `/speckit.plan` on the approved Spec.
4.  **Task**: Run `/speckit.tasks` to generate the checklist.
5.  **Build**: Use `/speckit.implement` to let Roo build the feature step-by-step.

## Creating Custom Commands

You can extend this system by creating your own slash commands.

### 1. Command Definition

Create a new Markdown file in `.roo/commands/`. The filename becomes the command (e.g., `mycommand.md` becomes `/mycommand`).

**Structure:**

```markdown
---
description: Description of what this command does.
---

## User Input

```text
$ARGUMENTS
```

## Instructions

1.  **Step 1**: Do something.
2.  **Step 2**: Run a script if needed:
    ```bash
    .specify/scripts/bash/my-script.sh --arg "$ARGUMENTS"
    ```
```

### 2. Script Integration (Optional)

If your command needs to perform system operations (like git commands, file creation), create a bash script in `.specify/scripts/bash/`.

**Best Practices:**
-   Keep scripts atomic (do one thing well).
-   Use absolute paths or relative paths from the project root.
-   Return JSON output if the agent needs to parse the result.

