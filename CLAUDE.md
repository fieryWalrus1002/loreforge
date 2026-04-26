# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Loreforge is a toy project exploring Azure Bicep workflows, built around a tabletop RPG combat/campaign management system. The game system follows d20/WWN (Worlds Without Number) conventions.

## Architecture

```
data/        # JSON game data (bestiary, combat roster)
src/         # Python source (worker.py — currently a placeholder)
infra/       # Azure infrastructure (main.bicep — currently a placeholder)
```

The intended shape is a Python worker reading game data from `data/`, with Azure infrastructure defined in `infra/main.bicep`.

## Data Schemas

**Bestiary entry** (`data/bestiary.json`):
```json
{
  "name": "...",
  "hd": "6",          // hit dice
  "ac": "15",         // armor class
  "mv": "15m",        // movement
  "ml": "9",          // morale
  "skill": "+3",
  "save": "12+",
  "t_target": 6,
  "attacks": [{ "name": "...", "atk": "+9x3", "dmg": "1d6", "tr_die": "1d6", "tr_mult": "x3", "shock": "3/-" }]
}
```

**Roster entry** (`data/roster.json`):
```json
{
  "id": "...",
  "name": "...",
  "is_pc": true,
  "hp": 12, "max_hp": 14,
  "system_strain": 0,
  "attributes": { "str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10 },
  "ac": 10,
  "attacks": [],
  "skill": "+3",
  "initiative_mod": 2,
  "current_init": 4,
  "is_active": false,
  "is_dead": false
}
```

## Build / Test / Lint

No tooling is configured yet. The `.gitignore` is Python-focused, so add `pyproject.toml` or `requirements.txt` when dependencies are introduced.


## Job Application Context

Magnus is using loreforge as a portfolio project while applying for a **senior data engineering role**. The role is infrastructure-first, backend-only (no UI/front-end), and centered on enabling data science and ML/AI work at scale.

**What the hiring team is looking for (priority order):**
1. **Azure** — must-have; other clouds are a ramp-up cost disadvantage
2. **Python** — must-have
3. **GitHub/Git workflows** — must-have (CI/CD, automated deployments)
4. **Infrastructure as Code** — Bicep/Terraform, container-based services, Kubernetes preferred over ADF/Databricks
5. **DevOps/MLOps/LLMOps** — strong secondary signal; at least one of these

**What this means for loreforge:**
- Lean into the Azure + Bicep + Python stack — this directly matches the must-haves
- Build out CI/CD via GitHub Actions to demonstrate GitHub workflow fluency
- Show data pipeline thinking: ingestion, transformation, storage (data lakes, blob, Parquet)
- MLOps/LLMOps angle is a differentiator — consider adding observability, model deployment, or agentic workflow elements
- Avoid spending time on any UI — success is measured by backend systems quality

**Anti-patterns to avoid in this project:**
- Front-end or visualization work
- App-centric framing (this is plumbing, not a product)
- AWS/GCP-specific tooling