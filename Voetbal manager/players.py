from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query_db
from auth import login_required

# ============================================================================
# SPELERBEHEER
# ============================================================================
# Dit bestand bevat alle functies voor het beheren van spelers
# Deze functies zijn alleen beschikbaar voor trainers

players_bp = Blueprint("players", __name__)

# ROUTE: Overzicht van alle spelers
# GET: Toont een lijst met alle geregistreerde spelers
# Alleen trainers hebben toegang tot deze pagina
@players_bp.route("/players", endpoint="players_list")
@login_required
def players_list():
    # Controleer of de ingelogde gebruiker een trainer is
    if session.get("role") != "trainer":
        # Alleen trainers mogen hier komen, spelers worden terugstuurd
        return redirect(url_for("dashboard.dashboard"))
    
    # Haal alle spelers uit de database en sorteer op gebruikersnaam
    spelers = query_db("SELECT * FROM spelers ORDER BY username")
    
    # Toon het spelersoverzicht
    return render_template("players/players.html", spelers=spelers)

# ROUTE: Nieuwe speler toevoegen
# GET: Toont formulier om een nieuwe speler in te voeren
# POST: Verwerkt het formulier en voegt speler toe aan database
@players_bp.route("/players/add", methods=["GET", "POST"], endpoint="players_add")
@login_required
def players_add():
    # Alleen trainers mogen spelers toevoegen
    if session.get("role") != "trainer":
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        # Haal formuliergegevens op en verwijder spaties
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        positie = request.form.get("positie", "").strip()  # Positie (keeper, verdediger, etc.)
        rugnummer = request.form.get("rugnummer", "").strip()  # Rugnummer van speler
        team = request.form.get("team", "").strip()  # Team (optioneel)

        # ---- VALIDATIE: Controleer rugnummer ----
        # Rugnummer moet een getal zijn tussen 1 en 99
        if not rugnummer.isdigit() or int(rugnummer) < 1 or int(rugnummer) > 99:
            flash("Rugnummer moet tussen 1 en 99 liggen.", "error")
            return redirect(url_for("players.players_add"))

        # ---- VALIDATIE: Controleer of rugnummer uniek is ----
        existing = query_db(
            "SELECT id FROM spelers WHERE rugnummer=?",
            (rugnummer,),
            one=True,
        )
        if existing:
            flash("Dit rugnummer is al in gebruik.", "error")
            return redirect(url_for("players.players_add"))

        # ---- VALIDATIE: Controleer verplichte velden ----
        if not username or not password:
            flash("Gebruikersnaam en wachtwoord zijn verplicht.", "error")
            return redirect(url_for("players.players_add"))

        # ---- OPSLAAN: Voeg nieuwe speler toe aan database ----
        query_db(
            "INSERT INTO spelers (username, password, positie, rugnummer, team) "
            "VALUES (?,?,?,?,?)",
            (username, password, positie, rugnummer, team),
            commit=True,
        )
        # Terug naar overzicht
        return redirect(url_for("players.players_list"))

    # Bij GET request: toon het formulier
    return render_template("players/players_add.html")

# ROUTE: Spelergegevens bewerken
# GET: Toont formulier met huidige gegevens van speler
# POST: Slaat wijzigingen op in database
@players_bp.route("/players/edit/<int:speler_id>", methods=["GET", "POST"], endpoint="players_edit")
@login_required
def players_edit(speler_id):
    # Alleen trainers mogen spelers bewerken
    if session.get("role") != "trainer":
        return redirect(url_for("dashboard.dashboard"))

    # Zoek de speler in database
    speler = query_db("SELECT * FROM spelers WHERE id=?", (speler_id,), one=True)
    if not speler:
        # Speler niet gevonden, terug naar overzicht
        return redirect(url_for("players.players_list"))

    if request.method == "POST":
        # Haal aangepaste gegevens op uit formulier
        username = request.form["username"].strip()
        positie = request.form.get("positie", "").strip()
        rugnummer = request.form.get("rugnummer", "").strip()
        team = request.form.get("team", "").strip()

        # ---- VALIDATIE: Controleer rugnummer ----
        if not rugnummer.isdigit() or int(rugnummer) < 1 or int(rugnummer) > 99:
            flash("Rugnummer moet tussen 1 en 99 liggen.", "error")
            return redirect(url_for("players_edit", speler_id=speler_id))

        # ---- VALIDATIE: Controleer of rugnummer al in gebruik is (door ander speler) ----
        existing = query_db(
            "SELECT id FROM spelers WHERE rugnummer=? AND id<>?",
            (rugnummer, speler_id),  # Sluit huidige speler uit
            one=True,
        )
        if existing:
            flash("Dit rugnummer is al in gebruik.", "error")
            return redirect(url_for("players_edit", speler_id=speler_id))

        # ---- OPSLAAN: Update spelergegevens ----
        query_db(
            "UPDATE spelers SET username=?, positie=?, rugnummer=?, team=? WHERE id=?",
            (username, positie, rugnummer, team, speler_id),
            commit=True,
        )
        return redirect(url_for("players.players_list"))

    # Bij GET request: toon formulier met huidige gegevens
    return render_template("players/players_edit.html", speler=speler)

# ROUTE: Speler verwijderen
# Verwijdert een speler volledig uit het systeem
@players_bp.route("/players/delete/<int:speler_id>", endpoint="players_delete")
@login_required
def players_delete(speler_id):
    # Alleen trainers mogen spelers verwijderen
    if session.get("role") != "trainer":
        return redirect(url_for("dashboard.dashboard"))
    
    # Verwijder speler uit database
    query_db("DELETE FROM spelers WHERE id=?", (speler_id,), commit=True)
    
    # Terug naar spelers overzicht
    return redirect(url_for("players.players_list"))
