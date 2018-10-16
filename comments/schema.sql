-- wtf this isn't enforced by default?!?!?
-- sqlite you are retarded
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS threads(
    id          INTEGER PRIMARY KEY,
    created     DATE DEFAULT (DATETIME('now')) -- when was the blog post made?
);

CREATE TABLE IF NOT EXISTS comments(
    id          INTEGER PRIMARY KEY,
    thread_id    INTEGER NOT NULL,
    title        TEXT NOT NULL,              -- user supplied title
    author_name  TEXT NOT NULL,                       -- user supplied name
    commentbody TEXT NOT NULL,              -- duh, this is what the comment is
    emailhash       TEXT,                       -- not actually displayed, but kept for comment deletion - only need the hash. This is text, as its an argon2 output string, of the form "$argon2i$....."
    ipaddr      TEXT,              -- XXX: handling ipv4 or v6? idk
    created     DATE DEFAULT (DATETIME('now')), -- when was the comment published?

    FOREIGN KEY(thread_id) REFERENCES threads(id) -- don't cascade these, because its best if they're archived.
);

-- match captcha_ids to threads (each token is only able to be used for one blog post)
CREATE TABLE IF NOT EXISTS tokenmapping(
    -- id is 128 bit random string, converted to urlsafe string (secrets.token_urlsafe)
    -- it is sufficiently long to make guessing other people's IDs annoying/v difficult

    -- requires 22 chars, as ceil(16/3) * 4 -> 24
    captcha_id          VARCHAR(24) PRIMARY KEY,
    thread_id           INTEGER NOT NULL,

    -- keep track of this, as we can clean up stale tokens
    created             DATE DEFAULT (DATETIME('now')),
    expiry      DATE DEFAULT (DATETIME('now', '+1 day')) NOT NULL,
    
    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tokens(
    captcha_id          VARCHAR(24) PRIMARY KEY,
    -- SHA256 hash of 256bit token
    token               BYTEA,
    created     DATE DEFAULT (DATETIME('now')) NOT NULL,
    expiry      DATE DEFAULT (DATETIME('now', '+20 minutes')) NOT NULL,

    FOREIGN KEY(captcha_id) REFERENCES tokenmapping(captcha_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS challenges(
    captcha_id          VARCHAR(24) PRIMARY KEY,

    -- answer to captcha query - json wrapped array (contains multiple answers)
    -- XXX: rename to answers
    -- we cooould hash this, but not sure if its really relevant
    answer      TEXT NOT NULL,

    -- json response string that is what we send to the client (we keep for posterity)
    hint        TEXT NOT NULL,

    attempts    INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY(captcha_id) REFERENCES tokenmapping(captcha_id) ON DELETE CASCADE
);

-- these are generated 
CREATE TABLE IF NOT EXISTS deletetokens(
    id              VARCHAR(24) PRIMARY KEY,
    -- sha256 hash of 256 bit token
    secret          BYTEA NOT NULL,

    comment_id      INTEGER NOT NULL,
    thread_id       INTEGER NOT NULL,

    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE,
    FOREIGN KEY(comment_id) REFERENCES comments(id) ON DELETE CASCADE
    );
