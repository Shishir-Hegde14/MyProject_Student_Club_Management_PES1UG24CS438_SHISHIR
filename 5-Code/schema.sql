PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    allocation INTEGER NOT NULL CHECK(allocation >= 0)
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('lead','student','coordinator','finance','dean','checkin')),
    club_id INTEGER REFERENCES clubs(id)
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    club_id INTEGER NOT NULL REFERENCES clubs(id),
    lead_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    event_date TEXT NOT NULL,
    venue TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK(capacity > 0),
    budget INTEGER NOT NULL CHECK(budget > 0),
    status TEXT NOT NULL DEFAULT 'Draft' CHECK(status IN ('Draft','Faculty pending','Finance pending','Dean pending','Approved','Rejected')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS budget_items (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id),
    description TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK(amount > 0)
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id),
    actor_id INTEGER NOT NULL REFERENCES users(id),
    stage TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    signed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, stage)
);
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id),
    attendee_id INTEGER NOT NULL REFERENCES users(id),
    used_at TEXT,
    UNIQUE(event_id, attendee_id)
);
