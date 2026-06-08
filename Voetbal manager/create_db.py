import sqlite3

def create_tables():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # -------------------------------------------------------------
    # SPELERS
    # -------------------------------------------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS spelers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        wachtwoord TEXT NOT NULL,
        positie TEXT,
        rugnummer INTEGER,
        team TEXT
    );
    """)

    # -------------------------------------------------------------
    # TRAININGEN
    # -------------------------------------------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trainingen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titel TEXT NOT NULL,
        datum TEXT NOT NULL,
        tijd TEXT NOT NULL,
        beschrijving TEXT
    );
    """)

    # -------------------------------------------------------------
    # WEDSTRIJDEN ( thuis_uit )
    # -------------------------------------------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS wedstrijden (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tegenstander TEXT NOT NULL,
        datum TEXT NOT NULL,
        tijd TEXT NOT NULL,
        locatie TEXT,
        thuis_uit TEXT
    );
    """)

    # -------------------------------------------------------------
    # MELDINGEN
    # -------------------------------------------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meldingen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        speler_id INTEGER NOT NULL,
        tegenstander TEXT,
        datum TEXT,
        tijd TEXT
    );
    """)

    # -------------------------------------------------------------
    # CHAT MESSAGES
    # -------------------------------------------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        sender_name TEXT NOT NULL,
        sender_role TEXT NOT NULL,
        recipient_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        seen INTEGER DEFAULT 0
    );
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print("Database aangemaakt / bijgewerkt!")
