# ela/core/db_utils.py
import os
import sqlite3

BASE_DIR = os.getcwd()
SETTINGS_DB = os.path.join(BASE_DIR, 'settings.db')
CACHE_DB = os.path.join(BASE_DIR, 'cache.db')

# Схемы
SETTINGS_SCHEMA = '''
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
'''

CACHE_SCHEMA = '''
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS file_cache (
    data_hash TEXT PRIMARY KEY,
    semantic_units TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS key_terms_cache (
    data_hash TEXT PRIMARY KEY,
    terms_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(data_hash) REFERENCES file_cache(data_hash) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS translation_cache (
    full_hash TEXT PRIMARY KEY,
    data_hash TEXT NOT NULL,
    bilingual_objects TEXT NOT NULL,
    FOREIGN KEY(data_hash) REFERENCES file_cache(data_hash) ON DELETE CASCADE
);
'''

def init_settings_db(path: str = SETTINGS_DB):
    conn = sqlite3.connect(path)
    conn.executescript(SETTINGS_SCHEMA)
    conn.commit()
    conn.close()

def init_cache_db(path: str = CACHE_DB):
    conn = sqlite3.connect(path)
    conn.executescript(CACHE_SCHEMA)
    conn.commit()
    conn.close()

def get_setting(key, default=None, path: str = SETTINGS_DB):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value, path: str = SETTINGS_DB):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute('REPLACE INTO settings (key,value) VALUES (?,?)', (key, value))
    conn.commit()
    conn.close()
