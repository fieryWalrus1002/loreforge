# Loreforge Pipeline — Specs Overview

## What This Project Demonstrates

Loreforge is a data engineering portfolio project built on Azure. The domain is tabletop RPG combat data, but the engineering problems are real:

- Ingesting data from **heterogeneous sources** with inconsistent schemas
- **Normalizing** that data to a canonical format via a Python ETL worker
- **Persisting** clean output to Azure Blob Storage in Parquet format
- **Validating** schema contracts at ingestion time with structured logging
- **Deploying** infrastructure reproducibly via Bicep and CI/CD via GitHub Actions

## Intentional Dirty Data

The raw source files (`data/raw/`) deliberately simulate the kind of schema inconsistency found in real-world data engineering — different teams, different vintages of data, different conventions. The pipeline's job is to detect, log, and resolve these inconsistencies on the way to the canonical schema.

Known inconsistencies in the raw sources (by design):

| Field (canonical) | Variant found in raw data | Source |
|---|---|---|
| `tr_die` | `t_die` | `bestiary.json` (Clanker entry) |
| `tr_mult` | `t_rate` | `bestiary.json` (Clanker entry) |
| `hd` | string in bestiary, integer in roster; `"1 HP"` in text tables means fixed HP=1, hd=1 | all sources |
| `id` | no consistent generation strategy | roster |
| `ml`, `save` | absent on PC entries vs explicit on NPC entries | roster |

## Spec Index

- [01_raw_sources.md](./01_raw_sources.md) — raw input schemas and known inconsistencies
- [02_canonical_schema.md](./02_canonical_schema.md) — normalized target schema
- [03_pipeline_worker.md](./03_pipeline_worker.md) — worker requirements and acceptance criteria
- [04_text_parser.md](./04_text_parser.md) — rules for parsing mixed prose/tabular `.txt` sources
