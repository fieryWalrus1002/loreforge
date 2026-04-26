# Raw Data Sources

These files represent upstream data as delivered — inconsistent, incomplete in places, and not yet fit for analysis. The pipeline treats them as read-only inputs.

## `data/raw/bestiary.json`

A catalogue of creature stat blocks. Each entry represents a combatant template.

```json
{
  "name": "string",
  "hd": "string",         // hit dice — stored as string, e.g. "6"
  "ac": "string",         // armor class — stored as string, e.g. "15"
  "mv": "string",         // movement, e.g. "15m"
  "ml": "string",         // morale — stored as string, e.g. "9"
  "skill": "string",      // skill modifier, e.g. "+3"
  "save": "string",       // save target, e.g. "12+"
  "t_target": "integer",
  "attacks": [ <attack> ]
}
```

### Attack sub-schema (bestiary)

Most entries:
```json
{
  "name": "string",
  "atk": "string",
  "dmg": "string",
  "tr_die": "string",
  "tr_mult": "string",
  "shock": "string"
}
```

**Known variant — Clanker entry uses different field names:**
```json
{
  "name": "string",
  "atk": "string",
  "dmg": "string",
  "t_die": "string",      // ⚠ should be tr_die
  "t_rate": "string",     // ⚠ should be tr_mult
  "tl": "integer",
  "enc": "integer"
}
```

Ranged weapon entries also include: `range`, `mag`, `attr`, `tl`, `enc`.

---

## `data/raw/roster.json`

The active combat roster — a mix of player characters (PCs) and NPCs instantiated from bestiary templates.

```json
{
  "id": "string",             // ⚠ no consistent generation strategy
  "name": "string",
  "is_pc": "boolean",
  "hp": "integer",
  "max_hp": "integer",
  "system_strain": "integer",
  "attributes": {
    "str": "integer", "dex": "integer", "con": "integer",
    "int": "integer", "wis": "integer", "cha": "integer"
  },
  "ac": "integer",
  "attacks": [ <attack> ],
  "skill": "string",
  "hd": "integer",            // ⚠ integer here, string in bestiary
  "mv": "string | null",      // null on PC entries
  "ml": "string | null",      // null on PC entries
  "save": "string | null",    // null on PC entries
  "initiative_mod": "integer",
  "current_init": "integer",
  "is_active": "boolean",
  "is_dead": "boolean"
}
```

### Known inconsistencies

| Issue | Detail |
|---|---|
| `hd` type mismatch | String in bestiary (`"6"`), integer in roster (`6`) |
| Null combat fields on PCs | `mv`, `ml`, `save` are null for PC entries — NPCs populate these from bestiary |
| ID format | `"unit_1776108236020"`, `"pc_01"`, `"tiger_415"` — no single strategy |
| Missing fields | Some attack entries omit `shock`, `range`, `tr_die` etc. depending on weapon type |
