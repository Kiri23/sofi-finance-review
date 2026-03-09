---
description: Analyze income vs vault allocations vs sin-vault expenses
argument-hint: <month-dir>
hooks:
  Stop:
    - hooks:
        - type: command
          command: "uv run \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validators/vault-validator.py"
---

# Vault Analysis Command

## Purpose

Calculate the financial breakdown: Income - Vault Allocations - Sin Vault Expenses = Sobrante (leftover). This is the core analysis unique to Christian's quincenal review workflow.

## Variables

DIR_PATH: $ARGUMENTS
ROOT_OPERATIONS_DIR: CLAUDE.md: ROOT_OPERATIONS_DIR

## Inputs

1. `DIR_PATH/agentic_merged_transactions.csv` — merged, categorized transactions
2. `ROOT_OPERATIONS_DIR/sofi_vault_config.json` — vault names and budgets

## Output

Write `DIR_PATH/vault_analysis.json` with this structure:

```json
{
  "period": {
    "month": "feb",
    "year": 2026,
    "start_date": "2026-02-01",
    "end_date": "2026-02-28"
  },
  "income": {
    "total": 2600.00,
    "breakdown": [
      {"date": "2026-02-15", "description": "Justworks Payroll", "amount": 1300.00},
      {"date": "2026-02-28", "description": "Justworks Payroll", "amount": 1300.00}
    ]
  },
  "vault_allocations": {
    "total": 1462.00,
    "by_vault": {
      "House": {"allocated": 500.00, "budget": 500.00},
      "Apple": {"allocated": 190.00, "budget": 190.00},
      "Seguro del carro": {"allocated": 128.00, "budget": 128.00},
      "Gasto fijo internet, luz, agua": {"allocated": 150.00, "budget": 150.00}
    }
  },
  "sin_vault_expenses": {
    "total": 228.92,
    "by_category": {
      "food": {"total": 85.50, "count": 8},
      "subscriptions": {"total": 35.00, "count": 2},
      "health": {"total": 45.00, "count": 1}
    },
    "transactions": [
      {"date": "2026-02-10", "description": "COSTCO WHSE", "category": "food", "amount": 42.52},
      {"date": "2026-02-08", "description": "WENDYS", "category": "food", "amount": 5.35}
    ]
  },
  "rescate_ahorro": {
    "total": 105.00,
    "transactions": [
      {"date": "2026-02-26", "description": "From Savings - 0070", "amount": 35.00},
      {"date": "2026-02-27", "description": "From Savings - 0070", "amount": 20.00}
    ],
    "note": "Money pulled from savings to cover the paycheck period. Target: $0. Red flag if > 0."
  },
  "gastos_sorpresa": {
    "total": 77.19,
    "transactions": [
      {"date": "2026-03-03", "description": "Caribbean Cinemas", "category": "entertainment", "amount": 14.86},
      {"date": "2026-03-04", "description": "Marshalls #631", "category": "shopping", "amount": 20.06}
    ],
    "note": "Non-recurring, non-essential expenses (entertainment, shopping, impulse food). Subset of sin_vault."
  },
  "vault_desviada": {
    "total": 0,
    "vaults": [
      {"vault": "Seguro del carro", "withdrawn": 90.00, "payment_found": true, "payment_to": "PROGRESSIVE", "status": "Pagado"},
      {"vault": "House", "withdrawn": 1000.00, "payment_found": true, "payment_to": "BANCO POPULAR", "status": "Pagado"}
    ],
    "note": "Vaults where money was withdrawn but NOT used for intended purpose. Total = sum of Desviado only."
  },
  "sobrante": 909.08,
  "formula": "income (2600.00) - vault_allocations (1462.00) - sin_vault_expenses (228.92) = sobrante (909.08)",
  "math_check": true
}
```

## Workflow

1. Read `agentic_merged_transactions.csv` from DIR_PATH
2. Read `sofi_vault_config.json` from ROOT_OPERATIONS_DIR
3. Load `known_mappings.json` from ROOT_OPERATIONS_DIR for `exclude_from_expenses` list

### Step 1: Calculate Income
- Sum all transactions where category = "Income"
- Include DIRECT_DEPOSIT transactions from savings account
- List each income transaction with date, description, amount

### Step 2: Calculate Vault Allocations
- Find all "Vault Allocation: *" category transactions (these are "To X Vault" movements)
- Group by vault name, sum amounts per vault
- Compare actual allocations vs budgets from `sofi_vault_config.json`
- Note: "Vault Transfer: *" (From X Vault) are withdrawals FROM vaults, not allocations

### Step 3: Identify Sin Vault Expenses
- These are all transactions that are NOT in the `exclude_from_expenses` list
- Specifically: NOT Income, NOT Vault Transfer, NOT Vault Allocation, NOT Internal Transfer, NOT Credit Card Payment, NOT Interest
- These are the "untracked" expenses — money spent outside the vault/envelope system
- Group by category with totals and transaction counts
- List every sin-vault transaction for the detail view

### Step 4: Rescate de Ahorro (Red Flag)
- Find all "From Savings - 0070" or "Internal Transfer" deposits into checking
- These represent money pulled from savings because the paycheck wasn't enough
- Sum total and list each transaction
- Target is $0 — any amount here is a red flag

### Step 5: Identify Gastos Sorpresa
- Subset of sin-vault expenses that are non-recurring and non-essential
- Categories that qualify: entertainment, shopping, tienda/ropa, impulse food (one-time restaurant visits, fast food splurges)
- Categories that do NOT qualify (they're expected variable costs): gas, supermercado, farmacia, subscriptions, bills
- List each surprise expense with date, description, category, amount

### Step 6: Detect Vault Desviada (Meta Fallida)
- For each vault in `sofi_vault_config.json`:
  1. Find "From X Vault" withdrawals (money left the vault to checking)
  2. Check if the corresponding payment was made by matching the vault's `note` field:
     - House → BANCO POPULAR
     - Apple → APPLECARD GSBANK
     - Seguro del carro → PROGRESSIVE
     - Gasto fijo internet, luz, agua → utility payments
  3. Status: "Pagado" if payment found, "Desviado" if not
  4. Only vaults with withdrawals are listed
- Total = sum of amounts where status = "Desviado"

### Step 7: Calculate Sobrante
- `sobrante = income - vault_allocations_total - sin_vault_expenses_total`
- Set `math_check = true` if the formula balances correctly
- If `sobrante < 0`, flag as "deficit" in the output

### Step 8: Write Output
- Write `vault_analysis.json` to DIR_PATH
- The Stop hook (vault-validator.py) will validate the math and structure

## Critical Requirements
- Income MUST only count actual deposits (DIRECT_DEPOSIT), not vault transfers
- Vault allocations MUST only count "To X Vault" transactions, not "From X Vault"
- Sin vault expenses MUST exclude all categories in `exclude_from_expenses`
- The formula MUST balance: income - allocations - sin_vault = sobrante
- All amounts must be positive numbers (absolute values)
