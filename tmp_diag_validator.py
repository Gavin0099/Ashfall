import json
from pathlib import Path
from governance_tools.contract_validator import validate_contract

def make_contract(**overrides):
    fields = {
        "LANG": "C++",
        "LEVEL": "L2",
        "SCOPE": "feature",
        "PLAN": "PLAN.md",
        "LOADED": "SYSTEM_PROMPT, HUMAN-OVERSIGHT",
        "CONTEXT": "Ashfall route balance -> governance checks; NOT: renderer work",
        "PRESSURE": "SAFE (45/200)",
        "RULES": "user_global",
        "RISK": "low",
        "OVERSIGHT": "auto",
        "MEMORY_MODE": "stateless",
    }
    fields.update(overrides)
    body = "\n".join(f"{key} = {value}" for key, value in fields.items())
    return f"[Governance Contract]\n{body}\n"

text = make_contract()
result = validate_contract(text)
print(f"Compliant: {result.compliant}")
print(f"Errors: {result.errors}")
print(f"Warnings: {result.warnings}")
