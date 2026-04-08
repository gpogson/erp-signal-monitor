import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "seen_articles.db")


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_articles (
                id TEXT PRIMARY KEY,
                seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Prune entries older than 30 days to keep DB lean
        conn.execute("""
            DELETE FROM seen_articles
            WHERE seen_at < datetime('now', '-30 days')
        """)


def is_seen(article_id: str) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM seen_articles WHERE id = ?", (article_id,)
        ).fetchone()
        return row is not None


def mark_seen(article_id: str):
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_articles (id) VALUES (?)", (article_id,)
        )
