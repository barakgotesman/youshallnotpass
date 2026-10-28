-- Which levels each anonymous player has beaten. Later levels unlock from this,
-- and it lets a returning player see their progress after a page reload.
CREATE TABLE session_progress (
    session_id  uuid NOT NULL REFERENCES sessions(id),
    level_id    integer NOT NULL REFERENCES levels(id),
    cleared_at  timestamptz NOT NULL DEFAULT now(),
    -- One row per level per player: clearing twice must not create duplicates.
    PRIMARY KEY (session_id, level_id)
);

-- A defense version is identified by what it is made of, so the same prompts
-- and models always map to the same row. The unique index lets the app
-- "insert if missing" safely when two requests race on a fresh deploy.
CREATE UNIQUE INDEX defense_versions_content_idx
    ON defense_versions (level_id, prompt_versions, models);

-- Loading a player's history for a level (to build an attack record) filters
-- on exactly these two columns.
CREATE INDEX attempts_session_level_idx ON attempts (session_id, level_id, id);
