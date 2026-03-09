---
description: Generate Excel workbook with quincenal financial review
argument-hint: <month-dir>
hooks:
  Stop:
    - hooks:
        - type: command
          command: "uv run \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validators/excel-validator.py"
---

# Generate Excel Command

## Purpose

Generate an Excel workbook (.xlsx) for the quincenal financial review. Produces a formatted workbook with summary, distribution chart data, and detailed transaction listing.

## Variables

DIR_PATH: $ARGUMENTS
ROOT_OPERATIONS_DIR: CLAUDE.md: ROOT_OPERATIONS_DIR

## Inputs

1. `DIR_PATH/vault_analysis.json` — vault analysis output
2. `DIR_PATH/agentic_merged_transactions.csv` — all categorized transactions
3. `ROOT_OPERATIONS_DIR/sofi_vault_config.json` — vault configuration

## Output

Write `DIR_PATH/resumen_quincenal.xlsx` with 3 sheets.

## Implementation

Use a Python inline script with openpyxl. Run with `uv run`:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["openpyxl", "pandas"]
# ///
```

## Sheet 1: Resumen Quincenal

Summary overview of the period's finances.

| Row | Content |
|-----|---------|
| 1 | **Title:** "Resumen Quincenal - {Month} {Year}" (bold, 16pt) |
| 3 | **Income** |
| 4 | Each income source with date and amount |
| 5 | **Total Income:** ${amount} (bold, green) |
| 7 | **Vault Allocations** |
| 8+ | Each vault: name, allocated, budget, difference |
| N | **Total Vault Allocations:** ${amount} (bold) |
| N+2 | **Sin Vault (Variable Expenses)** |
| N+3 | Each category: name, total, count |
| N+M | **Total Sin Vault:** ${amount} (bold, red) |
| N+M+2 | *(empty row)* |
| N+M+3 | **Gastos Sorpresa** (bold, 12pt, orange fill #FFF2CC) |
| N+M+4 | Each surprise/impulse expense: date, description, amount |
| N+M+X | **Total Gastos Sorpresa:** ${amount} (bold, orange) |
| N+M+X+2 | **Vault Desviada (Meta Fallida)** (bold, 12pt, red fill #FFC7CE) |
| N+M+X+3 | Each vault where money was withdrawn but NOT used for its intended purpose: vault name, amount withdrawn, expected payment, status |
| N+M+X+Y | **Total Vault Desviada:** ${amount} (bold, red) |
| N+M+X+Y+2 | *(empty row)* |
| N+M+X+Y+3 | **Sobrante:** ${amount} (bold, green if positive, red if negative) |
| N+M+X+Y+4 | **Formula:** income - vaults - sin_vault = sobrante |

### Gastos Sorpresa Section

Surprise/impulse expenses — transactions tagged as `surprise` or `impulse` in the CSV, or transactions that are non-recurring and don't match any known pattern. These are expenses the user didn't plan for.

**Detection logic (from vault_analysis.json):**
- If `vault_analysis.json` has a `gastos_sorpresa` field, use it directly
- Otherwise, identify sin-vault transactions that are NOT in categories typically recurring (subscriptions, bills, insurance) — things like entertainment, shopping, one-time food splurges

**Columns:** Date | Description | Category | Amount

**Formatting:**
- Section header: orange fill (#FFF2CC), bold
- Each row: date, description, category, amount
- Total row: bold, orange text

### Vault Desviada (Meta Fallida) Section

When money was withdrawn from a vault ("From X Vault") but the intended payment for that vault's purpose was NOT made during the period. This signals a failed budget goal.

**Detection logic:**
- For each vault in `sofi_vault_config.json`, check:
  1. Was there a "From X Vault" withdrawal? (money left the vault)
  2. Was the corresponding payment made? Match using the vault's `note` field:
     - House vault → look for BANCO POPULAR payment
     - Apple vault → look for APPLECARD GSBANK payment
     - Seguro del carro vault → look for PROGRESSIVE payment
     - Gasto fijo internet, luz, agua → look for utility payments
  3. If money was withdrawn but payment NOT found → **vault desviada**
- Compare amount withdrawn vs expected payment amount

**Columns:** Vault Name | Amount Withdrawn | Expected Payment | Status (Pagado/Desviado)

**Formatting:**
- Section header: red fill (#FFC7CE), bold
- "Desviado" status: red text, bold
- "Pagado" status: green text
- Total row: bold, sum of desviado amounts only

### Formatting
- Column B: Amounts (width 15, number format `$#,##0.00`)
- Column C: Budget/Notes (width 15)
- Column D: Difference (width 15)
- Header rows: bold, larger font
- Positive sobrante: green fill (#C6EFCE)
- Negative sobrante: red fill (#FFC7CE)
- Vault rows: light blue fill (#DAEEF3)

## Sheet 2: Distribucion

Breakdown of where money went, suitable for creating a pie chart.

| Column A | Column B |
|----------|----------|
| Category | Amount |
| Vault: House | 500.00 |
| Vault: Apple | 190.00 |
| ... | ... |
| Sin Vault: food | 85.50 |
| Sin Vault: subscriptions | 35.00 |
| ... | ... |
| Sobrante | 909.08 |

- Include ALL vault allocations as "Vault: {name}"
- Include ALL sin-vault categories as "Sin Vault: {category}"
- Include "Gastos Sorpresa" total as its own row (if any)
- Include "Vault Desviada" total as its own row (if any)
- Include Sobrante as the final row
- This data can be used to create a pie chart in Excel

## Sheet 3: Detalle Gastos Variables

Full listing of sin-vault (variable/untracked) expenses.

| Date | Description | Category | Amount |
|------|-------------|----------|--------|
| 2026-02-10 | COSTCO WHSE | food | 42.52 |
| 2026-02-08 | WENDYS | food | 5.35 |
| ... | ... | ... | ... |
| | | **TOTAL** | **228.92** |

### Formatting
- Header row: bold, dark blue background (#4472C4), white text
- Alternating row colors (white / light gray #F2F2F2)
- Amount column: number format `$#,##0.00`
- Total row: bold, top border
- Sort by date descending

## Workflow

1. Read `vault_analysis.json` from DIR_PATH
2. Read `agentic_merged_transactions.csv` from DIR_PATH
3. Read `sofi_vault_config.json` from ROOT_OPERATIONS_DIR
4. Create a Python script that uses openpyxl to generate the workbook
5. Run the script with `uv run`
6. Verify `resumen_quincenal.xlsx` was created
7. The Stop hook (excel-validator.py) validates the output

## Critical Requirements
- File must be valid .xlsx (openable by Excel/Numbers)
- All 3 sheets must exist with correct names
- Totals in Resumen sheet must match vault_analysis.json values
- Amount columns must use Excel number format (not text)
