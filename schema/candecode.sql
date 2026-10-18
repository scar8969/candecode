-- 🚗 can-analyzer schema
CREATE TABLE log_files(id INTEGER PRIMARY KEY, name TEXT, format TEXT DEFAULT 'asc', frame_count INTEGER DEFAULT 0, uploaded_at DATETIME);
CREATE TABLE messages(id INTEGER PRIMARY KEY, log_id INTEGER REFERENCES log_files(id), ts REAL, can_id TEXT, data_hex TEXT, decoded_json TEXT DEFAULT '{}');
