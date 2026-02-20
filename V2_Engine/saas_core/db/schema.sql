-- SaaS Core — Database Schema (V5 Unified BYOK)
-- Tables: users, projects, oauth_states, unified_credentials
--
-- unified_credentials replaces the old api_credentials + oauth_tokens tables.
-- The credential_type column is the discriminator:
--   'api_key'    — Simple LLM key  ({"key": "sk-..."})
--   'oauth_app'  — OAuth Client ID/Secret ({"client_id": "...", "client_secret": "..."})
--   'oauth_token'— OAuth Access/Refresh Tokens ({"access_token": "...", "refresh_token": "...", "expiry": "..."})
-- UNIQUE(user_id, provider, credential_type) solves the "Google Collision":
--   (dev_admin, google, api_key)   = Gemini API key
--   (dev_admin, google, oauth_app) = GSC OAuth Client

CREATE TABLE IF NOT EXISTS users (
    user_id     TEXT PRIMARY KEY,
    email       TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL,
    provider    TEXT    NOT NULL,
    site_url    TEXT    NOT NULL,
    label       TEXT,
    created_at  TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, provider, site_url)
);

CREATE TABLE IF NOT EXISTS oauth_states (
    state       TEXT PRIMARY KEY,
    user_id     TEXT    NOT NULL,
    provider    TEXT    NOT NULL,
    created_at  TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS unified_credentials (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             TEXT    NOT NULL,
    provider            TEXT    NOT NULL,
    credential_type     TEXT    NOT NULL,
    encrypted_payload   TEXT    NOT NULL,
    metadata            TEXT,
    is_active           INTEGER DEFAULT 1,
    updated_at          TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, provider, credential_type)
);
