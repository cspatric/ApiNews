from typing import List, Dict, Any
from .connection import create_connection

def get_or_create_channel_id(channel_link: str) -> int:
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM channels WHERE link = ?", (channel_link,))
    result = cursor.fetchone()

    if result:
        channel_id = result[0]
    else:
        cursor.execute("INSERT INTO channels (link) VALUES (?)", (channel_link,))
        conn.commit()
        channel_id = cursor.lastrowid

    conn.close()
    return channel_id


def save_messages(messages: List[Dict[str, Any]]):
    conn = create_connection()
    cursor = conn.cursor()

    for msg in messages:
        channel_id = get_or_create_channel_id(msg["channel"])
        cursor.execute("""
            INSERT INTO messages (channel_id, timestamp, text, links)
            VALUES (?, ?, ?, ?);
        """, (
            channel_id,
            msg["timestamp"],
            msg["text"],
            ", ".join(msg["links"])
        ))

    conn.commit()
    conn.close()
