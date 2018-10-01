-- wtf this isn't enforced by default?!?!?
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS threads(
    id          INTEGER PRIMARY KEY,
    created     DATE DEFAULT (DATETIME('now')) -- when was the blog post made?
);

CREATE TABLE IF NOT EXISTS comments(
    id          INTEGER PRIMARY KEY,
    thread_id    INTEGER NOT NULL,
    name        TEXT NOT NULL,              -- user supplied name
    commentbody TEXT NOT NULL,              -- duh, this is what the comment is
    email       TEXT,                       -- not actually displayed, but kept for logging stuff
    ipaddr      TEXT NOT NULL,              -- ipv4 or v6?
    created     DATE DEFAULT (DATETIME('now')), -- when was the comment published?

    FOREIGN KEY(thread_id) REFERENCES threads(id)
);

-- match tokens to threads (each token is only able to be used for one blog post)
CREATE TABLE IF NOT EXISTS tokenmapping(
    captcha_id          BYTEA PRIMARY KEY,
    thread_id           INTEGER NOT NULL,
    
    FOREIGN KEY(thread_id) REFERENCES threads(id)
);

CREATE TABLE IF NOT EXISTS tokens(
    captcha_id          BYTEA PRIMARY KEY,
    created     DATE DEFAULT (DATETIME('now')) NOT NULL,
    expiry      DATE DEFAULT (DATETIME('now', '+5 minutes')) NOT NULL,

    FOREIGN KEY(captcha_id) REFERENCES tokenmapping(captcha_id)
);

CREATE TABLE IF NOT EXISTS challenges(
    captcha_id          BYTEA PRIMARY KEY,
    -- answer to captcha query - array
    answer      TEXT NOT NULL,

    -- json response string that is what we send to the client (we keep for posterity)
    hint        TEXT NOT NULL,

    FOREIGN KEY(captcha_id) REFERENCES tokenmapping(captcha_id)
);
