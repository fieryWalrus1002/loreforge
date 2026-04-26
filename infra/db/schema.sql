CREATE TABLE pipeline_runs (
    id TEXT PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    records_read INTEGER NOT NULL DEFAULT 0,
    records_written INTEGER NOT NULL DEFAULT 0,
    warnings INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE creatures (
    id TEXT PRIMARY KEY,
    source_id TEXT,
    name TEXT NOT NULL,
    hd INTEGER NOT NULL,
    hp INTEGER NOT NULL,
    ac INTEGER NOT NULL,
    mv TEXT,
    ml INTEGER,
    skill TEXT,
    save TEXT,
    description TEXT,
    special_abilities JSONB NOT NULL DEFAULT '[]',
    source_file TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE characters (
    id TEXT PRIMARY KEY,
    source_id TEXT,
    name TEXT NOT NULL,
    is_pc BOOLEAN NOT NULL,
    hp INTEGER NOT NULL,
    max_hp INTEGER NOT NULL,
    system_strain INTEGER NOT NULL DEFAULT 0,
    ac INTEGER NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}',
    skill TEXT,
    initiative_mod INTEGER NOT NULL DEFAULT 0,
    source_file TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- creature_id XOR character_id: each attack belongs to exactly one owner
CREATE TABLE attacks (
    id TEXT PRIMARY KEY,
    creature_id TEXT REFERENCES creatures(id),
    character_id TEXT REFERENCES characters(id),
    name TEXT NOT NULL,
    atk TEXT NOT NULL,
    num_attacks INTEGER NOT NULL DEFAULT 1,
    dmg TEXT NOT NULL,
    dmg_type TEXT,
    poison BOOLEAN NOT NULL DEFAULT FALSE,
    tr_die TEXT,
    tr_mult TEXT,
    shock_dmg INTEGER,
    shock_ac INTEGER,
    range_str TEXT,
    mag INTEGER,
    attr TEXT,
    tl INTEGER,
    enc INTEGER,
    CONSTRAINT attacks_has_one_owner CHECK (
        (creature_id IS NOT NULL)::int + (character_id IS NOT NULL)::int = 1
    )
);

CREATE TABLE dead_letters (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES pipeline_runs(id),
    source_file TEXT NOT NULL,
    raw_content TEXT,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_attacks_creature ON attacks(creature_id);
CREATE INDEX idx_attacks_character ON attacks(character_id);
CREATE INDEX idx_creatures_name ON creatures(name);
CREATE INDEX idx_dead_letters_run ON dead_letters(run_id);
