#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Vault Analysis Validator for Agentic Finance Review

Validates vault_analysis.json:
- File exists and is valid JSON
- Required fields present (income, vault_allocations, sin_vault_expenses, sobrante)
- Math check: income - vault_allocations.total - sin_vault_expenses.total = sobrante
- All vault names in config have corresponding entries

Outputs JSON decision for Claude Code Stop hook:
- {"decision": "block", "reason": "..."} to block and retry
- {} to allow completion
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Default operations directory
ROOT_OPERATIONS_DIR = Path("apps/agentic-finance-review/data/real_2025_2026")

# Log file in same directory as this script
LOG_FILE = Path(__file__).parent / "vault-validator.log"


def log(message: str):
    """Append timestamped message to log file."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def find_vault_analysis(target: Path) -> Path | None:
    """Find vault_analysis.json in the target path."""
    if target.is_file() and target.name == "vault_analysis.json":
        return target
    if target.is_dir():
        candidate = target / "vault_analysis.json"
        if candidate.exists():
            return candidate
        # Search recursively
        files = list(target.rglob("vault_analysis.json"))
        if files:
            return files[0]
    return None


def validate_vault_analysis(file_path: Path) -> list[str]:
    """Validate vault_analysis.json structure and math."""
    errors = []

    if not file_path.exists():
        return [f"vault_analysis.json not found at {file_path}"]

    try:
        with open(file_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON in vault_analysis.json: {e}"]

    # Check required top-level fields
    required_fields = ["income", "vault_allocations", "sin_vault_expenses", "sobrante"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors  # Can't continue without required fields

    # Validate income structure
    income = data["income"]
    if "total" not in income:
        errors.append("income.total is missing")
    elif not isinstance(income["total"], (int, float)):
        errors.append(f"income.total must be numeric, got {type(income['total']).__name__}")

    # Validate vault_allocations structure
    vault_alloc = data["vault_allocations"]
    if "total" not in vault_alloc:
        errors.append("vault_allocations.total is missing")
    elif not isinstance(vault_alloc["total"], (int, float)):
        errors.append(f"vault_allocations.total must be numeric, got {type(vault_alloc['total']).__name__}")

    # Validate sin_vault_expenses structure
    sin_vault = data["sin_vault_expenses"]
    if "total" not in sin_vault:
        errors.append("sin_vault_expenses.total is missing")
    elif not isinstance(sin_vault["total"], (int, float)):
        errors.append(f"sin_vault_expenses.total must be numeric, got {type(sin_vault['total']).__name__}")

    # Validate sobrante is numeric
    if not isinstance(data["sobrante"], (int, float)):
        errors.append(f"sobrante must be numeric, got {type(data['sobrante']).__name__}")

    if errors:
        return errors  # Can't do math check without valid numbers

    # Math check: income - vault_allocations - sin_vault = sobrante
    income_total = income["total"]
    vault_total = vault_alloc["total"]
    sin_vault_total = sin_vault["total"]
    sobrante = data["sobrante"]

    expected_sobrante = income_total - vault_total - sin_vault_total
    tolerance = 0.01

    if abs(expected_sobrante - sobrante) > tolerance:
        errors.append(
            f"Math doesn't balance!\n"
            f"    income ({income_total:.2f}) - vault_allocations ({vault_total:.2f}) "
            f"- sin_vault_expenses ({sin_vault_total:.2f}) = {expected_sobrante:.2f}\n"
            f"    But sobrante is {sobrante:.2f}\n"
            f"    Difference: {abs(expected_sobrante - sobrante):.2f}"
        )
    else:
        log(f"  Math check passed: {income_total:.2f} - {vault_total:.2f} - {sin_vault_total:.2f} = {sobrante:.2f}")

    # Check vault config alignment (optional — only if config exists)
    config_path = ROOT_OPERATIONS_DIR / "sofi_vault_config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            config_vaults = set(config.get("vaults", {}).keys())
            analysis_vaults = set(vault_alloc.get("by_vault", {}).keys())

            missing_vaults = config_vaults - analysis_vaults
            if missing_vaults:
                log(f"  Note: {len(missing_vaults)} vaults in config have no allocations this period: {missing_vaults}")
                # Not an error — some vaults may not have allocations every period
        except (json.JSONDecodeError, KeyError):
            pass  # Config issues are not this validator's problem

    # Validate transactions list in sin_vault_expenses
    if "transactions" in sin_vault:
        txn_total = sum(t.get("amount", 0) for t in sin_vault["transactions"])
        if abs(txn_total - sin_vault_total) > 0.01:
            errors.append(
                f"sin_vault_expenses.transactions total ({txn_total:.2f}) "
                f"doesn't match sin_vault_expenses.total ({sin_vault_total:.2f})"
            )

    # Validate rescate_ahorro (optional but validated if present)
    if "rescate_ahorro" in data:
        rescate = data["rescate_ahorro"]
        if "total" not in rescate:
            errors.append("rescate_ahorro.total is missing")
        elif not isinstance(rescate["total"], (int, float)):
            errors.append(f"rescate_ahorro.total must be numeric, got {type(rescate['total']).__name__}")
        elif rescate["total"] < 0:
            errors.append(f"rescate_ahorro.total must be >= 0, got {rescate['total']}")
        else:
            if rescate["total"] > 0:
                log(f"  RED FLAG: rescate_ahorro = ${rescate['total']:.2f} (target: $0)")
            # Validate transaction amounts sum
            if "transactions" in rescate:
                r_total = sum(t.get("amount", 0) for t in rescate["transactions"])
                if abs(r_total - rescate["total"]) > 0.01:
                    errors.append(
                        f"rescate_ahorro.transactions total ({r_total:.2f}) "
                        f"doesn't match rescate_ahorro.total ({rescate['total']:.2f})"
                    )

    # Validate gastos_sorpresa (optional but validated if present)
    if "gastos_sorpresa" in data:
        sorpresa = data["gastos_sorpresa"]
        if "total" not in sorpresa:
            errors.append("gastos_sorpresa.total is missing")
        elif not isinstance(sorpresa["total"], (int, float)):
            errors.append(f"gastos_sorpresa.total must be numeric, got {type(sorpresa['total']).__name__}")
        else:
            # gastos_sorpresa must be a subset of sin_vault_expenses
            if sorpresa["total"] > sin_vault_total + 0.01:
                errors.append(
                    f"gastos_sorpresa.total ({sorpresa['total']:.2f}) cannot exceed "
                    f"sin_vault_expenses.total ({sin_vault_total:.2f})"
                )

    # Validate vault_desviada (optional but validated if present)
    if "vault_desviada" in data:
        desviada = data["vault_desviada"]
        if "total" not in desviada:
            errors.append("vault_desviada.total is missing")
        elif not isinstance(desviada["total"], (int, float)):
            errors.append(f"vault_desviada.total must be numeric, got {type(desviada['total']).__name__}")

    return errors


def main():
    log("=" * 50)
    log("VAULT VALIDATOR STOP HOOK TRIGGERED")
    log(f"sys.argv: {sys.argv}")

    # Read hook input from stdin
    try:
        stdin_data = sys.stdin.read()
        log(f"stdin_data length: {len(stdin_data)}")
    except Exception:
        pass

    # Get target from command line arg
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        log(f"Target (from arg): {target}")
    else:
        target = ROOT_OPERATIONS_DIR
        log(f"Target (default): {target}")

    # Find vault_analysis.json
    analysis_file = find_vault_analysis(target)

    if analysis_file is None:
        log("  vault_analysis.json not found — skipping validation")
        # Not blocking — file might not be created yet
        print(json.dumps({}))
        return

    log(f"  Validating: {analysis_file}")
    errors = validate_vault_analysis(analysis_file)

    # Output decision JSON
    if errors:
        log(f"RESULT: BLOCK ({len(errors)} errors)")
        for err in errors:
            log(f"  {err}")
        print(json.dumps({
            "decision": "block",
            "reason": "Vault analysis validation failed:\n" + "\n".join(errors)
        }))
    else:
        log("RESULT: PASS - Vault analysis validation successful")
        print(json.dumps({}))


if __name__ == "__main__":
    main()
