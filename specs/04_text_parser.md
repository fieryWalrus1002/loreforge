# Text Parser Requirements

Handles `.txt` files containing mixed prose and tabular data, as produced by copy-pasting from a PDF rulebook.

## Input Structure

A text file may contain, in any order:

- `#` comment lines — strip and ignore
- Descriptive prose paragraphs — creature lore, special ability descriptions
- A **stat table** — the primary structured data target, identified by a header line containing `HD AC Atk`

## Stage 1 — Preprocessing

- [ ] Strip all lines beginning with `#`
- [ ] Preserve line numbers in metadata for debugging

## Stage 2 — Table Detection and Parsing

The stat table is identified by a header line matching the pattern:

```
<creature type>  HD  AC  Atk  Dmg  TR  Shock  MV  ML  Skill  Save
```

All lines between the header and the next blank line (or end of file) are data rows.

### Compound Cell Parsing Rules

| Column | Raw example | Parsed result | Rule |
|---|---|---|---|
| `HD` | `4` | `{"hd": 4, "hp": null}` | Standard: HP rolled as `hd`d8 at runtime |
| `HD` | `1 HP` | `{"hd": 1, "hp": 1}` | Fixed HP given explicitly — use it, assume 1 HD |
| `Atk` | `+3` | `{"atk": "+3", "num_attacks": 1}` | Single attack |
| `Atk` | `+6x2` | `{"atk": "+6", "num_attacks": 2}` | `x{n}` suffix = number of attacks |
| `Atk` | `+5x3` | `{"atk": "+5", "num_attacks": 3}` | Same |
| `Dmg` | `1d8 bite` | `{"dmg": "1d8", "dmg_type": "bite"}` | Trailing word = damage type |
| `Dmg` | `1d6+2 claw` | `{"dmg": "1d6+2", "dmg_type": "claw"}` | Modifier included in dmg |
| `Dmg` | `1d6+poison` | `{"dmg": "1d6", "dmg_type": "bite", "poison": true}` | `+poison` is a flag, not a modifier |
| `Dmg` | `1d6+ bite` | `{"dmg": "1d6", "dmg_type": "bite"}` | Trailing `+` is a PDF artifact — strip it |
| `TR` | `1d8/x2` | `{"tr_die": "1d8", "tr_mult": "x2"}` | Split on `/` |
| `Shock` | `3/-` | `{"shock_dmg": 3, "shock_ac": null}` | `dmg/-` means shock applies regardless of AC |
| `Shock` | `-` | `{"shock_dmg": null, "shock_ac": null}` | No shock |

### HD and HP Rule

The pipeline always resolves `hp` to a concrete integer. Rolling happens later, in the combat tracker.

- `hd` — always an integer (number of hit dice), minimum 1
- `hp` — explicit integer from source if given; otherwise `floor(4.5 * hd)` as the default average

```
"1 HP" → hd=1, hp=1               (explicit HP from source)
"4"    → hd=4, hp=floor(4.5*4)=18 (default average)
"3"    → hd=3, hp=floor(4.5*3)=13 (default average)
"1"    → hd=1, hp=floor(4.5*1)=4  (default average)
```

When the combat tracker instantiates a creature, it will roll `hd`d8 to get the actual combat HP, overwriting the default. The canonical bestiary record is a template, not a live combatant.

## Stage 3 — Prose Extraction (Optional)

Special ability blocks follow the pattern:

```
<Ability Name>: <description text, possibly spanning multiple lines>
```

These can be extracted as unstructured text and stored in a `special_abilities` list on the creature record. Full structured parsing of ability mechanics is out of scope for the base pipeline.

### LLM Extraction (Future)

Structured parsing of prose ability descriptions (damage, save types, conditions) is a candidate for Claude API extraction. If implemented, each ability description is passed to the API with a schema prompt, and the returned JSON is validated before storage. See `specs/05_llm_extraction.md` (future).

## Acceptance Criteria

- [ ] Comment lines are stripped before any other processing
- [ ] Table header line is detected reliably regardless of surrounding prose
- [ ] All compound cell rules in the table above are applied
- [ ] `1 HP` entries produce `hd=1, hp=1`; all other HD values produce `hp=null`
- [ ] PDF artifacts (trailing `+`, hyphenation in prose) are handled without breaking parsing
- [ ] Rows that cannot be parsed emit a dead-letter log entry with the raw line and reason
- [ ] Prose special ability text is extracted and stored as raw strings on the record
