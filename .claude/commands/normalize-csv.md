---
description: Normalize a raw bank CSV export into our standard format
argument-hint: <raw_csv_file>
hooks:
  Stop:
    - hooks:
        - type: command
          command: "uv run \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validators/csv-validator.py"
        - type: command
          command: "uv run \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validators/normalized-balance-validator.py"
---

# Normalize CSV Command

Transform a single raw bank CSV export into our standardized normalized format.

## Variables
ROOT_OPERATIONS_DIR: CLAUDE.md: ROOT_OPERATIONS_DIR

## Arguments
- `$ARGUMENTS`: Path to a raw CSV file (e.g., `ROOT_OPERATIONS_DIR/mock_dataset_jan_1st_2026/raw_checkings.csv`)

## Supported Input Formats

### Format A: Traditional Bank Export
```csv
Date,Description,Withdrawals,Deposits,Category,Balance
"01/31/2026","DEBIT CARD PURCHASE   XXXXX4291 Amazon Prime*KV2819YT5","$148.32","","Subscriptions","$42,156.78"
```
- Dates in MM/DD/YYYY format (quoted)
- Separate Withdrawals/Deposits columns with $ and commas
- Card numbers in descriptions (XXXXX1234)

### Format B: SoFi Export
```csv
Date,Description,Type,Amount,Current balance,Status
2026-02-12,From Christian dinero personal  Vault,DEPOSIT,20.00,58.55,Posted
2026-02-12,FARMACIA CAR-TA7,ATM,-160.00,38.55,Posted
```
- Dates already in YYYY-MM-DD format
- Single `Amount` column: positive = deposit, negative = withdrawal
- `Type` field: DEBIT_CARD, DEPOSIT, WITHDRAWAL, DIRECT_DEPOSIT, DIRECT_PAY, INTEREST_EARNED, ATM, OTHER
- `Status` field (always "Posted" for completed transactions)
- No card number noise in descriptions

## Output Format (Normalized)
```csv
date,description,category,deposit,withdrawal,balance,account_name
2026-01-31,Amazon Prime Subscription,,148.32,,42156.78,checkings
```

## Normalization Rules

### Auto-Detect Format
1. Read the CSV header row
2. If columns include `Type` and `Amount` and `Current balance` → **SoFi format (Format B)**
3. If columns include `Withdrawals` and `Deposits` → **Traditional format (Format A)**
4. Error if neither format matches

### Date Conversion
- **Format A:** Convert MM/DD/YYYY to YYYY-MM-DD (ISO 8601)
- **Format B:** Already YYYY-MM-DD, no conversion needed
- Filter out transactions from previous months (keep only current month based on parent directory name)

### Amount Parsing
- **Format A:**
  - Remove $ symbols and commas from Withdrawals/Deposits
  - Withdrawals go in withdrawal column, Deposits go in deposit column
- **Format B (SoFi):**
  - If Amount > 0 → deposit column, leave withdrawal blank
  - If Amount < 0 → withdrawal column (absolute value), leave deposit blank
  - If Amount = 0 → skip or leave both blank
- Leave blank (not 0) if no value

### Balance Parsing
- **Format A:** Remove $ and commas from Balance column
- **Format B:** `Current balance` is already numeric, rename to `balance`

### Description Cleaning
- **Format A:** Remove card numbers (XXXXX1234), excess whitespace, clean merchant names
- **Format B:** Descriptions are already clean. Preserve vault names exactly (e.g., "From House Vault", "To Seguro del carro Vault")
- Keep essential transaction info

### Category (Leave Empty)
- Set category to empty string
- Categorization happens in the next step via categorize-csv-agent

### Account Name
- Extract from filename: raw_checkings.csv -> checkings
- raw_savings.csv -> savings
- raw_credit.csv -> credit

### Status Filtering (SoFi only)
- Only include transactions with Status = "Posted"
- Skip "Pending" transactions

## Workflow

1. Read the CSV file path from `$ARGUMENTS`
2. Auto-detect the CSV format from headers
3. Parse the bank-format CSV
4. Apply format-specific normalization rules
5. Filter to only include transactions from the target month (derive from parent directory name)
6. Write to normalized_<account>.csv in the same directory
7. The Stop hook will validate the output CSV

## Critical Requirements
- Dates MUST be in YYYY-MM-DD format
- Only include transactions from the target month (derive from directory name)
- Balance column must have numeric values (no $ or commas)
- category column should be empty (will be filled by categorize agent)
- account_name must be populated from the source filename
- Vault names in descriptions must be preserved exactly as-is

## Example
```
/normalize-csv ROOT_OPERATIONS_DIR/mock_dataset_feb_1st_2026/raw_checkings.csv
```
Output: `normalized_checkings.csv` in the same directory
