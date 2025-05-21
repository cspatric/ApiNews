import sqlite3
from typing import List, Dict, Any

DB_NAME = "telegram_messages.db"

def create_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn


def initialize_database():
    conn = create_connection()
    cursor = conn.cursor()

    # Cria tabela de canais
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT NOT NULL UNIQUE
        );
    """)

    # Cria tabela de mensagens com chave estrangeira
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



def save_messages(messages: List[Dict[str, Any]]):
    conn = create_connection()
    cursor = conn.cursor()

    for msg in messages:
        cursor.execute("""
            INSERT INTO messages (channel, timestamp, text, links)
            VALUES (?, ?, ?, ?);
        """, (
            msg["channel"],
            msg["timestamp"],
            msg["text"],
            ", ".join(msg["links"])  # salva os links como string separada por vírgulas
        ))

    conn.commit()
    conn.close()
