---
model: opus
description: Categorize transactions in normalized CSV files based on descriptions
argument-hint: <month-dir>
hooks:
  Stop:
    - hooks:
        - type: command
          command: "uv run \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validators/csv-validator.py"
---

# Categorize CSV Command

## Purpose

Analyze transaction descriptions in normalized CSV files and populate the empty `category` column with appropriate personal spending categories. Includes vault-awareness for SoFi envelope budgeting.

## Variables

DIR_PATH: $ARGUMENTS
ROOT_OPERATIONS_DIR: CLAUDE.md: ROOT_OPERATIONS_DIR

## Vault-Aware Categorization (Priority 1)

Before applying keyword-based categories, check for vault-related transactions. Load `ROOT_OPERATIONS_DIR/sofi_vault_config.json` if it exists.

### Auto-Categorize Rules (in order of priority)

1. **Vault Transfers** (description matches `From * Vault`):
   - Category: `"Vault Transfer: {vault_name}"`
   - Example: "From House Vault" → `"Vault Transfer: House"`
   - Example: "From Christian dinero personal Vault" → `"Vault Transfer: Christian dinero personal"`

2. **Vault Allocations** (description matches `To * Vault`):
   - Category: `"Vault Allocation: {vault_name}"`
   - Example: "To Seguro del carro Vault" → `"Vault Allocation: Seguro del carro"`

3. **Internal Transfers** (savings ↔ checking):
   - "From Savings - 0070" → `"Internal Transfer"`
   - "To Savings - 0070" → `"Internal Transfer"`

4. **Paycheck** (Type = DIRECT_DEPOSIT, or description contains payroll provider):
   - Category: `"Income"`

5. **Interest** (description contains "Interest earned"):
   - Category: `"Interest"`

6. **Known Mappings Overrides** (see Step 4 below)

7. **Keyword-based categories** (see table below)

## Categories

| Category | Keywords |
|----------|----------|
| `engineering` | CURSOR, OPENAI, ANTHROPIC, REPLICATE, GOOGLE CLOUD, NEON.TECH, VERCEL, AWS, GITHUB, ELEVENLABS |
| `trading` | TRADINGVIEW |
| `food` | TRADER JOE, WHOLE FOODS, DOORDASH, UBER EATS, restaurant, grocery, PANADERIA, ECONO, COSTCO, SAMS CLUB, WENDYS, BURGER KING, KFC, POLLO TROPICAL, PIZZA, BODEGUITA, COLMADO |
| `bills` | RENT, CON EDISON, NATIONAL GRID, SPECTRUM, utilities |
| `entertainment` | NETFLIX, SPOTIFY, MAX.COM, DISNEY, MIDJOURNEY |
| `amazon` | AMAZON, AMZN (purchases, not Prime) |
| `subscriptions` | Prime, recurring monthly services, APPLE.COM/BILL |
| `transfers` | VENMO, APPLE CASH, ZELLE, bank transfers |
| `income` | PAYCHECK, salary, ACH CREDIT, DIRECT_DEPOSIT |
| `loans` | STUDENT LN, DEPT EDUCATION |
| `travel` | Airlines, hotels, Uber/Lyft rides |
| `health` | BROOKLYN BOULDERS, pharmacy, medical, QUEST DIAGNOSTICS, FARMACIA |
| `insurance` | PROGRESSIVE |
| `shopping` | TJ MAXX, BURLINGTON, OFFICE MAX |
| `gas` | TEXACO, GAS STATION, ECONO FUEL |
| `other` | Default fallback |

## Workflow

1. Find all `normalized_*.csv` files in DIR_PATH
2. For each transaction:
   a. First, check vault-aware rules (priority 1-5 above)
   b. If no vault rule matched, check known_mappings overrides (step 4)
   c. If still uncategorized, apply keyword-based categorization
   d. If nothing matches, assign `"other"`
3. Update the category column in place
4. **Apply Known Mappings** (see below)
5. Report results including vault transfer summary

## Step 4: Apply Known Mappings

After AI categorization, apply user-defined overrides from `known_mappings.json`:

1. Check if `ROOT_OPERATIONS_DIR/known_mappings.json` exists (ROOT_OPERATIONS_DIR is defined in CLAUDE.md)
2. If it does NOT exist, skip this step
3. If it exists, read the `overrides` array
4. For each transaction in every `normalized_*.csv` file in DIR_PATH:
   - Check against each override rule:
     - `description_contains`: case-insensitive substring match on the transaction description
     - `description_matches` (optional): regex pattern match on description. If present, BOTH `description_contains` and `description_matches` must match
     - `amount` (optional): if present, the transaction's withdrawal or deposit must match this amount exactly
     - `amount_max` (optional): if present, the transaction's withdrawal or deposit must be <= this amount
     - If BOTH `description_contains` and `amount` are specified, BOTH must match
     - If `description_contains` and `amount_max` are specified, description must match AND amount must be <= amount_max
     - If only `description_contains` is specified (no amount or amount_max), match regardless of amount
   - If a match is found, override the AI-assigned category with the override's `category`
   - First matching override wins (stop checking after first match)
5. Report which overrides were applied:
   - List each override that matched, how many transactions it affected, and the categories that were changed

## Report

After categorization, include a vault transfer summary:
```
### Vault Summary
- Vault Transfers (From Vault): X transactions, $Y total
- Vault Allocations (To Vault): X transactions, $Y total
- Internal Transfers: X transactions
- Sin Vault (uncovered expenses): X transactions, $Y total
```
