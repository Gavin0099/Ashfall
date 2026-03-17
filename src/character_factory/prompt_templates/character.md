Generate ONE Fallout-style character as valid JSON matching this schema:
{{SCHEMA}}

HARD CONSTRAINTS:
- background_id must be one of: {{AVAILABLE_BACKGROUNDS}}
- traits must be chosen from: {{AVAILABLE_TRAITS}} (max 2)
- SPECIAL values must sum to exactly {{SPECIAL_TOTAL}}
- starting_resource_bias must include at least one positive AND one negative value (e.g., {"medkits": 2, "food": -2})
- description must NOT contain these words: {{FORBIDDEN_WORDS}}
- structural_weakness field must describe a concrete gameplay limitation (e.g., "Extremely low carrying capacity" or "Susceptible to psychological trauma"), not just a personality trait.
- tags must be a flat list of strings. Include background specific tags and trait tags.

DIVERSITY CONSTRAINTS:
- Already used backgrounds: {{USED_BACKGROUNDS}}
- Already used dominant stats: {{USED_DOMINANT_STATS}}
- Already used traits: {{USED_TRAITS}}

Character Identity:
Create a unique character name and background story that fits the gritty, post-apocalyptic tone of Ashfall. Avoid clichés.

Respond with ONLY the JSON object. No markdown, no explanation.
