from typing import List, Dict, Any, Optional
from .connection import create_connection


def create_channel(channel_link: str) -> int:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO channels (link) VALUES (?)", (channel_link,))
    conn.commit()
    channel_id = cursor.lastrowid
    conn.close()
    return channel_id


def get_channel_id(channel_link: str) -> Optional[int]:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM channels WHERE link = ?", (channel_link,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def list_channels() -> List[Dict[str, Any]]:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, link FROM channels")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "link": row[1]} for row in rows]


def save_messages(messages: List[Dict[str, Any]]):
    conn = create_connection()
    cursor = conn.cursor()

    for msg in messages:
        channel_link = msg["channel"]
        channel_id = get_channel_id(channel_link)

        if channel_id is None:
            channel_id = create_channel(channel_link)

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
