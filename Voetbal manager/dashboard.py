from flask import Blueprint, render_template, session
from db import query_db
from auth import login_required
from datetime import datetime

# Dashboardfunctionaliteit voor trainer en speler.
dashboard_bp = Blueprint("dashboard", __name__)

# Helper functie om volgende event op te halen
def get_next_event(table, date_col="datum", time_col="tijd", desc_col=None):
    """Get the next upcoming event from a table based on date and time."""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    
    query = f"""
        SELECT * FROM {table}
        WHERE {date_col} > ? 
           OR ({date_col} = ? AND {time_col} > ?)
        ORDER BY {date_col}, {time_col}
        LIMIT 1
    """
    event = query_db(query, (today, today, current_time), one=True)
    if event:
        if table == "wedstrijden":
            return f"{event['tegenstander']} — {event['datum']} {event['tijd']}"
        else:  # trainingen
            return f"{event['titel']} — {event['datum']} {event['tijd']}"
    return None

# Tonen van het dashboard, met verschillende data voor trainer en speler.
@dashboard_bp.route("/dashboard", endpoint="dashboard")
@login_required
def dashboard():
    role = session.get("role")
    
    # Volgende wedstrijd en training voor beide rollen
    next_match = get_next_event("wedstrijden")
    next_training = get_next_event("trainingen")
    
    if role == "trainer":
        # Trainer ziet overzichtskaartjes met aantallen.
        spelers_count = query_db("SELECT COUNT(*) AS c FROM spelers", one=True)["c"]
        trainingen_count = query_db("SELECT COUNT(*) AS c FROM trainingen", one=True)["c"]
        wedstrijden_count = query_db("SELECT COUNT(*) AS c FROM wedstrijden", one=True)["c"]
        return render_template(
            "basis/dashboard.html",
            role=role,
            spelers_count=spelers_count,
            trainingen_count=trainingen_count,
            wedstrijden_count=wedstrijden_count,
            next_match=next_match,
            next_training=next_training,
        )

    # Speler ziet zijn eigen gegevens en aankomende activiteiten.
    speler_id = session.get("speler_id")
    speler = query_db("SELECT * FROM spelers WHERE id=?", (speler_id,), one=True)
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    
    # Haal alleen trainingen op die in de toekomst liggen (datum > vandaag of datum = vandaag en tijd > nu)
    trainingen = query_db(
        "SELECT * FROM trainingen WHERE datum > ? OR (datum = ? AND tijd > ?) ORDER BY datum, tijd LIMIT 5",
        (today, today, current_time)
    )
    wedstrijden = query_db(
        "SELECT * FROM wedstrijden WHERE datum > ? OR (datum = ? AND tijd > ?) ORDER BY datum, tijd LIMIT 5",
        (today, today, current_time)
    )
    meldingen = query_db(
        "SELECT w.* FROM wedstrijden w "
        "JOIN wedstrijd_spelers ws ON w.id = ws.wedstrijd_id "
        "WHERE (w.datum > ? OR (w.datum = ? AND w.tijd > ?)) AND ws.speler_id = ? "
        "ORDER BY w.datum, w.tijd",
        (today, today, current_time, speler_id),
    )
    return render_template(
        "basis/dashboard.html",
        role=role,
        speler=speler,
        trainingen=trainingen,
        wedstrijden=wedstrijden,
        meldingen=meldingen,
        next_match=next_match,
        next_training=next_training,
    )
