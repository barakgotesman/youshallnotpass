-- Initial schema. Mirrors the data model in CLAUDE.md.

-- pgvector adds the `vector` column type and similarity search. We use it to
-- store attack embeddings (lists of numbers that capture a message's meaning),
-- so similar attacks can be found and grouped into families.
CREATE EXTENSION IF NOT EXISTS vector;

-- Anonymous players. We store a hash of the IP, never the raw address.
CREATE TABLE sessions (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_hash     text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE levels (
    id                  integer PRIMARY KEY,
    name                text NOT NULL,
    -- Which layers this level enables (see api/defense/levels.py).
    pipeline_config     jsonb NOT NULL,
    -- FK added below, after defense_versions exists (the two reference each other).
    current_defense_version_id integer
);

-- Server-only. Never selected by any endpoint that returns data to the client.
CREATE TABLE secrets (
    id          serial PRIMARY KEY,
    level_id    integer NOT NULL REFERENCES levels(id),
    value       text NOT NULL,
    active      boolean NOT NULL DEFAULT true
);

-- A "defense version" is a snapshot of which prompts and models a level used,
-- so every eval result and attack can be tied to the exact defense it faced.
CREATE TABLE defense_versions (
    id                  serial PRIMARY KEY,
    level_id            integer NOT NULL REFERENCES levels(id),
    prompt_versions     jsonb NOT NULL,   -- e.g. {"defender": "v2", "classifier": "v1"}
    models              jsonb NOT NULL,   -- e.g. {"defender": "llama-3.3-70b"}
    notes               text,
    created_at          timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE levels
    ADD CONSTRAINT levels_current_defense_version_fk
    FOREIGN KEY (current_defense_version_id) REFERENCES defense_versions(id);

-- Every chat turn. The trace (per-layer verdicts, latency, tokens) is the raw
-- material for evals and the public Defense Log.
CREATE TABLE attempts (
    id                  bigserial PRIMARY KEY,
    session_id          uuid NOT NULL REFERENCES sessions(id),
    level_id            integer NOT NULL REFERENCES levels(id),
    defense_version_id  integer NOT NULL REFERENCES defense_versions(id),
    user_message        text NOT NULL,
    model_response      text,             -- null when an input layer blocked the turn
    pipeline_trace      jsonb NOT NULL,
    leaked              boolean NOT NULL DEFAULT false,
    created_at          timestamptz NOT NULL DEFAULT now()
);

-- Curated successful attacks; these become the regression suite.
CREATE TABLE attacks (
    id                  serial PRIMARY KEY,
    level_id            integer NOT NULL REFERENCES levels(id),
    defense_version_id  integer NOT NULL REFERENCES defense_versions(id),
    conversation        jsonb NOT NULL,   -- full message history that caused the leak
    discovered_at       timestamptz NOT NULL DEFAULT now(),
    family              text,             -- cluster label, filled in by evals/embed.py
    -- 384 dimensions = output size of multilingual-e5-small. Changing the
    -- embedding model later means a new migration and re-embedding everything.
    embedding           vector(384),
    in_regression_suite boolean NOT NULL DEFAULT false
);

-- Approximate nearest-neighbour index so "find attacks similar to this one"
-- stays fast as the table grows. Cosine distance fits text embeddings.
CREATE INDEX attacks_embedding_idx ON attacks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE eval_runs (
    id                  serial PRIMARY KEY,
    defense_version_id  integer NOT NULL REFERENCES defense_versions(id),
    models              jsonb NOT NULL,
    git_sha             text,
    metrics             jsonb,            -- block rate, false positives, latency, cost
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE eval_results (
    id          bigserial PRIMARY KEY,
    run_id      integer NOT NULL REFERENCES eval_runs(id) ON DELETE CASCADE,
    case_kind   text NOT NULL CHECK (case_kind IN ('attack', 'benign')),
    case_ref    text NOT NULL,            -- attack id or benign dataset line
    blocked     boolean NOT NULL,
    leaked      boolean NOT NULL,
    decided_by  text,                     -- which layer or method decided
    trace       jsonb NOT NULL
);
