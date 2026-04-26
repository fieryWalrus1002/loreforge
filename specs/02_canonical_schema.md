# Canonical Schema

This is the normalized target schema that the pipeline produces. All raw source inconsistencies are resolved before writing output.

## Combatant

```json
{
  "id": "string",             // format: {type}_{ulid}, e.g. "pc_01J4...", "npc_01J4..."
  "name": "string",           // uppercased, stripped
  "is_pc": "boolean",
  "hp": "integer",            // resolved at ingest: explicit value from source, or floor(4.5 * hd)
  "max_hp": "integer",        // same value as hp at ingest; combat tracker may diverge after rolling
  "system_strain": "integer",
  "attributes": {
    "str": "integer",
    "dex": "integer",
    "con": "integer",
    "int": "integer",
    "wis": "integer",
    "cha": "integer"
  },
  "ac": "integer",
  "hd": "integer",            // always integer — coerced from string if needed
  "mv": "string | null",
  "ml": "integer | null",     // always integer — coerced from string if needed
  "skill": "string",
  "save": "string | null",
  "initiative_mod": "integer",
  "current_init": "integer",
  "is_active": "boolean",
  "is_dead": "boolean",
  "attacks": [ <attack> ]
}
```

## Attack

All attack entries normalized to this shape regardless of weapon type. Optional fields are explicit nulls rather than absent keys.

```json
{
  "name": "string",
  "atk": "string",
  "dmg": "string",
  "tr_die": "string | null",    // normalized from t_die
  "tr_mult": "string | null",   // normalized from t_rate
  "shock": "string | null",
  "range": "string | null",
  "mag": "integer | null",
  "attr": "string | null",
  "tl": "integer | null",
  "enc": "integer | null"
}
```

## Normalization Rules

| Raw field | Raw type | Canonical field | Canonical type | Rule |
|---|---|---|---|---|
| `hd` | string or integer | `hd` | integer | `int(value)`; minimum 1 |
| `hd` + fixed HP (e.g. `"1 HP"`) | string | `hd=1, hp=1` | integer | Fixed HP wins; assume 1 HD |
| `hp` | absent | `hp` | integer | Default: `floor(4.5 * hd)` |
| `ac` | string or integer | `ac` | integer | `int(value)` |
| `ml` | string or integer or null | `ml` | integer or null | `int(value)` if present |
| `t_die` | string | `tr_die` | string | rename |
| `t_rate` | string | `tr_mult` | string | rename |
| absent optional attack fields | absent | all attack fields | null | fill with null |
| `id` | inconsistent string | `id` | `{type}_{ulid}` | regenerate if non-conforming |

## Output Format

- **File format:** Parquet
- **Location:** Azure Blob Storage container `loreforge-canonical`
- **Partitioning:** `source={bestiary|roster}/date={YYYY-MM-DD}/`
- **One file per pipeline run per source**
