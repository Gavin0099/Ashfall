import json
try:
    import jsonschema
except ImportError:
    jsonschema = None

from pathlib import Path
from collections import Counter

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "character_schema.json"
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "characters"

def basic_validate(data, schema):
    """Fallback validation if jsonschema is missing."""
    required = schema.get("required", [])
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    return True

def validate_diversity_and_schema() -> bool:
    if not SCHEMA_PATH.exists():
        print(f"Error: Schema not found at {SCHEMA_PATH}")
        return False

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    characters = []
    errors = []

    if not DATA_DIR.exists():
        print("Warning: No character data directory found.")
        return True

    for p in DATA_DIR.glob("*.json"):
        with open(p, "r", encoding="utf-8") as f:
            try:
                char = json.load(f)
                if jsonschema:
                    jsonschema.validate(char, schema)
                else:
                    basic_validate(char, schema)
                characters.append(char)
            except Exception as e:
                errors.append(f"Validation failed for {p.name}: {e}")

    if not characters:
        print("No characters to validate.")
        return True

    # Check SPECIAL totals
    for char in characters:
        total = sum(char["special"].values())
        if total != 40:
            errors.append(f"Character {char['character_id']} SPECIAL total is {total}, expected 40")

    # Check Resource Trade-offs
    for char in characters:
        bias = char.get("starting_resource_bias", {})
        has_pos = any(v > 0 for v in bias.values())
        has_neg = any(v < 0 for v in bias.values())
        if not (has_pos and has_neg):
            errors.append(f"Character {char['character_id']} lacks resource trade-off (bias: {bias})")

    # Diversity Audit
    bg_counts = Counter(c["background_id"] for c in characters)
    dominant_stats = Counter(max(c["special"], key=c["special"].get) for c in characters)
    
    if bg_counts.most_common(1) and bg_counts.most_common(1)[0][1] > 3:
        errors.append(f"Diversity failure: Role {bg_counts.most_common(1)[0][0]} is over-represented")

    if len(dominant_stats) < 2 and len(characters) >= 5:
         errors.append(f"Diversity failure: Only {len(dominant_stats)} dominant stats found across {len(characters)} characters")

    if errors:
        print("--- Character Factory Validation Errors ---")
        for err in errors:
            print(f"  [!] {err}")
        return False

    print(f"SUCCESS: {len(characters)} characters passed schema and diversity checks.")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if validate_diversity_and_schema() else 1)
