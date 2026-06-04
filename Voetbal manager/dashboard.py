from flask import Blueprint, render_template, session
from db import query_db
from auth import login_required
from datetime import datetime

# ============================================================================
# DASHBOARD
# ============================================================================
# Dit bestand bevat het dashboard dat trainers en spelers zien nadat ze inloggen.
# Trainers zien een overzicht met statistieken.
# Spelers zien hun persoonlijke gegevens en aankomende activiteiten.

dashboard_bp = Blueprint("dashboard", __name__)

# HULPFUNCTIE: get_next_event()
# Zoekt het volgende aankomende event (training of wedstrijd) op basis van datum en tijd
# Parameters:
#   - table: 'trainingen' of 'wedstrijden'
#   - date_col: naam van datumkolom
#   - time_col: naam van tijdkolom
#   - desc_col: beschrijvingskolom (titel/tegenstander)
# Return: String met event-info of None als geen toekomst event
def get_next_event(table, date_col="datum", time_col="tijd", desc_col=None):
    """Zoekt het volgende event dat nog moet plaatsvinden."""
    # Haal huidige datum en tijd op
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    
    # Bouw SQL-query om toekomstige events te zoeken
    # Events moeten in de toekomst liggen (datum > vandaag OR (datum = vandaag EN tijd > nu))
    query = f"""
        SELECT * FROM {table}
        WHERE {date_col} > ? 
           OR ({date_col} = ? AND {time_col} > ?)
        ORDER BY {date_col}, {time_col}
        LIMIT 1
    """
    # Voer query uit
    event = query_db(query, (today, today, current_time), one=True)
    
    if event:
        # Event gevonden! Format de informatie voor weergave
        if table == "wedstrijden":
            # Voor wedstrijden: toon tegenstander, datum en tijd
            return f"{event['tegenstander']} — {event['datum']} {event['tijd']}"
        else:  # trainingen
            # Voor trainingen: toon titel, datum en tijd
            return f"{event['titel']} — {event['datum']} {event['tijd']}"
    
    # Geen toekomstig event gevonden
    return None

# ROUTE: Dashboard
# GET: Toont personaliseerd dashboard afhankelijk van rol (trainer/speler)
@dashboard_bp.route("/dashboard", endpoint="dashboard")
@login_required
def dashboard():
    # Bepaal welke rol de gebruiker heeft
    role = session.get("role")
    
    # Haal de volgende wedstrijd en training op (voor beide rollen)
    next_match = get_next_event("wedstrijden")
    next_training = get_next_event("trainingen")
    
    # ============================================================
    # TRAINER DASHBOARD
    # ============================================================
    if role == "trainer":
        # Trainer ziet statistieken: totaal aantal spelers, trainingen en wedstrijden
        
        # Tel aantal spelers in database
        spelers_count = query_db("SELECT COUNT(*) AS c FROM spelers", one=True)["c"]
        
        # Tel aantal trainingen
        trainingen_count = query_db("SELECT COUNT(*) AS c FROM trainingen", one=True)["c"]
        
        # Tel aantal wedstrijden
        wedstrijden_count = query_db("SELECT COUNT(*) AS c FROM wedstrijden", one=True)["c"]
        
        # Toon trainer dashboard met statistieken
        return render_template(
            "basis/dashboard.html",
            role=role,
            spelers_count=spelers_count,
            trainingen_count=trainingen_count,
            wedstrijden_count=wedstrijden_count,
            next_match=next_match,
            next_training=next_training,
        )

    # ============================================================
    # SPELER DASHBOARD
    # ============================================================
    # Haal speler-ID en gegevens uit sessie
    speler_id = session.get("speler_id")
    speler = query_db("SELECT * FROM spelers WHERE id=?", (speler_id,), one=True)
    
    # Bepaal huidige datum en tijd voor filtering
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    
    # Haal de volgende 5 trainingen op (alleen toekomstige trainingen)
    # Trainingen moeten in de toekomst liggen
    trainingen = query_db(
        "SELECT * FROM trainingen WHERE datum > ? OR (datum = ? AND tijd > ?) ORDER BY datum, tijd LIMIT 5",
        (today, today, current_time)
    )
    
    # Haal de volgende 5 wedstrijden op (alleen toekomstige wedstrijden)
    wedstrijden = query_db(
        "SELECT * FROM wedstrijden WHERE datum > ? OR (datum = ? AND tijd > ?) ORDER BY datum, tijd LIMIT 5",
        (today, today, current_time)
    )
    
    # Haal de wedstrijden op waar DIT speler in geselecteerd is
    # Dit zijn meldingen: wedstrijden waar de speler wordt verwacht te spelen
    meldingen = query_db(
        "SELECT w.* FROM wedstrijden w "
        "JOIN wedstrijd_spelers ws ON w.id = ws.wedstrijd_id "
        "WHERE (w.datum > ? OR (w.datum = ? AND w.tijd > ?)) AND ws.speler_id = ? "
        "ORDER BY w.datum, w.tijd",
        (today, today, current_time, speler_id),
    )
    
    # Toon speler dashboard met persoonlijke informatie en activiteiten
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
