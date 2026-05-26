from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query_db
from auth import login_required

# Blueprint voor spelerbeheer door de trainer.
players_bp = Blueprint("players", __name__)

# Lijst met alle spelers, alleen zichtbaar voor trainers.
@players_bp.route("/players", endpoint="players_list")
@login_required
def players_list():
    if session.get("role") != "trainer":
        return redirect(url_for("dashboard.dashboard"))
    spelers = query_db("SELECT * FROM spelers ORDER BY username")
    return render_template("players/players.html", spelers=spelers)

# Nieuwe speler toevoegen.
@players_bp.route("/players/add", methods=["GET", "POST"], endpoint="players_add")
@login_required
def players_add():
    if session.get("role") != "trainer":
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        positie = request.form.get("positie", "").strip()
        rugnummer = request.form.get("rugnummer", "").strip()
        team = request.form.get("team", "").strip()

        # Validatie van rugnummer en unieke waarde.
        if not rugnummer.isdigit() or int(rugnummer) < 1 or int(rugnummer) > 99:
            flash("Rugnummer moet tussen 1 en 99 liggen.", "error")
            return redirect(url_for("players.players_add"))

        existing = query_db(
            "SELECT id FROM spelers WHERE rugnummer=?",
            (rugnummer,),
            one=True,
        )
        if existing:
            flash("Dit rugnummer is al in gebruik.", "error")
            return redirect(url_for("players.players_add"))

        if not username or not password:
            flash("Gebruikersnaam en wachtwoord zijn verplicht.", "error")
            return redirect(url_for("players.players_add"))

        query_db(
            "INSERT INTO spelers (username, password, positie, rugnummer, team) "
            "VALUES (?,?,?,?,?)",
            (username, password, positie, rugnummer, team),
            commit=True,
        )
        return redirect(url_for("players.players_list"))

    return render_template("players/players_add.html")

# Spelergegevens bewerken.
@players_bp.route("/players/edit/<int:speler_id>", methods=["GET", "POST"], endpoint="players_edit")
@login_required
def players_edit(speler_id):
    if session.get("role") != "trainer":
        return redirect(url_for("dashboard.dashboard"))

    speler = query_db("SELECT * FROM spelers WHERE id=?", (speler_id,), one=True)
    if not speler:
        return redirect(url_for("players.players_list"))

    if request.method == "POST":
        username = request.form["username"].strip()
        positie = request.form.get("positie", "").strip()
        rugnummer = request.form.get("rugnummer", "").strip()
        team = request.form.get("team", "").strip()

        if not rugnummer.isdigit() or int(rugnummer) < 1 or int(rugnummer) > 99:
            flash("Rugnummer moet tussen 1 en 99 liggen.", "error")
            return redirect(url_for("players_edit", speler_id=speler_id))

        existing = query_db(
            "SELECT id FROM spelers WHERE rugnummer=? AND id<>?",
            (rugnummer, speler_id),
            one=True,
        )
        if existing:
            flash("Dit rugnummer is al in gebruik.", "error")
            return redirect(url_for("players_edit", speler_id=speler_id))

        query_db(
            "UPDATE spelers SET username=?, positie=?, rugnummer=?, team=? WHERE id=?",
            (username, positie, rugnummer, team, speler_id),
            commit=True,
        )
        return redirect(url_for("players.players_list"))

    return render_template("players/players_edit.html", speler=speler)

# Speler verwijderen.
@players_bp.route("/players/delete/<int:speler_id>", endpoint="players_delete")
@login_required
def players_delete(speler_id):
    if session.get("role") != "trainer":
        return redirect(url_for("dashboard.dashboard"))
    query_db("DELETE FROM spelers WHERE id=?", (speler_id,), commit=True)
    return redirect(url_for("players.players_list"))
