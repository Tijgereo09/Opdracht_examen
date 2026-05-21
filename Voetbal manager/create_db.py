import sqlite3

def table_exists(cur, name):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cur.fetchall()]
    return column in cols

def create_database():
    conn = sqlite3.connect("database.db")
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


    conn.commit()
    conn.close()
    print("Database gecontroleerd en bijgewerkt.")
