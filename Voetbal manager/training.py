from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query_db
from auth import login_required
from datetime import datetime

# ============================================================================
# TRAININGSGEBRUIK
# ============================================================================
# Dit bestand bevat alle functies voor het beheren van trainingen.
# Trainers kunnen trainingen aanmaken, wijzigen en verwijderen.
# Spelers kunnen toekomstige trainingen bekijken.

training_bp = Blueprint("training", __name__)

# ROUTE: Overzicht van trainingen
# GET: Toont lijst met alle trainingen (trainers zien alles, spelers zien alleen toekomst)
@training_bp.route("/training", endpoint="training_list")
@login_required
def training_list():
    # Controleer de rol van de gebruiker
    if session.get("role") == "trainer":
        # Trainers zien alle trainingen (ook verleden)
        trainingen = query_db("SELECT * FROM trainingen ORDER BY datum, tijd")
    else:
        # Spelers zien alleen toekomstige trainingen
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        trainingen = query_db(
            "SELECT * FROM trainingen WHERE datum > ? OR (datum = ? AND tijd > ?) ORDER BY datum, tijd",
            (today, today, current_time)
        )
    
    # Toon training overzicht
    return render_template("training/training.html", trainingen=trainingen)

# ROUTE: Nieuwe training toevoegen
# GET: Toont formulier voor nieuwe training
# POST: Verwerkt formulier en slaat training op
@training_bp.route("/training/add", methods=["GET", "POST"], endpoint="training_add")
@login_required
def training_add():
    # Alleen trainers mogen trainingen toevoegen
    if session.get("role") != "trainer":
        return redirect(url_for("training.training_list"))

    if request.method == "POST":
        # Haal formuliergegevens op
        titel = request.form["titel"].strip()          # Naam van training
        datum = request.form["datum"].strip()          # Datum (YYYY-MM-DD)
        tijd = request.form["tijd"].strip()            # Begintijd (HH:MM)
        locatie = request.form.get("locatie", "").strip()           # Locatie waar training plaatsvindt
        beschrijving = request.form.get("beschrijving", "").strip()  # Extra informatie

        # ---- OPSLAAN: Voeg training toe aan database ----
        query_db(
            "INSERT INTO trainingen (titel, datum, tijd, locatie, beschrijving) "
            "VALUES (?,?,?,?,?)",
            (titel, datum, tijd, locatie, beschrijving),
            commit=True,
        )
        # Terug naar overzicht
        return redirect(url_for("training.training_list"))

    # Bij GET request: toon het formulier
    return render_template("training/training_detail.html", training=None)

# ROUTE: Training details bekijken of bewerken
# GET: Toont details van een training
# POST: Update training gegevens (alleen voor trainer)
@training_bp.route("/training/<int:training_id>", methods=["GET", "POST"], endpoint="training_detail")
@login_required
def training_detail(training_id):
    # Zoek de training in database
    training = query_db(
        "SELECT * FROM trainingen WHERE id=?", (training_id,), one=True
    )
    
    # Training niet gevonden?
    if not training:
        return redirect(url_for("training.training_list"))

    # Alleen trainers mogen wijzigingen maken
    if request.method == "POST" and session.get("role") == "trainer":
        # Haal nieuwe gegevens op
        titel = request.form["titel"].strip()
        datum = request.form["datum"].strip()
        tijd = request.form["tijd"].strip()
        locatie = request.form.get("locatie", "").strip()
        beschrijving = request.form.get("beschrijving", "").strip()

        # ---- OPSLAAN: Update training in database ----
        query_db(
            "UPDATE trainingen SET titel=?, datum=?, tijd=?, locatie=?, beschrijving=? "
            "WHERE id=?",
            (titel, datum, tijd, locatie, beschrijving, training_id),
            commit=True,
        )
        # Terug naar overzicht
        return redirect(url_for("training.training_list"))

    # Toon training details
    return render_template(
        "training/training_detail.html",
        training=training,
    )

# ROUTE: Training verwijderen
# Verwijdert een training compleet uit het systeem
@training_bp.route("/training/delete/<int:training_id>", endpoint="training_delete")
@login_required
def training_delete(training_id):
    # Alleen trainers mogen trainingen verwijderen
    if session.get("role") != "trainer":
        return redirect(url_for("training.training_list"))
    
    # Verwijder training uit database
    query_db("DELETE FROM trainingen WHERE id=?", (training_id,), commit=True)
    
    # Terug naar overzicht
    return redirect(url_for("training.training_list"))
