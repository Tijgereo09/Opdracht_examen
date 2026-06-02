from flask import Blueprint, render_template, session
from db import query_db
from auth import login_required

# Dashboardfunctionaliteit voor trainer en speler.
dashboard_bp = Blueprint("dashboard", __name__)

# Tonen van het dashboard, met verschillende data voor trainer en speler.
@dashboard_bp.route("/dashboard", endpoint="dashboard")
@login_required
def dashboard():
    role = session.get("role")
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
        )

    # Speler ziet zijn eigen gegevens en aankomende activiteiten.
    speler_id = session.get("speler_id")
    speler = query_db("SELECT * FROM spelers WHERE id=?", (speler_id,), one=True)
    trainingen = query_db("SELECT * FROM trainingen ORDER BY datum, tijd LIMIT 5")
    wedstrijden = query_db("SELECT * FROM wedstrijden ORDER BY datum, tijd LIMIT 5")
    meldingen = query_db(
        "SELECT w.* FROM wedstrijden w "
        "JOIN wedstrijd_spelers ws ON w.id = ws.wedstrijd_id "
        "WHERE ws.speler_id = ? "
        "ORDER BY w.datum, w.tijd",
        (speler_id,),
    )
    return render_template(
        "basis/dashboard.html",
        role=role,
        speler=speler,
        trainingen=trainingen,
        wedstrijden=wedstrijden,
        meldingen=meldingen,
    )
