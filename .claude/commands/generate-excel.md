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

### Layout

Use **Column B** for labels and **Column C** for amounts (Column A is left empty for indentation). This matches the existing Excel layout from the manual quincena workbook.

| Section | Content |
|---------|---------|
| **Title** | B2: "QUINCENA: {Month Start} → {Month End}, {Year}" (bold, 14pt) |
| | B3: "SoFi Bank · Paycheck Akcelita" (subtitle, gray) |
| **INGRESO** | B5: section header |
| | B6+: Each income source (date + description), C: amount, D: % of income |
| **GASTOS FIJOS — Sobres (Vaults)** | B: section header, C: "Presupuestado", D: "% Ingreso", E: "Destino" |
| | B: Each vault indented ("  Casa (Hipoteca)"), C: amount, D: % of income, E: payment destination |
| | B: "  Subtotal Gastos Fijos", C: total |
| **GASTOS VARIABLES — Sin Sobre** | B: section header, C: "Total", D: "% Ingreso", E: "Transacciones" |
| | B: Each category indented, C: total, D: %, E: merchant names |
| | B: "  Subtotal Gastos Variables", C: total |
| **BALANCE** | B: section header |
| | B: "  Ingreso", C: total income |
| | B: "  (−) Gastos Fijos (Vaults)", C: negative total |
| | B: "  (−) Gastos Variables", C: negative total |
| | B: "  SOBRANTE", C: amount, D: % of income |
| **Saldos reales** | B: current account balances (Savings, Checking, Interest) |
| **RESCATE DE AHORRO** | B: section header (red fill #FFC7CE) — RED FLAG |
| | B: "Dinero sacado de ahorro para cubrir la quincena" (italic, gray) |
| | B: Each "From Savings" transfer with date, C: amount |
| | B: "  Total Rescate de Ahorro", C: total (bold, red) |
| | B: "  Meta: $0 por quincena" (italic, red) |
| **GASTOS SORPRESA** | B: section header (orange #C65911) |
| | B: Each surprise expense indented (description + date), C: amount, D: category (orange fill #FFF2CC) |
| | B: "  Subtotal Gastos Sorpresa", C: total, D: % of income |
| **VAULT DESVIADA (META FALLIDA)** | B: section header (red #C00000) |
| | B: "  Vault", C: "Retirado", D: "Pago Hecho?", E: "Status" |
| | B: Each vault row, C: withdrawn amount, D: yes/no, E: Pagado/Desviado |
| | B: "  Subtotal Vault Desviada", C: total (red, bold) |

### Rescate de Ahorro Section (Red Flag)

Money pulled from savings to cover the current paycheck period. This is the most critical warning — it means the paycheck wasn't enough.

**Source data:** `vault_analysis.json` → `rescate_ahorro` field
- List each "From Savings - 0070" transfer with date and amount
- Show total in bold red
- Include target note: "Meta: $0 por quincena"

**Formatting:**
- Section header: red fill (#FFC7CE), bold, dark red text (#C00000)
- Data rows: light red fill
- Total row: bold, dark red text
- Placed BEFORE Gastos Sorpresa (it's more critical)

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
- Column A: Empty (spacer)
- Column B: Labels (width 40)
- Column C: Amounts (width 15, number format `#,##0.00`)
- Column D: Percentages (width 15, format `0.0%`) or secondary data
- Column E: Notes/destinations (width 25)
- Section headers: bold, 11pt
- Subtotal rows: bold
- Positive sobrante: green text (#006100)
- Negative sobrante: red text (#C00000)
- Rescate de Ahorro rows: light red fill (#FFC7CE)
- Gastos Sorpresa rows: light orange fill (#FFF2CC)
- Indented items use "  " (2 spaces) prefix in Column B

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
- Include "Rescate de Ahorro" total as its own row (if any, red flag)
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
