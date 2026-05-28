import sqlite3
import os

# Get the path to the database file (in the parent directory)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')

# Controleert of een tabel bestaat in de SQLite database.
def table_exists(cur, name):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

# Controleert of een kolom bestaat in een opgegeven tabel.
def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cur.fetchall()]
    return column in cols

# Maakt de database en benodigde tabellen aan of werkt bestaande tabellen bij.
def create_database():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    cur = conn.cursor()

    # -----------------------------
    # 1. SPELERS
    # -----------------------------
    if not table_exists(cur, "spelers"):
        cur.execute("""
            CREATE TABLE spelers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                positie TEXT,
                rugnummer TEXT,
                team TEXT
            )
        """)
        print("Tabel 'spelers' aangemaakt.")
    else:
        for col in ["positie", "rugnummer", "team"]:
            if not column_exists(cur, "spelers", col):
                cur.execute(f"ALTER TABLE spelers ADD COLUMN {col} TEXT")
                print(f"Kolom '{col}' toegevoegd aan 'spelers'.")

    # -----------------------------
    # 2. TRAININGEN
    # -----------------------------
    if not table_exists(cur, "trainingen"):
        cur.execute("""
            CREATE TABLE trainingen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titel TEXT NOT NULL,
                datum TEXT,
                tijd TEXT,
                locatie TEXT,
                beschrijving TEXT
            )
        """)
        print("Tabel 'trainingen' aangemaakt.")
    else:
        for col in ["titel", "datum", "tijd", "locatie", "beschrijving"]:
            if not column_exists(cur, "trainingen", col):
                cur.execute(f"ALTER TABLE trainingen ADD COLUMN {col} TEXT")
                print(f"Kolom '{col}' toegevoegd aan 'trainingen'.")

    # -----------------------------
    # 3. WEDSTRIJDEN
    # -----------------------------
    if not table_exists(cur, "wedstrijden"):
        cur.execute("""
            CREATE TABLE wedstrijden (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tegenstander TEXT NOT NULL,
                datum TEXT,
                tijd TEXT,
                locatie TEXT,
                thuis_uit TEXT,
                resultaat TEXT
            )
        """)
        print("Tabel 'wedstrijden' aangemaakt.")
    else:
        for col in ["tegenstander", "datum", "tijd", "locatie", "thuis_uit", "resultaat"]:
            if not column_exists(cur, "wedstrijden", col):
                cur.execute(f"ALTER TABLE wedstrijden ADD COLUMN {col} TEXT")
                print(f"Kolom '{col}' toegevoegd aan 'wedstrijden'.")

    # Maak de tussenliggende tabel 'wedstrijd_spelers' voor koppelingen tussen wedstrijden en spelers.
    if not table_exists(cur, "wedstrijd_spelers"):
        cur.execute("""
            CREATE TABLE wedstrijd_spelers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wedstrijd_id INTEGER NOT NULL,
                speler_id INTEGER NOT NULL,
                positie TEXT,
                bank INTEGER DEFAULT 0,
                FOREIGN KEY(wedstrijd_id) REFERENCES wedstrijden(id),
                FOREIGN KEY(speler_id) REFERENCES spelers(id)
            )
        """)
        print("Tabel 'wedstrijd_spelers' aangemaakt.")
    else:
        if not column_exists(cur, "wedstrijd_spelers", "positie"):
            cur.execute("ALTER TABLE wedstrijd_spelers ADD COLUMN positie TEXT")
            print("Kolom 'positie' toegevoegd aan 'wedstrijd_spelers'.")
        if not column_exists(cur, "wedstrijd_spelers", "bank"):
            cur.execute("ALTER TABLE wedstrijd_spelers ADD COLUMN bank INTEGER DEFAULT 0")
            print("Kolom 'bank' toegevoegd aan 'wedstrijd_spelers'.")

    # Maak de tabel voor chatberichten aan.
    if not table_exists(cur, "messages"):
        cur.execute("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                sender_name TEXT NOT NULL,
                sender_role TEXT NOT NULL,
                recipient_role TEXT NOT NULL,
                recipient_id INTEGER,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Tabel 'messages' aangemaakt.")
    else:
        if not column_exists(cur, "messages", "sender_id"):
            cur.execute("ALTER TABLE messages ADD COLUMN sender_id INTEGER")
            print("Kolom 'sender_id' toegevoegd aan 'messages'.")
        if not column_exists(cur, "messages", "recipient_id"):
            cur.execute("ALTER TABLE messages ADD COLUMN recipient_id INTEGER")
            print("Kolom 'recipient_id' toegevoegd aan 'messages'.")

    # Maak de tabel voor reacties op trainingen of wedstrijden aan.
    if not table_exists(cur, "comments"):
        cur.execute("""
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_name TEXT NOT NULL,
                sender_role TEXT NOT NULL,
                training_id INTEGER,
                wedstrijd_id INTEGER,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Tabel 'comments' aangemaakt.")

    # Sla alle wijzigingen op en sluit de verbinding.
    conn.commit()
    conn.close()
    print("Database gecontroleerd en bijgewerkt.")
