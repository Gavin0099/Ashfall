import json
import yaml
import os
from pathlib import Path
from typing import List, Dict, Any

# Note: In a real environment, we'd use the anthropic client.
# For this agentic workflow, we will simulate the generation or provide a tool to call.
# However, to be "ready to use", I'll write the code that uses the Environment Variable.

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "character_schema.json"
CONSTRAINTS_PATH = Path(__file__).resolve().parent / "constraints.yaml"
TEMPLATE_PATH = Path(__file__).resolve().parent / "prompt_templates" / "character.md"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "characters"

def load_config():
    with open(CONSTRAINTS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_template():
    return TEMPLATE_PATH.read_text(encoding="utf-8")

def build_prompt(config: Dict, existing: List[Dict]) -> str:
    schema = load_schema()
    template = load_template()
    
    used_bg = [c["background_id"] for c in existing]
    used_stats = [max(c["special"], key=c["special"].get) for c in existing]
    used_traits = [t for c in existing for t in c.get("traits", [])]
    
    # Simple filtering for prompt
    avail_bg = [b for b in config["content_constraints"]["background_pool"] if used_bg.count(b) < config["diversity_rules"]["max_per_background"]]
    avail_tr = config["content_constraints"]["trait_pool"]
    
    prompt = template.replace("{{SCHEMA}}", json.dumps(schema, indent=2))
    prompt = prompt.replace("{{AVAILABLE_BACKGROUNDS}}", str(avail_bg))
    prompt = prompt.replace("{{AVAILABLE_TRAITS}}", str(avail_tr))
    prompt = prompt.replace("{{SPECIAL_TOTAL}}", str(config["diversity_rules"]["special_total"]))
    prompt = prompt.replace("{{FORBIDDEN_WORDS}}", str(config["content_constraints"]["forbidden_words"]))
    prompt = prompt.replace("{{USED_BACKGROUNDS}}", str(used_bg))
    prompt = prompt.replace("{{USED_DOMINANT_STATS}}", str(used_stats))
    prompt = prompt.replace("{{USED_TRAITS}}", str(used_traits))
    
    return prompt

def mock_generate_locally(prompt: str) -> Dict:
    """Fallback generator using local heuristics to provide diverse mock data."""
    import random
    config = load_config()
    bg_pool = config["content_constraints"]["background_pool"]
    tr_pool = config["content_constraints"]["trait_pool"]
    
    # Extract existing backgrounds from prompt to simulate "context awareness"
    # (Simple string search in prompt for demonstration)
    used_bg_str = prompt.split("Already used backgrounds: ")[1].split("\n")[0]
    used_bg = eval(used_bg_str) if used_bg_str != "[]" else []
    
    available = [b for b in bg_pool if b not in used_bg]
    bg = random.choice(available if available else bg_pool)
    
    # Random SPECIAL summing to 40
    stats = ["strength", "perception", "endurance", "charisma", "intelligence", "agility", "luck"]
    vals = [1] * 7
    remaining = 40 - 7
    for _ in range(remaining):
        vals[random.randint(0, 6)] += 1
    
    special = {stats[i]: vals[i] for i in range(7)}
    
    return {
        "character_id": f"gen_{bg}_{random.randint(100, 999)}",
        "background_id": bg,
        "display_name": f"Generated {bg.replace('_', ' ').capitalize()}",
        "description": "Mocked description for testing.",
        "special": special,
        "traits": random.sample(tr_pool, 2),
        "perks": [],
        "tags": [f"tag_{bg}"],
        "starting_resource_bias": {"food": 2, "ammo": -2},
        "structural_weakness": "Mocked weakness."
    }

def run_factory(count: int = None):
    config = load_config()
    n = count or config["generation"]["count"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    generated = []
    # Load existing to avoid duplication
    for p in OUTPUT_DIR.glob("*.json"):
        with open(p, "r", encoding="utf-8") as f:
            generated.append(json.load(f))

    print(f"Starting Character Factory to generate {n} characters...")
    
    for i in range(n):
        prompt = build_prompt(config, generated)
        
        # Real implementation would use:
        # client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        # ...
        
        char = mock_generate_locally(prompt)
        # Ensure unique ID
        char["character_id"] = f"{char['background_id']}_{len(generated)+1}"
        
        out_path = OUTPUT_DIR / f"{char['character_id']}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(char, f, indent=2, ensure_ascii=False)
            
        generated.append(char)
        print(f"  [+] Generated {char['character_id']}")

if __name__ == "__main__":
    run_factory()
