import sqlite3

def table_exists(cur, name):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cur.fetchall()]
    return column in cols

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
    # kolommen toevoegen indien ze ontbreken
    if not column_exists(cur, "spelers", "positie"):
        cur.execute("ALTER TABLE spelers ADD COLUMN positie TEXT")
    if not column_exists(cur, "spelers", "rugnummer"):
        cur.execute("ALTER TABLE spelers ADD COLUMN rugnummer TEXT")
    if not column_exists(cur, "spelers", "team"):
        cur.execute("ALTER TABLE spelers ADD COLUMN team TEXT")

# voorbeeldspeler indien leeg
cur.execute("SELECT COUNT(*) FROM spelers")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO spelers (username, password, positie, rugnummer, team)
        VALUES ('speler1', 'test123', 'Aanvaller', '9', 'A-ploeg')
    """)
    print("Voorbeeldspeler toegevoegd.")


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


conn.commit()
conn.close()

print("Database gecontroleerd en bijgewerkt.")
