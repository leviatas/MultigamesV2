--DROP TABLE IF EXISTS users;
--DROP TABLE IF EXISTS games;


/*CREATE TABLE IF NOT EXISTS users (
    id bigint PRIMARY KEY,
    name text NOT NULL
);
*/
/*CREATE TABLE IF NOT EXISTS games_xapi_bot (
    id bigint PRIMARY KEY,
    groupName TEXT NOT NULL,
    data text NOT NULL
);*/
/*DROP TABLE IF EXISTS games_xapi_bot;*/

CREATE TABLE IF NOT EXISTS games (
    id bigint PRIMARY KEY,
    groupName TEXT NOT NULL,
    tipojuego TEXT NOT NULL,
    data TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS config (
    id bigint PRIMARY KEY,
    token TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stats (
    id bigint PRIMARY KEY,
    fascistwinhitler INTEGER NOT NULL,
    fascistwinpolicies INTEGER NOT NULL,
    liberalwinpolicies INTEGER NOT NULL,
    liberalwinkillhitler INTEGER NOT NULL,
    cancelgame INTEGER NOT NULL
);

--DROP TABLE IF EXISTS stats_detail;

CREATE TABLE IF NOT EXISTS stats_detail (
    id SERIAL PRIMARY KEY,
    playerlist TEXT,
    game_endcode INTEGER NOT NULL,
    liberal_track INTEGER NOT NULL,
    fascist_track INTEGER NOT NULL,
    num_players INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id bigint PRIMARY KEY,
    name text NOT NULL
);

--DROP TABLE IF EXISTS users_group;
CREATE TABLE IF NOT EXISTS users_group (
    id SERIAL PRIMARY KEY,
    group_id bigint,
    user_id bigint,
    alert_me boolean
);
