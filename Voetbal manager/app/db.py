import sqlite3
import time
import os

# Get the path to the database file (in the parent directory)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')

# Open een verbinding met de SQLite database en stel rijtoegang in als dict-achtig object.
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.row_factory = sqlite3.Row
    return conn

# Voer een query uit met optionele commit en retourneer resultaten.
def query_db(query, args=(), one=False, commit=False):
    retries = 6
    delay = 0.5
    while retries > 0:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(query, args)
            if commit:
                conn.commit()
            rows = cur.fetchall()
            conn.close()
            if one:
                return rows[0] if rows else None
            return rows
        except sqlite3.OperationalError as exc:
            conn.close()
            if "database is locked" in str(exc).lower() and retries > 1:
                time.sleep(delay)
                retries -= 1
                delay *= 1.5
                continue
            raise
