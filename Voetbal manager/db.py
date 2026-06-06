import sqlite3
import time

# ============================================================================
# DATABASE HULPFUNCTIES — PRO VERSIE
# - WAL mode
# - Retry logic
# - Automatische migratie (voegt 'seen' toe indien ontbreekt)
# ============================================================================

DB_PATH = "database.db"


# ----------------------------------------------------------------------------
# Controleer of kolom bestaat
# ----------------------------------------------------------------------------
def column_exists(column_name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("PRAGMA table_info(messages)")
    columns = [row[1] for row in cur.fetchall()]
    conn.close()
    return column_name in columns


# ----------------------------------------------------------------------------
# Automatische migratie: voeg kolom 'seen' toe indien ontbreekt
# ----------------------------------------------------------------------------
def run_migrations():
    if not column_exists("seen"):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("ALTER TABLE messages ADD COLUMN seen INTEGER DEFAULT 0")
        conn.commit()
        conn.close()
        print("✔ Migratie uitgevoerd: kolom 'seen' toegevoegd.")


# ----------------------------------------------------------------------------
# Maak databaseverbinding
# ----------------------------------------------------------------------------
def get_db():
    # Run migrations bij elke start
    run_migrations()

    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------------------------------------------------------------
# Query-functie met retry logic
# ----------------------------------------------------------------------------
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

            # Database locked → retry
            if "database is locked" in str(exc).lower() and retries > 1:
                time.sleep(delay)
                retries -= 1
                delay *= 1.5
                continue

            # Andere fout → raise
            raise
