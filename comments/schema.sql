CREATE TABLE IF NOT EXISTS threads(
    id          INTEGER PRIMARY KEY,
    created     DATE DEFAULT (DATETIME('now')) -- when was the blog post made?
);

CREATE TABLE IF NOT EXISTS comments(
    id          INTEGER PRIMARY KEY,
    threadid    INTEGER NOT NULL,
    name        TEXT NOT NULL,              -- user supplied name
    commentbody TEXT NOT NULL,              -- duh, this is what the comment is
    email       TEXT,                       -- not actually displayed, but kept for logging stuff
    ipaddr      TEXT NOT NULL,              -- ipv4 or v6?
    created     DATE DEFAULT (DATETIME('now')), -- when was the comment published?

    FOREIGN KEY threadid REFERENCES threads(id)
);
