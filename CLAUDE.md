# Project Context

This is an Agentic Finance Review project using Claude Code agentics (skills, agents, commands, hooks) to autonomously review finances.

## Variables

ROOT_OPERATIONS_DIR: apps/agentic-finance-review/data/real_2025_2026/

## SoFi Bank Context

### CSV Format
SoFi exports CSVs with columns: `Date,Description,Type,Amount,Current balance,Status`
- Single `Amount` column: positive = deposit, negative = debit
- `Type` field: DEBIT_CARD, DEPOSIT, WITHDRAWAL, DIRECT_DEPOSIT, DIRECT_PAY, INTEREST_EARNED, ATM, OTHER
- Dates already in YYYY-MM-DD format (no conversion needed)
- No card number noise in descriptions

### Vault System (Envelope Budgeting)
SoFi Vaults act as virtual envelopes within the savings account. Vault config is at `ROOT_OPERATIONS_DIR/sofi_vault_config.json`.

**Vault transfer patterns in checking CSV:**
- `"From X Vault"` — money withdrawn from vault to checking (DEPOSIT type)
- `"To X Vault"` — money allocated from checking to vault (WITHDRAWAL type)
- `"From Savings - 0070"` — transfer from savings to checking
- `"To Savings - 0070"` — transfer from checking to savings

These are all internal movements, not real expenses. They must be excluded from expense analysis.

### Pay Schedule
- Employer: Akcelita LLC (via Justworks payroll)
- Quincenal: 15th and 30th of each month
- Base: ~$1,300 per paycheck (variable)
- Paycheck deposits go to savings account (DIRECT_DEPOSIT type)

### Expense Analysis
The key insight is: **Sin Vault expenses** = transactions that aren't covered by any vault.
- Income - Vault Allocations - Sin Vault expenses = Sobrante (leftover)
- `known_mappings.json` has override rules and `exclude_from_expenses` list
