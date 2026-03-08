---
model: opus
description: Main orchestrator - runs the full agentic finance review workflow
argument-hint: <month> <csv1> [csv2] ...
hooks:
  Stop:
    - hooks:
        - type: command
          command: "uv run \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validators/html-validator.py"
---

# Review Finances

## Purpose

Orchestrate the complete agentic finance review workflow by chaining multiple specialized subagents to process raw bank CSV exports into vault analysis, Excel workbook, and HTML dashboard with financial insights and visualizations.

## Variables

MONTH: $1
CSV_FILES: $2, $3, $4, ... (remaining arguments - file paths or pasted CSV content)
YEAR: `date +%Y` (get current year from CLI)
ROOT_OPERATIONS_DIR: CLAUDE.md: ROOT_OPERATIONS_DIR
MONTH_DIR: ROOT_OPERATIONS_DIR/mock_dataset_{MONTH}_1st_{YEAR}

## Instructions

- First, set up the target directory and ensure raw CSV files are in place
- Chain through each agent in sequential order - do NOT proceed to next agent if current fails
- Wait for each agent to complete before proceeding to the next
- All agents receive MONTH_DIR as their directory path
- Report progress after each step completes
- Do NOT skip any agents in the chain

## Workflow

1. Get current year: `date +%Y`
2. Parse arguments: MONTH and CSV_FILES
3. Construct MONTH_DIR path: `ROOT_OPERATIONS_DIR/mock_dataset_{MONTH}_1st_{YEAR}`
4. Execute the setup and agent chain in order:

### Step 0: Setup Directory and CSV Files

Create or verify the target directory and populate with raw CSV files:

1. Check if MONTH_DIR exists, if not create it with `mkdir -p`
2. Create `assets/` subdirectory if needed
3. For each CSV file provided in CSV_FILES:
   - **Infer account name from filename** if possible:
     - `checkings.csv`, `checking.csv`, `chk.csv`, filename contains `Checking` → `checkings`
     - `savings.csv`, `saving.csv`, `sav.csv`, filename contains `Savings` → `savings`
     - `credit.csv`, `creditcard.csv`, `cc.csv`, filename contains `Credit` or `Apple Card` → `credit`
     - `raw_*.csv` → extract name between `raw_` and `.csv`
     - SoFi filenames: `SOFI-Checking*` → `checkings`, `SOFI-Savings*` → `savings`
   - **If account name cannot be inferred**, use AskUserQuestion:
     ```
     Question: "What account does this CSV represent?"
     Header: "Account"
     Options:
       - "checkings" - Primary checking account
       - "savings" - Savings account
       - "credit" - Credit card account
     ```
   - **If it's a file path** (exists): Copy to MONTH_DIR as `raw_{account_name}.csv`
   - **If it's pasted CSV content**: Write to MONTH_DIR as `raw_{account_name}.csv`
4. Verify at least one `raw_*.csv` file exists in MONTH_DIR

### Agent Chain

#### Step 1: Normalize Agent
Invoke: `Use the normalize-csv-agent to process MONTH_DIR`
- **Input**: raw_*.csv files in MONTH_DIR
- **Output**: normalized_*.csv files (category column empty)

#### Step 2: Categorize Agent
Invoke: `Use the categorize-csv-agent to categorize transactions in MONTH_DIR`
- **Input**: normalized_*.csv files
- **Output**: Same files with category column populated (vault-aware + known_mappings applied)

#### Step 2.5: Flag & Review

Review flagged transactions with the user before proceeding to merge.

1. Check if `ROOT_OPERATIONS_DIR/known_mappings.json` exists. If not, skip this step.
2. Load `flag_rules` from `known_mappings.json`:
   - `amount_threshold`: Flag any transaction with withdrawal > this amount
   - `flag_categories`: Flag transactions assigned to these categories (after categorization)
   - `flag_description_patterns`: Always flag transactions matching these description patterns (case-insensitive)
3. Scan ALL `normalized_*.csv` files in MONTH_DIR for transactions that match ANY flag rule
4. **Do NOT flag vault transfers, vault allocations, or internal transfers** — these are expected movements
5. If no transactions are flagged, skip to Step 3
6. Present flagged transactions to the user via `AskUserQuestion` (batched, max 4 questions at a time):
   - For each flagged transaction, show: date, description, amount, current category, and why it was flagged
   - Ask: "What category should this be?" with options:
     - Keep current category (first option)
     - 2-3 contextually relevant alternative categories
   - The user can also type a custom category via "Other"
7. For each transaction where the user changes the category:
   a. Update the category in the normalized CSV file
   b. Ask: "Should this be added to known_mappings.json as a permanent override?" with options:
     - "Yes — always categorize this way" (add description_contains + amount override)
     - "Yes — for any amount" (add description_contains-only override)
     - "No — just this once"
   c. If user says yes, append the new rule to the `overrides` array in `known_mappings.json`
