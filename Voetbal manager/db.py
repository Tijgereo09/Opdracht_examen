import sqlite3

# Open een verbinding met de SQLite database en stel rijtoegang in als dict-achtig object.
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Voer een query uit met optionele commit en retourneer resultaten.
def query_db(query, args=(), one=False, commit=False):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    if commit:
        conn.commit()
    rows = cur.fetchall()
    conn.close()
    if one:
        return rows[0] if rows else None
    return rows
