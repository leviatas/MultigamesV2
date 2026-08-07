--DROP TABLE IF EXISTS users;
--DROP TABLE IF EXISTS games;

CREATE TABLE IF NOT EXISTS users (
    id bigint PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE IF NOT EXISTS games_secret_hitler (
    id bigint PRIMARY KEY,
    groupName TEXT NOT NULL,
    data text NOT NULL
);

CREATE TABLE IF NOT EXISTS stats_secret_hitler (
    id bigint PRIMARY KEY,
    fascistwinhitler INTEGER NOT NULL,
    fascistwinpolicies INTEGER NOT NULL,
    liberalwinpolicies INTEGER NOT NULL,
    liberalwinkillhitler INTEGER NOT NULL,
    cancelgame INTEGER NOT NULL
);

--DROP TABLE IF EXISTS stats_detail;

CREATE TABLE IF NOT EXISTS stats_detail_secret_hitler (
    id SERIAL PRIMARY KEY,
    playerlist TEXT,
    game_endcode INTEGER NOT NULL,
    liberal_track INTEGER NOT NULL,
    fascist_track INTEGER NOT NULL,
    num_players INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS config (
     id bigint PRIMARY KEY,
     token TEXT NOT NULL
 );

CREATE TABLE IF NOT EXISTS user_stats (
    id SERIAL PRIMARY KEY,
    data text NOT NULL
); 

-- legacy, no usada: el catalogo de logros vive en Constants/Achievements.py
CREATE TABLE IF NOT EXISTS achivements_secret_hitler (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description text NOT NULL
);

-- Estadisticas nuevas vinculadas al ID de Telegram (no reemplazan stats_detail_secret_hitler,
-- que sigue alimentando /stats por nombre).
CREATE TABLE IF NOT EXISTS stats_secret_hitler_games (
    id SERIAL PRIMARY KEY,
    game_endcode INTEGER NOT NULL,
    legacy_detail_id INTEGER UNIQUE, -- referencia a stats_detail_secret_hitler.id, solo para partidas migradas con /vincularstats
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS stats_secret_hitler_players (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES stats_secret_hitler_games(id),
    uid BIGINT NOT NULL,
    name TEXT NOT NULL,
    role TEXT,
    party TEXT,
    won BOOLEAN NOT NULL,
    died BOOLEAN NOT NULL,
    killed_by_uid BIGINT, -- NULL si no lo mataron o si el dato no se pudo reconstruir al migrar
    UNIQUE (game_id, uid)
);
ALTER TABLE stats_secret_hitler_players ADD COLUMN IF NOT EXISTS mvp BOOLEAN NOT NULL DEFAULT FALSE;

-- Logros desbloqueados por jugador. El catalogo (nombre, descripcion, condicion)
-- vive en SecretHitler/Constants/Achievements.py; aca solo se guarda quien
-- desbloqueo cual (identificado por achievement_code, el Logro.code estable).
CREATE TABLE IF NOT EXISTS achievements_secret_hitler_players (
    id SERIAL PRIMARY KEY,
    uid BIGINT NOT NULL,
    achievement_code TEXT NOT NULL,
    game_id INTEGER REFERENCES stats_secret_hitler_games(id), -- NULL si se otorgo fuera de una partida (ej. backfill)
    earned_at TIMESTAMP DEFAULT now(),
    UNIQUE (uid, achievement_code)
);
CREATE INDEX IF NOT EXISTS idx_achievements_shp_uid ON achievements_secret_hitler_players(uid);

-- Una fila por cada formula (presidente+canciller) que efectivamente promulgo una
-- politica (no incluye promulgaciones por anarquia, que no fueron votadas). Fines
-- estadisticos y posible base para futuros logros. Ver Game.formula_history y
-- StatsExtended.save_extended_game_stats().
CREATE TABLE IF NOT EXISTS stats_secret_hitler_formulas (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES stats_secret_hitler_games(id),
    round INTEGER NOT NULL,
    president_uid BIGINT NOT NULL,
    chancellor_uid BIGINT NOT NULL,
    policy TEXT NOT NULL, -- 'liberal' o 'fascista'
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_stats_shf_game_id ON stats_secret_hitler_formulas(game_id);
CREATE INDEX IF NOT EXISTS idx_stats_shf_president_uid ON stats_secret_hitler_formulas(president_uid);
CREATE INDEX IF NOT EXISTS idx_stats_shf_chancellor_uid ON stats_secret_hitler_formulas(chancellor_uid);

-- If there are no stats in the stats table I initiate it.
DO $$
BEGIN 
  IF (SELECT count(*) = 0 FROM stats_secret_hitler) THEN
   INSERT INTO stats VALUES (1, 0, 0, 0, 0, 0);
  END IF; 
END $$;
--
