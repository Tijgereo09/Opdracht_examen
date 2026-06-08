import sqlite3
import time

# ============================================================================
# DATABASE HULPFUNCTIES
# - WAL mode
# - Retry logic
# - Automatische migraties voor ALLE tabellen
# ============================================================================

DB_PATH = "database.db"


# ----------------------------------------------------------------------------
# Controleer of tabel bestaat
# ----------------------------------------------------------------------------
def table_exists(table):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    exists = cur.fetchone() is not None
    conn.close()
    return exists


# ----------------------------------------------------------------------------
# Controleer of kolom bestaat in een tabel
# ----------------------------------------------------------------------------
def column_exists_in(table, column):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cur.fetchall()]
    conn.close()
    return column in columns


# ----------------------------------------------------------------------------
# Automatische migraties
# ----------------------------------------------------------------------------
def run_migrations():

    # -----------------------------
    # TABEL: messages
    # -----------------------------
    if table_exists("messages"):
        if not column_exists_in("messages", "seen"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("ALTER TABLE messages ADD COLUMN seen INTEGER DEFAULT 0")
            conn.commit()
            conn.close()
            print("Migratie uitgevoerd: kolom 'seen' toegevoegd aan messages")

    # -----------------------------
    # TABEL: wedstrijden
    # -----------------------------
    if table_exists("wedstrijden"):
        if not column_exists_in("wedstrijden", "thuis_uit"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("ALTER TABLE wedstrijden ADD COLUMN thuis_uit TEXT")
            conn.commit()
            conn.close()
            print("Migratie uitgevoerd: kolom 'thuis_uit' toegevoegd aan wedstrijden")

    # -----------------------------
    # TABEL: wedstrijd_spelers
    # -----------------------------
    if not table_exists("wedstrijd_spelers"):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE wedstrijd_spelers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wedstrijd_id INTEGER NOT NULL,
                speler_id INTEGER NOT NULL,
                positie TEXT,
                bank INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
        print("Migratie uitgevoerd: tabel 'wedstrijd_spelers' aangemaakt.")


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

            # Database locked = retry
            if "database is locked" in str(exc).lower() and retries > 1:
                time.sleep(delay)
                retries -= 1
                delay *= 1.5
                continue

            # Andere fout = raise
            raise
