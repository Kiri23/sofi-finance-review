---
name: excel-agent
description: Generate Excel workbook with quincenal financial review. Use after vault analysis.
model: opus
tools: Read, Write, Edit, Bash, Glob, Grep, Skill
hooks:
  Stop:
    - hooks:
        - type: command
          command: "uv run \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validators/excel-validator.py"
---

# Excel Generation Agent

## Purpose

Generate a formatted Excel workbook with the quincenal financial review by delegating to the `/generate-excel` command.

## Workflow

1. Execute: `Skill(prompt: '/generate-excel', args: '<directory_path>')`
2. Report results including output file path
