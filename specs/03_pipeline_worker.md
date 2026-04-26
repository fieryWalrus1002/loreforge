# Pipeline Worker Requirements

## Responsibility

The worker reads raw JSON sources, validates and normalizes them to the canonical schema, and writes Parquet output to Azure Blob Storage. It is a batch process — one run processes all sources and exits.

## Acceptance Criteria

### Ingestion

- [ ] Worker reads all `.json` files from `data/raw/`
- [ ] Each source file is processed independently — failure in one does not abort others
- [ ] Source filename is recorded in pipeline run metadata

### Validation

- [ ] Missing required fields (e.g. `name`, `hp`, `ac`) raise a logged error and skip the entry
- [ ] Type mismatches on coercible fields (e.g. `hd` as string) are coerced and logged as warnings
- [ ] Unrecognized field name variants (e.g. `t_die` instead of `tr_die`) are remapped and logged as warnings
- [ ] Entries that cannot be normalized are written to a dead-letter log, not silently dropped

### Normalization

- [ ] All normalization rules in [02_canonical_schema.md](./02_canonical_schema.md) are applied
- [ ] Output entries contain no absent optional fields — all optional fields are explicit nulls
- [ ] IDs that don't match `{type}_{ulid}` format are regenerated and original ID is preserved in `source_id`

### Output

- [ ] Clean records are written to Parquet
- [ ] Output is uploaded to Azure Blob Storage under `loreforge-canonical/source={name}/date={YYYY-MM-DD}/`
- [ ] A run summary is logged: records read, records written, warnings, errors

### Observability

- [ ] All log output is structured JSON (not plaintext)
- [ ] Log entries include: `timestamp`, `level`, `source_file`, `record_id`, `message`
- [ ] Pipeline run duration is logged on exit

## Out of Scope

- Game logic (combat resolution, initiative, attack rolls)
- Any UI or API layer
- Streaming / real-time ingestion — this is batch only
