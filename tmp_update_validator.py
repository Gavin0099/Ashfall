from __future__ import annotations
import sys
from pathlib import Path

file_path = Path("governance_tools/contract_validator.py")
content = file_path.read_text(encoding="utf-8")

# 1. Update ValidationResult dataclass
new_dataclass = """@dataclass
class ValidationResult:
    compliant: bool
    contract_found: bool
    fields: dict
    metrics: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)"""
content = content.replace("@dataclass\nclass ValidationResult:\n    compliant: bool\n    contract_found: bool\n    fields: dict\n    errors: list[str] = field(default_factory=list)\n    warnings: list[str] = field(default_factory=list)", new_dataclass)

# 2. Update validate_contract signature and logic
old_validate = "def validate_contract(text: str, available_rules: set[str] | None = None) -> ValidationResult:"
new_validate = "def validate_contract(text: str, available_rules: set[str] | None = None, balance_summary_path: Optional[Path] = None, regret_threshold: float = 0.5) -> ValidationResult:"
content = content.replace(old_validate, new_validate)

# 3. Add regret gate check inside validate_contract
regret_check = """    _validate_rules(fields, errors, available=available_rules)
    _validate_choice(fields, "RISK", VALID_RISK_LEVELS, errors)
    _validate_choice(fields, "OVERSIGHT", VALID_OVERSIGHT_LEVELS, errors)
    _validate_choice(fields, "MEMORY_MODE", VALID_MEMORY_MODES, errors)

    metrics = {}
    if balance_summary_path and balance_summary_path.exists():
        try:
            summary = json.loads(balance_summary_path.read_text(encoding="utf-8"))
            regret = summary.get("avg_steps_from_regret_to_death", 0.0)
            metrics["avg_steps_from_regret_to_death"] = regret
            if regret < regret_threshold:
                errors.append(f"Regret gate failed: avg_steps_from_regret_to_death={regret} < {regret_threshold}")
        except Exception as e:
            warnings.append(f"Failed to read balance summary for regret gate: {e}")"""

content = content.replace('    _validate_rules(fields, errors, available=available_rules)\n    _validate_choice(fields, "RISK", VALID_RISK_LEVELS, errors)\n    _validate_choice(fields, "OVERSIGHT", VALID_OVERSIGHT_LEVELS, errors)\n    _validate_choice(fields, "MEMORY_MODE", VALID_MEMORY_MODES, errors)', regret_check)

# 4. Update return ValidationResult
content = content.replace("    return ValidationResult(\n        compliant=len(errors) == 0,\n        contract_found=True,\n        fields=fields,\n        errors=errors,\n        warnings=warnings,\n    )", "    return ValidationResult(\n        compliant=len(errors) == 0,\n        contract_found=True,\n        fields=fields,\n        metrics=metrics,\n        errors=errors,\n        warnings=warnings,\n    )")

# 5. Update format_json
content = content.replace('"warnings": result.warnings,', '"warnings": result.warnings,\n            "metrics": result.metrics,')

file_path.write_text(content, encoding="utf-8")
print("Successfully updated governance_tools/contract_validator.py")
