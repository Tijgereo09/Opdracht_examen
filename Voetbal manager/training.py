from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query_db
from auth import login_required

# Trainingbeheer en routes voor overzicht, toevoegen, wijzigen en verwijderen.
training_bp = Blueprint("training", __name__)

# Toon een overzicht van alle trainingen.
@training_bp.route("/training", endpoint="training_list")
@login_required
def training_list():
    trainingen = query_db("SELECT * FROM trainingen ORDER BY datum, tijd")
    return render_template("training/training.html", trainingen=trainingen)

# Nieuwe training toevoegen door de trainer.
@training_bp.route("/training/add", methods=["GET", "POST"], endpoint="training_add")
@login_required
def training_add():
    if session.get("role") != "trainer":
        return redirect(url_for("training.training_list"))

    if request.method == "POST":
        titel = request.form["titel"].strip()
        datum = request.form["datum"].strip()
        tijd = request.form["tijd"].strip()
        locatie = request.form.get("locatie", "").strip()
        beschrijving = request.form.get("beschrijving", "").strip()

        query_db(
            "INSERT INTO trainingen (titel, datum, tijd, locatie, beschrijving) "
            "VALUES (?,?,?,?,?)",
            (titel, datum, tijd, locatie, beschrijving),
            commit=True,
        )
        return redirect(url_for("training.training_list"))

    return render_template("training/training_detail.html", training=None)

# Toon of bewerk een bestaande training.
@training_bp.route("/training/<int:training_id>", methods=["GET", "POST"], endpoint="training_detail")
@login_required
def training_detail(training_id):
    training = query_db(
        "SELECT * FROM trainingen WHERE id=?", (training_id,), one=True
    )
    if not training:
        return redirect(url_for("training.training_list"))

    if request.method == "POST" and session.get("role") == "trainer":
        titel = request.form["titel"].strip()
        datum = request.form["datum"].strip()
        tijd = request.form["tijd"].strip()
        locatie = request.form.get("locatie", "").strip()
        beschrijving = request.form.get("beschrijving", "").strip()

        query_db(
            "UPDATE trainingen SET titel=?, datum=?, tijd=?, locatie=?, beschrijving=? "
            "WHERE id=?",
            (titel, datum, tijd, locatie, beschrijving, training_id),
            commit=True,
        )
        return redirect(url_for("training.training_list"))

    return render_template(
        "training/training_detail.html",
        training=training,
    )

# Training verwijderen door de trainer.
@training_bp.route("/training/delete/<int:training_id>", endpoint="training_delete")
@login_required
def training_delete(training_id):
    if session.get("role") != "trainer":
        return redirect(url_for("training.training_list"))
    query_db("DELETE FROM trainingen WHERE id=?", (training_id,), commit=True)
    return redirect(url_for("training.training_list"))