8. Report summary of flagged items and any changes made

#### Step 3: Merge Agent
Invoke: `Use the merge-accounts-agent to merge accounts in MONTH_DIR`
- **Input**: normalized_*.csv files (now categorized)
- **Output**: agentic_merged_transactions.csv

#### Step 4: Vault Analysis Agent
Invoke: `Use the vault-analyzer-agent to analyze finances in MONTH_DIR`
- **Input**: agentic_merged_transactions.csv + sofi_vault_config.json
- **Output**: vault_analysis.json (income - vaults - sin vault = sobrante)

#### Step 5: Excel Agent
Invoke: `Use the excel-agent to generate the Excel workbook for MONTH_DIR`
- **Input**: vault_analysis.json + agentic_merged_transactions.csv
- **Output**: resumen_quincenal.xlsx (3 sheets: Resumen, Distribucion, Detalle)

#### Step 6: Accumulate
Invoke: `/accumulate-csvs MONTH_DIR`
- **Input**: agentic_merged_transactions.csv
- **Output**: ROOT_OPERATIONS_DIR/agentic_cumulative_dataset_{YEAR}.csv

#### Step 7: Graph Agent (Monthly)
Invoke: `Use the graph-agent to generate visualizations for MONTH_DIR`
- **Input**: agentic_merged_transactions.csv
- **Output**: MONTH_DIR/assets/*.png (8 graphs)

#### Step 8: Graph Agent (Cumulative)
Invoke: `Use the graph-agent to generate visualizations for ROOT_OPERATIONS_DIR using agentic_cumulative_dataset_{YEAR}.csv`
- **Input**: ROOT_OPERATIONS_DIR/agentic_cumulative_dataset_{YEAR}.csv
- **Output**: ROOT_OPERATIONS_DIR/assets/*.png (8 graphs for full year)

#### Step 9: Generative UI Agent (Monthly)
Invoke: `Use the generative-ui-agent to create the dashboard for MONTH_DIR`
- **Input**: CSVs + MONTH_DIR/assets/*.png
- **Output**: MONTH_DIR/index.html

#### Step 10: Generative UI Agent (Cumulative)
Invoke: `Use the generative-ui-agent to create the dashboard for ROOT_OPERATIONS_DIR`
- **Input**: agentic_cumulative_dataset_{YEAR}.csv + ROOT_OPERATIONS_DIR/assets/*.png
- **Output**: ROOT_OPERATIONS_DIR/index.html (yearly dashboard)

#### Step 11: Open Results
Open the generated outputs:
```bash
open MONTH_DIR/resumen_quincenal.xlsx
open -a "Google Chrome" MONTH_DIR/index.html
```

5. Now follow the `Report` section to report the completed work

## Report

Present progress and completion in this format:

## Finance Review: [MONTH] [YEAR]

### Setup
- Directory: [MONTH_DIR]
- Raw files: [list of raw_*.csv files]

### Progress
- [x] Setup: Directory created, [count] CSV files placed
- [x] Normalize: [count] files processed
- [x] Categorize: [count] transactions categorized ([count] vault transfers, [count] sin vault)
- [x] Flag & Review: [count] transactions flagged, [count] recategorized, [count] new mappings added
- [x] Merge: Combined into agentic_merged_transactions.csv
- [x] Vault Analysis: Income $X - Vaults $Y - Sin Vault $Z = Sobrante $W
- [x] Excel: resumen_quincenal.xlsx generated (3 sheets)
- [x] Accumulate: Updated cumulative dataset
- [x] Graph (Monthly): [count] visualizations generated
- [x] Graph (Cumulative): [count] visualizations generated for year
- [x] Dashboard (Monthly): index.html created
- [x] Dashboard (Cumulative): yearly index.html created
- [x] Open: Opened Excel + dashboard

### Vault Summary
| Vault | Allocated | Budget | Diff |
|-------|-----------|--------|------|
| House | $500 | $500 | $0 |
| ... | ... | ... | ... |

**Sin Vault (Variable Expenses): $Z**
**Sobrante: $W**

### Final Deliverables

**Monthly (MONTH_DIR):**
1. `normalized_*.csv` - Clean, normalized transaction files
2. `agentic_merged_transactions.csv` - Combined transactions
3. `vault_analysis.json` - Vault analysis breakdown
4. `resumen_quincenal.xlsx` - Excel workbook (3 sheets)
5. `assets/*.png` - Financial insight graphs
6. `index.html` - Monthly dashboard

**Cumulative (ROOT_OPERATIONS_DIR):**
7. `agentic_cumulative_dataset_{YEAR}.csv` - Yearly cumulative data
8. `assets/*.png` - Yearly insight graphs
9. `index.html` - Yearly dashboard

### Examples
```
# With existing CSV files
/review-finances feb /path/to/SOFI-Checking.csv /path/to/SOFI-Savings.csv

# With just month (if raw files already exist in target dir)
/review-finances jan
```
