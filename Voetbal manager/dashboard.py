from flask import Blueprint, render_template, session
from auth import login_required
from db import query_db

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    role = session.get("role")
    user_id = session.get("speler_id")  # bestaat alleen voor spelers

    # -------------------------------------------------------------
    # SPELERDATA OPHALEN (ALLEEN VOOR SPELER)
    # -------------------------------------------------------------
    speler = None
    if role == "speler":
        speler = query_db(
            "SELECT username, positie, rugnummer, team FROM spelers WHERE id=?",
            (user_id,),
            one=True
        )

    # -------------------------------------------------------------
    # TRAINER: spelerslijst ophalen voor privéchats
    # -------------------------------------------------------------
    spelers = []
    if role == "trainer":
        spelers = query_db("SELECT id, username FROM spelers")

    # -------------------------------------------------------------
    # TRAINER: statistieken
    # -------------------------------------------------------------
    spelers_count = trainingen_count = wedstrijden_count = None

    if role == "trainer":
        spelers_count = query_db("SELECT COUNT(*) AS c FROM spelers", one=True)["c"]
        trainingen_count = query_db("SELECT COUNT(*) AS c FROM trainingen", one=True)["c"]
        wedstrijden_count = query_db("SELECT COUNT(*) AS c FROM wedstrijden", one=True)["c"]

    # -------------------------------------------------------------
    # SPELER: meldingen + trainingen
    # -------------------------------------------------------------
    meldingen = []
    trainingen = []

    if role == "speler":
        meldingen = query_db(
            "SELECT * FROM meldingen WHERE speler_id=? ORDER BY datum ASC",
            (user_id,)
        )
        trainingen = query_db(
            "SELECT * FROM trainingen WHERE datum >= DATE('now') ORDER BY datum ASC"
        )

    # -------------------------------------------------------------
    # VOLGENDE TRAINING & WEDSTRIJD
    # -------------------------------------------------------------
    next_training = query_db(
        "SELECT titel FROM trainingen WHERE datum >= DATE('now') ORDER BY datum ASC LIMIT 1",
        one=True
    )
    next_match = query_db(
        "SELECT tegenstander FROM wedstrijden WHERE datum >= DATE('now') ORDER BY datum ASC LIMIT 1",
        one=True
    )

    next_training = next_training["titel"] if next_training else None
    next_match = next_match["tegenstander"] if next_match else None

    # -------------------------------------------------------------
    # TEMPLATE RENDEREN
    # -------------------------------------------------------------
    return render_template(
        "basis/dashboard.html",
        role=role,
        speler=speler,
        spelers=spelers,
        spelers_count=spelers_count,
        trainingen_count=trainingen_count,
        wedstrijden_count=wedstrijden_count,
        meldingen=meldingen,
        trainingen=trainingen,
        next_training=next_training,
        next_match=next_match
    )
