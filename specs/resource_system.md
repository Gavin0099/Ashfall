# Resource System

## Resources

The game tracks five player-facing resource/state values:

- Food
- Ammo
- Medkits
- Scrap
- Radiation

---

## Resource Rules

Food:
- Consumed when entering a node
- If food reaches 0, player dies

Ammo:
- Required for attacks

Medkits:
- Restore player HP

Scrap:
- Reserve currency/resource for future progression hooks

Radiation:
- Persistent irreversible state in v0.1
- Gained from high-risk environmental or scavenging choices
- Not removed by medkits
- Each move while `radiation > 0` deals 1 HP travel attrition
- If HP reaches 0 while irradiated, death reason should remain attributable as `radiation_death`
