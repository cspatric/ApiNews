import sqlite3

DB_NAME = "newsApi.db"

def create_connection():
    return sqlite3.connect(DB_NAME)

def initialize_database():
    conn = create_connection()
    cursor = conn.cursor()

    # Países
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS countrys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
    """)

    # Prioridades
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS priorities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
    """)

    # Canais
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT NOT NULL UNIQUE,
            country_id INTEGER,
            FOREIGN KEY (country_id) REFERENCES countrys(id)
        );
    """)

    # Categorias de alerta
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
    """)

   # Mensagens coletadas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            text TEXT,
            links TEXT,
            images TEXT,
            video TEXT,
            FOREIGN KEY (channel_id) REFERENCES channels(id)
        );
    """)


    # Alertas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_ids TEXT, -- armazenado como JSON ou CSV
            priority_id INTEGER,
            country_id INTEGER,
            title TEXT,
            short_description TEXT,
            alert_body TEXT, -- pode conter JSON
            images TEXT,     -- longtext como base64 ou urls
            timestamp TEXT,
            coordinates TEXT,
            FOREIGN KEY (priority_id) REFERENCES alert_categories(id),
            FOREIGN KEY (country_id) REFERENCES countrys(id)
        );
    """)

    conn.commit()
    conn.close()
