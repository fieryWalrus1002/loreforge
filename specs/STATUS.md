# Loreforge — Project Status

_Last updated: 2026-04-25_

---

## Summary

The Python ETL pipeline is complete and green in CI. Infrastructure is fully defined in Bicep. The remaining gap between specs and reality is the **output layer**: the specs call for Parquet files written to Azure Blob Storage; what we have is PostgreSQL. That gap is the natural next focus.

---

## What Is Done

### Python Pipeline (`src/`)

| Component | Status | Notes |
|---|---|---|
| Bestiary ingestor | ✅ Done | Reads new nested-stats schema; maps all attack field variants |
| Roster ingestor | ✅ Done | PC/NPC split; source_id preserved; canonical ULID IDs generated |
| Text-table ingestor | ✅ Done | Mixed prose/table `.txt` files; all compound cell rules; dead-letter on bad rows |
| Schema validation | ✅ Done | `coerce_int`, `default_hp`, field remapping, asterisk stripping, bare-die normalization |
| Dead-letter logging | ✅ Done | Unparseable records captured with raw content and reason; never silently dropped |
| Structured logging | ✅ Done | `structlog` JSON output throughout; timestamps, levels, source file on all entries |
| DB writer | ✅ Done | psycopg3; `creatures`, `characters`, `attacks`, `dead_letters`, `pipeline_runs` tables; `ON CONFLICT DO NOTHING` |
| Worker orchestration | ✅ Done | Scans `data/raw/`, dispatches to matching ingestor, writes totals, logs run summary |
| Parquet output | ❌ Not started | Spec calls for Parquet → Azure Blob; currently PostgreSQL only |
| Azure Blob upload | ❌ Not started | `canonical-data` container exists in Bicep but nothing writes to it |

### Tests (`tests/`)

47 tests, all passing. Coverage across all three ingestors plus schema validation utilities.

| File | Tests | What it covers |
|---|---|---|
| `test_bestiary.py` | 10 | Parsing, HP default, type coercion, dead letters, unique IDs, attack mapping |
| `test_roster.py` | 9 | Parsing, PC/NPC split, source_id preservation, attacks, missing HP dead letter |
| `test_schema.py` | 11 | `coerce_int`, `default_hp`, `normalize_tr`, `strip_annotation`, `remap_attack_fields` |
| `test_text_table.py` | 17 | All text-table compound cell rules, shock/TR/HD parsing, prose extraction, dead letters |

### Infrastructure (`infra/`)

| Resource | Status | Notes |
|---|---|---|
| PostgreSQL Flexible Server | ✅ Defined | Standard_B1ms burstable, v16, 32GB, firewall open to Azure services |
| Azure Container Registry | ✅ Defined | Basic SKU; admin user enabled |
| Container Apps Job | ✅ Defined | Manual trigger; `DATABASE_URL` injected via env; 0.5 CPU / 1Gi |
| Container Apps Environment | ✅ Defined | Linked to Log Analytics |
| Storage Account (Data Lake Gen2) | ✅ Defined | `raw-data` + `canonical-data` containers |
| Log Analytics workspace | ✅ Defined | 30-day retention |
| DB schema | ✅ Defined | `infra/db/schema.sql`; includes CHECK constraint enforcing attack ownership |
| Bicep deploy command | ✅ Documented | In `infra/main.bicep` header comment |

### CI/CD (`github/workflows/`)

| Step | Status | Notes |
|---|---|---|
| Lint (`ruff`) | ✅ Green | Runs on push + PR to main |
| Type check (`mypy`) | ✅ Green | `--ignore-missing-imports` |
| Tests (`pytest`) | ✅ Green | 47/47 passing after today's schema fix |
| Docker build | ✅ Green | Image builds but is not pushed or deployed |
| CD — push image to ACR | ❌ Not started | No workflow step for ACR auth or push |
| CD — Bicep deploy | ❌ Not started | No deploy-on-merge workflow |

---

## Spec Gaps and Drift

### `01_raw_sources.md` — STALE for bestiary

The spec describes the old flat bestiary schema with string fields (`"hd": "6"`, `"atk": "+9x3"`, etc.). The actual `bestiary.json` on disk has a completely different shape:

- Stats are nested under a `"stats"` key (now integers)
- Attacks use `atk_bonus` (int), `damage`, `trauma_die`, `trauma_mult`, `shock_value`, `shock_threshold`, `num_attacks`
- No more `t_die`/`t_rate` field-name inconsistency (that "dirty data" was the old schema)

The ingestor was updated today to match reality. The spec should be updated to reflect the current schema if it's being used as reference. The roster spec is still accurate.

### `02_canonical_schema.md` — Output section not implemented

The spec says:

> **File format:** Parquet  
> **Location:** Azure Blob Storage container `loreforge-canonical`  
> **Partitioning:** `source={bestiary|roster}/date={YYYY-MM-DD}/`

None of this exists. The worker writes to PostgreSQL. PostgreSQL is actually more useful for this domain (queryable, relational), but it wasn't the original plan and the Blob write path is the primary portfolio signal for data lake / data engineering patterns. Both should eventually exist.

### `02_canonical_schema.md` — Shock field shape

The spec defines `"shock": "string | null"` (e.g. `"3/AC 15"`). The implementation splits this into `shock_dmg: int | None` and `shock_ac: int | None` at parse time. This is better design (more queryable, no re-parsing needed downstream) but diverges from the spec. The spec should be updated.

### `04_text_parser.md` — HP resolution timing

The spec says `hp=null` for non-fixed HD entries (rolling happens in the combat tracker). The implementation resolves `hp = floor(4.5 * hd)` immediately at ingest time. The spec's own HD/HP table explicitly documents `floor(4.5 * hd)` as the default, so this is the correct behavior — the acceptance criteria bullet is the stale part.

---

## What's Next (Priority Order)

### 1. Parquet writer + Blob upload (closes the output gap)

Add `src/output/parquet_writer.py` using `pyarrow`. Partition output under `source={name}/date={YYYY-MM-DD}/`. Upload to the `canonical-data` Blob container using `azure-storage-blob`. This is the highest-value missing piece for the portfolio signal: landing zone → normalize → data lake.

### 2. CD workflow (closes the GitHub Actions gap)

Two steps:
- On merge to `main`: build Docker image, push to ACR (needs `AZURE_CLIENT_ID` / OIDC or `ACR_PASSWORD` secret)
- On merge to `main`: deploy Bicep via `azure/login` + `az deployment group create`

This demonstrates end-to-end GitOps and is a primary signal for the role.

### 3. Update stale specs

`01_raw_sources.md` should document the current bestiary schema. `02_canonical_schema.md` shock field and output section should be updated.

### 4. LLM extraction angle (differentiator)

`04_text_parser.md` already calls this out as a future spec (`05_llm_extraction.md`). Passing raw prose ability descriptions through the Claude API with a schema prompt, then validating the structured response, would demonstrate MLOps/LLMOps thinking directly relevant to the role's secondary requirements. Low implementation cost given the pipeline architecture already handles it (just a new output field on `special_abilities`).

### 5. DB migration automation

Currently `infra/db/schema.sql` must be run manually. Adding a startup step to the Container App Job (or a separate migration job) that applies the schema via `psql` would round out the infra story.
