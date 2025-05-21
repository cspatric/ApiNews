import sqlite3

DB_NAME = "newsApi.db"

def create_connection():
    return sqlite3.connect(DB_NAME)

def initialize_database():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT NOT NULL UNIQUE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            text TEXT,
            links TEXT,
            FOREIGN KEY (channel_id) REFERENCES channels(id)
        );
    """)

    conn.commit()
    conn.close()
