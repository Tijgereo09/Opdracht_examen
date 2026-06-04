import sqlite3
import time

# ============================================================================
# DATABASE HULPFUNCTIES
# ============================================================================
# Dit bestand bevat functies voor veilige communicatie met SQLite database

# FUNCTIE: get_db()
# Maakt een verbinding met de SQLite database
# - WAL-modus zorgt voor beter concurrencyondersteuning
# - sqlite3.Row zorgt ervoor dat queryresultaten als dictionaries kunnen worden gebruikt
def get_db():
    # Verbind met database.db, met timeout van 30 seconden
    conn = sqlite3.connect("database.db", timeout=30, check_same_thread=False)
    
    # Zet database in Write-Ahead Logging mode (betere prestaties bij meerdere gebruikers)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Stel timeout in zodat database niet direct "locked" meldt
    conn.execute("PRAGMA busy_timeout=30000")
    
    # Maak rijen toegankelijk als dictionaries (s['kolom'] ipv s[0])
    conn.row_factory = sqlite3.Row
    return conn

# FUNCTIE: query_db()
# Voert een SQL-query uit met automatische retry-logica voor databaseslot
# Parameters:
#   - query: SQL-commando om uit te voeren
#   - args: Waarden om in de query in te voegen (ter voorkoming van SQL-injectie)
#   - one: True als je maar één rij wilt (in plaats van alle rijen)
#   - commit: True als je de database wilt opslaan (voor INSERT/UPDATE/DELETE)
def query_db(query, args=(), one=False, commit=False):
    # Stel retry-parameters in voor als database vergrendeld is
    retries = 6  # Maximaal 6 pogingen
    delay = 0.5  # Eerste wachttijd: 0.5 seconde
    
    while retries > 0:
        # Maak verbinding met database
        conn = get_db()
        try:
            # Maak database-cursor aan om queries uit te voeren
            cur = conn.cursor()
            
            # Voer SQL-query uit met gegeven waarden
            cur.execute(query, args)
            
            # Als commit=True, sla alle wijzigingen op (voor INSERT/UPDATE/DELETE)
            if commit:
                conn.commit()
            
            # Haal alle queryresultaten op
            rows = cur.fetchall()
            conn.close()
            
            # Retourneer resultaat (één rij of alle rijen)
            if one:
                return rows[0] if rows else None
            return rows
            
        except sqlite3.OperationalError as exc:
            # Database was vergrendeld
            conn.close()
            
            if "database is locked" in str(exc).lower() and retries > 1:
                # Wacht een beetje en probeer opnieuw
                time.sleep(delay)
                retries -= 1
                delay *= 1.5  # Verhoog wachttijd bij volgende poging
                continue
            
            # Fout is niet 'database locked' of we hebben geen pogingen meer -> gooi fout
            raise
