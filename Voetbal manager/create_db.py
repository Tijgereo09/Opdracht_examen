import sqlite3

# ============================================================================
# DATABASE SETUP EN MIGRATIE
# ============================================================================
# Dit bestand maakt de SQLite database en alle benodigde tabellen aan.
# Bij het opstarten wordt automatisch gecontroleerd of alle tabellen bestaan.

# FUNCTIE: table_exists()
# Controleert of een bepaalde tabel in de database bestaat
# Parameters:
#   - cur: database cursor
#   - name: naam van de tabel
# Return: True als tabel bestaat, False als niet
def table_exists(cur, name):
    # Zoek tabel in sqlite_master (interne catalogus van database)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

# FUNCTIE: column_exists()
# Controleert of een bepaalde kolom in een tabel bestaat
# Parameters:
#   - cur: database cursor
#   - table: tabel naam
#   - column: kolom naam
# Return: True als kolom bestaat, False als niet
def column_exists(cur, table, column):
    # PRAGMA table_info geeft informatie over alle kolommen in tabel
    cur.execute(f"PRAGMA table_info({table})")
    # Extract alleen de kolomnamen (index 1 van elke rij)
    cols = [c[1] for c in cur.fetchall()]
    return column in cols

# FUNCTIE: create_database()
# Initialiseert de database en maakt alle benodigde tabellen aan.
# Als tabellen al bestaan, controleert deze functie of alle kolommen aanwezig zijn.
def create_database():
    # Verbind met database
    conn = sqlite3.connect("database.db", timeout=30, check_same_thread=False)
    
    # Zet in Write-Ahead Logging mode voor beter concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Stel timeout in
    conn.execute("PRAGMA busy_timeout=30000")
    
    cur = conn.cursor()

    # ============================================================
    # TABEL 1: SPELERS
    # ============================================================
    # Bevat alle spelesgegevens en inloggegevens
    # Kolommen:
    #   - id: uniek speler-identificatienummer
    #   - username: gebruikersnaam voor login
    #   - password: wachtwoord voor login
    #   - positie: voetbalposititie (keeper, verdediger, etc.)
    #   - rugnummer: rugnummer op voetbalshirt
    #   - team: team waar speler in speelt
    
    if not table_exists(cur, "spelers"):
        # Maak de tabel aan als deze nog niet bestaat
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
        # Tabel bestaat al, controleer of alle kolommen aanwezig zijn
        # Voeg kolommen toe als ze ontbreken
        for col in ["positie", "rugnummer", "team"]:
            if not column_exists(cur, "spelers", col):
                cur.execute(f"ALTER TABLE spelers ADD COLUMN {col} TEXT")
                print(f"Kolom '{col}' toegevoegd aan 'spelers'.")

    # -----------------------------
    # 2. TRAININGEN
    # -----------------------------
    # ============================================================
    # TABEL 2: TRAININGEN
    # ============================================================
    # Bevat gegevens over alle trainingsessies
    # Kolommen:
    #   - id: uniek trainings-ID
    #   - titel: naam/titel van training
    #   - datum: trainigsdatum (YYYY-MM-DD)
    #   - tijd: trainings begintijd (HH:MM)
    #   - locatie: waar training plaatsvindt
    #   - beschrijving: extra informatie over training
    
    if not table_exists(cur, "trainingen"):
        # Maak tabel aan
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
        # Controleer en voeg ontbrekende kolommen toe
        for col in ["titel", "datum", "tijd", "locatie", "beschrijving"]:
            if not column_exists(cur, "trainingen", col):
                cur.execute(f"ALTER TABLE trainingen ADD COLUMN {col} TEXT")
                print(f"Kolom '{col}' toegevoegd aan 'trainingen'.")

    # -----------------------------
    # 3. WEDSTRIJDEN
    # -----------------------------
    # ============================================================
    # TABEL 3: WEDSTRIJDEN
    # ============================================================
    # Bevat gegevens over voetbalwedstrijden
    # Kolommen:
    #   - id: uniek wedstrijd-ID
    #   - tegenstander: naam van tegenstander
    #   - datum: wedstrijddatum (YYYY-MM-DD)
    #   - tijd: wedstrijd begintijd (HH:MM)
    #   - locatie: waar wedstrijd plaatsvindt
    #   - thuis_uit: thuis of uit (H/U)
    #   - resultaat: eindstand van wedstrijd
    
    if not table_exists(cur, "wedstrijden"):
        # Maak tabel aan
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
        # Controleer en voeg ontbrekende kolommen toe
        for col in ["tegenstander", "datum", "tijd", "locatie", "thuis_uit", "resultaat"]:
            if not column_exists(cur, "wedstrijden", col):
                cur.execute(f"ALTER TABLE wedstrijden ADD COLUMN {col} TEXT")
                print(f"Kolom '{col}' toegevoegd aan 'wedstrijden'.")

    # ============================================================
    # TABEL 4: WEDSTRIJD_SPELERS (koppeltabel)
    # ============================================================
    # Verbindt spelers aan wedstrijden en slaat positie/bank-info op
    # Dit is een koppeltabel (junction table) voor many-to-many relatie
    # Kolommen:
    #   - id: unieke rij-ID
    #   - wedstrijd_id: verwijzing naar wedstrijden.id
    #   - speler_id: verwijzing naar spelers.id
    #   - positie: positie waarin speler speelt (keeper, verdediger, etc.)
    #   - bank: 0=in opstelling, 1=op de bank
    
    if not table_exists(cur, "wedstrijd_spelers"):
        # Maak tabel aan
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
        # Controleer en voeg ontbrekende kolommen toe
        if not column_exists(cur, "wedstrijd_spelers", "positie"):
            cur.execute("ALTER TABLE wedstrijd_spelers ADD COLUMN positie TEXT")
            print("Kolom 'positie' toegevoegd aan 'wedstrijd_spelers'.")
        if not column_exists(cur, "wedstrijd_spelers", "bank"):
            cur.execute("ALTER TABLE wedstrijd_spelers ADD COLUMN bank INTEGER DEFAULT 0")
            print("Kolom 'bank' toegevoegd aan 'wedstrijd_spelers'.")

    # ============================================================
    # TABEL 5: MESSAGES (chatberichten)
    # ============================================================
    # Slaat alle chat- en privéberichten op
    # Kolommen:
    #   - id: unieke bericht-ID
    #   - sender_id: ID van afzender (speler) of NULL voor trainer
    #   - sender_name: naam van afzender
    #   - sender_role: rol van afzender (trainer of speler)
    #   - recipient_role: ontvanger rol (trainer, speler, all voor globaal)
    #   - recipient_id: ID van ontvanger (voor privéberichten)
    #   - content: berichtinhoud
    #   - created_at: moment waarop bericht is verzonden
    
    if not table_exists(cur, "messages"):
        # Maak tabel aan
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
        # Controleer en voeg ontbrekende kolommen toe
        if not column_exists(cur, "messages", "sender_id"):
            cur.execute("ALTER TABLE messages ADD COLUMN sender_id INTEGER")
            print("Kolom 'sender_id' toegevoegd aan 'messages'.")
        if not column_exists(cur, "messages", "recipient_id"):
            cur.execute("ALTER TABLE messages ADD COLUMN recipient_id INTEGER")
            print("Kolom 'recipient_id' toegevoegd aan 'messages'.")

    # ============================================================
    # TABEL 6: COMMENTS (reacties op trainingen/wedstrijden)
    # ============================================================
    # Slaat reacties en opmerkingen op trainingen en wedstrijden op
    # Kolommen:
    #   - id: unieke reactie-ID
    #   - sender_name: naam van auteur
    #   - sender_role: rol van auteur (trainer of speler)
    #   - training_id: training ID als reactie op training (NULL als op wedstrijd)
    #   - wedstrijd_id: wedstrijd ID als reactie op wedstrijd (NULL als op training)
    #   - content: reactieinhoud
    #   - created_at: moment waarop reactie is geplaatst
    
    if not table_exists(cur, "comments"):
        # Maak tabel aan
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

    # ============================================================
    # OPSLAAN EN AFSLUITEN
    # ============================================================
    # Sla alle wijzigingen op in de database
    conn.commit()
    conn.close()
    print("Database gecontroleerd en bijgewerkt.")
