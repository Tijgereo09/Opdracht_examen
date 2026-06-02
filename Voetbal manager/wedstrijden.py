import sqlite3
from collections import Counter
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query_db
from auth import login_required

# Wedstrijdbeheer en opstellingslogica voor trainer en speler.
wedstrijden_bp = Blueprint("wedstrijden", __name__)

# Velden voor de basisopstelling.
LINEUP_FIELDS = [
    ("keeper", "Keeper"),
    ("verdediger_1", "Verdediger 1"),
    ("verdediger_2", "Verdediger 2"),
    ("verdediger_3", "Verdediger 3"),
    ("verdediger_4", "Verdediger 4"),
    ("middenvelder_1", "Middenvelder 1"),
    ("middenvelder_2", "Middenvelder 2"),
    ("middenvelder_3", "Middenvelder 3"),
    ("aanvaller_1", "Aanvaller 1"),
    ("aanvaller_2", "Aanvaller 2"),
    ("aanvaller_3", "Aanvaller 3"),
]
# Velden voor spelers op de bank.
BENCH_FIELDS = [
    ("bank_1", "Bank 1"),
    ("bank_2", "Bank 2"),
    ("bank_3", "Bank 3"),
]

# Verwachte positie voor elke veldnaam.
FIELD_POSITION = {
    "keeper": "keeper",
    "verdediger_1": "verdediger",
    "verdediger_2": "verdediger",
    "verdediger_3": "verdediger",
    "verdediger_4": "verdediger",
    "middenvelder_1": "middenvelder",
    "middenvelder_2": "middenvelder",
    "middenvelder_3": "middenvelder",
    "aanvaller_1": "aanvaller",
    "aanvaller_2": "aanvaller",
    "aanvaller_3": "aanvaller",
}

# Normaliseer positiecode voor vergelijking.
def normalize_position(value):
    if not value:
        return ""
    return value.strip().lower()

# Controleert of de spelerpositie bij het geselecteerde veld hoort.
def position_matches(field_name, speler_positie):
    expected = FIELD_POSITION.get(field_name)
    if not expected:
        return True
    speler_pos = normalize_position(speler_positie)
    return expected in speler_pos

# Haal de opstelling en bank op voor een wedstrijd.
def get_wedstrijd_lineup(wedstrijd_id):
    rows = query_db(
        "SELECT ws.*, s.username, s.positie AS speler_positie, s.rugnummer "
        "FROM wedstrijd_spelers ws "
        "JOIN spelers s ON ws.speler_id = s.id "
        "WHERE ws.wedstrijd_id = ?",
        (wedstrijd_id,),
    )
    lineup = {}
    bench = {}
    for row in rows:
        position = row["positie"]
        if not position:
            continue
        if row["bank"] == 1:
            bench[position] = row
        else:
            lineup[position] = row
    return lineup, bench

# Sla de volledige wedstrijdopstelling op in de database.
def update_wedstrijd_lineup(wedstrijd_id, lineup_data, bench_data):
    query_db(
        "DELETE FROM wedstrijd_spelers WHERE wedstrijd_id = ?",
        (wedstrijd_id,),
        commit=True,
    )
    for positie, speler_id in lineup_data.items():
        if speler_id:
            query_db(
                "INSERT INTO wedstrijd_spelers (wedstrijd_id, speler_id, positie, bank) VALUES (?,?,?,0)",
                (wedstrijd_id, speler_id, positie),
                commit=True,
            )
    for positie, speler_id in bench_data.items():
        if speler_id:
            query_db(
                "INSERT INTO wedstrijd_spelers (wedstrijd_id, speler_id, positie, bank) VALUES (?,?,?,1)",
                (wedstrijd_id, speler_id, positie),
                commit=True,
            )

# Bouw de selectie van spelers voor de basisopstelling vanuit het formulier.
def build_lineup_from_form(form):
    lineup = {}
    for name, _ in LINEUP_FIELDS:
        value = form.get(name, "")
        lineup[name] = int(value) if value and value.isdigit() else None
    return lineup

# Bouw de selectie van bankspelers vanuit het formulier.
def build_bench_from_form(form):
    bench = {}
    for name, _ in BENCH_FIELDS:
        value = form.get(name, "")
        bench[name] = int(value) if value and value.isdigit() else None
    return bench

# Extraheer de geselecteerde spelers-ID's uit lineup en bench.
def get_selected_player_ids(lineup, bench):
    ids = []
    for value in list(lineup.values()) + list(bench.values()):
        if not value:
            continue
        try:
            ids.append(value["speler_id"])
        except Exception:
            ids.append(value)
    return ids

# Map de gekozen opdrachtvelden naar speler-ID's.
def get_assignment_ids(assignments):
    return {name: value["speler_id"] for name, value in assignments.items()}

# Bouw een preview van lineup/bench met volledige spelergegevens voor display.
def build_lineup_preview(assignments, spelers):
    player_map = {s["id"]: s for s in spelers} if spelers else {}
    preview = {}
    for name, value in assignments.items():
        if not value:
            preview[name] = None
        elif isinstance(value, int):
            preview[name] = player_map.get(value)
        else:
            preview[name] = value
    return preview

# Laat een overzicht van alle wedstrijden zien.
@wedstrijden_bp.route("/wedstrijden", endpoint="wedstrijden_list")
@login_required
def wedstrijden_list():
    wedstrijden = query_db("SELECT * FROM wedstrijden ORDER BY datum, tijd")
    return render_template("wedstrijden/wedstrijden.html", wedstrijden=wedstrijden)

# Nieuwe wedstrijd toevoegen en opstelling kiezen.
@wedstrijden_bp.route("/wedstrijden/add", methods=["GET", "POST"], endpoint="wedstrijden_add")
@login_required
def wedstrijden_add():
    if session.get("role") != "trainer":
        return redirect(url_for("wedstrijden.wedstrijden_list"))

    spelers = query_db("SELECT * FROM spelers ORDER BY username")
    if request.method == "POST":
        tegenstander = request.form["tegenstander"].strip()
        datum = request.form["datum"].strip()
        tijd = request.form["tijd"].strip()
        locatie = request.form.get("locatie", "").strip()
        thuis_uit = request.form.get("thuis_uit", "").strip()
        lineup = build_lineup_from_form(request.form)
        bench = build_bench_from_form(request.form)
        selected_ids = get_selected_player_ids(lineup, bench)
        duplicate_ids = [pid for pid, count in Counter(selected_ids).items() if pid and count > 1]
        errors = []

        if duplicate_ids:
            errors.append("Elke speler kan maar één keer worden geselecteerd.")

        for field_name, speler_id in lineup.items():
            if speler_id:
                speler = next((s for s in spelers if s["id"] == speler_id), None)
                if not speler or not position_matches(field_name, speler["positie"]):
                    label = dict(LINEUP_FIELDS).get(field_name, field_name)
                    errors.append(
                        f"De speler voor {label} heeft niet de juiste positie. Kies een speler met de juiste positie."
                    )

        if errors:
            for message in errors:
                flash(message, "error")
            return render_template(
                "wedstrijden/wedstrijd_detail.html",
                wedstrijd=None,
                spelers=spelers,
                lineup=build_lineup_preview(lineup, spelers),
                bench=build_lineup_preview(bench, spelers),
                lineup_ids=lineup,
                bench_ids=bench,
                selected_player_ids=selected_ids,
                selected_spelers=[],
                LINEUP_FIELDS=LINEUP_FIELDS,
                BENCH_FIELDS=BENCH_FIELDS,
                FIELD_POSITION=FIELD_POSITION,
                comments=[],
            )

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO wedstrijden (tegenstander, datum, tijd, locatie, thuis_uit) "
            "VALUES (?,?,?,?,?)",
            (tegenstander, datum, tijd, locatie, thuis_uit),
        )
        wedstrijd_id = cur.lastrowid
        conn.commit()
        conn.close()

        update_wedstrijd_lineup(wedstrijd_id, lineup, bench)
        return redirect(url_for("wedstrijden.wedstrijden_list"))

    return render_template(
        "wedstrijden/wedstrijd_detail.html",
        wedstrijd=None,
        spelers=spelers,
        lineup={},
        bench={},
        lineup_ids={},
        bench_ids={},
        selected_player_ids=[],
        selected_spelers=[],
        LINEUP_FIELDS=LINEUP_FIELDS,
        BENCH_FIELDS=BENCH_FIELDS,
        FIELD_POSITION=FIELD_POSITION,
        comments=[],
    )

# Bekijk of bewerk een bestaande wedstrijd.
@wedstrijden_bp.route("/wedstrijden/<int:wedstrijd_id>", methods=["GET", "POST"], endpoint="wedstrijden_detail")
@login_required
def wedstrijden_detail(wedstrijd_id):
    wedstrijd = query_db(
        "SELECT * FROM wedstrijden WHERE id=?", (wedstrijd_id,), one=True
    )
    if not wedstrijd:
        return redirect(url_for("wedstrijden.wedstrijden_list"))

    spelers = query_db("SELECT * FROM spelers ORDER BY username") if session.get("role") == "trainer" else None
    lineup, bench = get_wedstrijd_lineup(wedstrijd_id)
    lineup_ids = get_assignment_ids(lineup)
    bench_ids = get_assignment_ids(bench)
    selected_player_ids = get_selected_player_ids(lineup, bench)
    selected_spelers = []
    if session.get("role") != "trainer":
        selected_spelers = [row for row in lineup.values()] + list(bench.values())

    if request.method == "POST" and session.get("role") == "trainer":
        tegenstander = request.form["tegenstander"].strip()
        datum = request.form["datum"].strip()
        tijd = request.form["tijd"].strip()
        locatie = request.form.get("locatie", "").strip()
        thuis_uit = request.form.get("thuis_uit", "").strip()
        lineup = build_lineup_from_form(request.form)
        bench = build_bench_from_form(request.form)
        selected_ids = get_selected_player_ids(lineup, bench)
        duplicate_ids = [pid for pid, count in Counter(selected_ids).items() if pid and count > 1]
        errors = []

        if duplicate_ids:
            errors.append("Elke speler kan maar één keer worden geselecteerd.")

        for field_name, speler_id in lineup.items():
            if speler_id:
                speler = next((s for s in spelers if s["id"] == speler_id), None)
                if not speler or not position_matches(field_name, speler["positie"]):
                    label = dict(LINEUP_FIELDS).get(field_name, field_name)
                    errors.append(
                        f"De speler voor {label} heeft niet de juiste positie. Kies een speler met de juiste positie."
                    )

        if errors:
            for message in errors:
                flash(message, "error")
            return render_template(
                "wedstrijden/wedstrijd_detail.html",
                wedstrijd=wedstrijd,
                spelers=spelers,
                lineup=build_lineup_preview(lineup, spelers),
                bench=build_lineup_preview(bench, spelers),
                lineup_ids=lineup,
                bench_ids=bench,
                selected_player_ids=selected_ids,
                selected_spelers=selected_spelers,
                LINEUP_FIELDS=LINEUP_FIELDS,
                BENCH_FIELDS=BENCH_FIELDS,
                FIELD_POSITION=FIELD_POSITION,
            )

        query_db(
            "UPDATE wedstrijden SET tegenstander=?, datum=?, tijd=?, locatie=?, thuis_uit=? "
            "WHERE id=?",
            (tegenstander, datum, tijd, locatie, thuis_uit, wedstrijd_id),
            commit=True,
        )
        update_wedstrijd_lineup(wedstrijd_id, lineup, bench)
        return redirect(url_for("wedstrijden.wedstrijden_list"))

    return render_template(
        "wedstrijden/wedstrijd_detail.html",
        wedstrijd=wedstrijd,
        spelers=spelers,
        lineup=build_lineup_preview(lineup, spelers) if spelers else lineup,
        bench=build_lineup_preview(bench, spelers) if spelers else bench,
        lineup_ids=lineup_ids,
        bench_ids=bench_ids,
        selected_player_ids=selected_player_ids,
        selected_spelers=selected_spelers,
        LINEUP_FIELDS=LINEUP_FIELDS,
        BENCH_FIELDS=BENCH_FIELDS,
        FIELD_POSITION=FIELD_POSITION,
    )

# Verwijder een wedstrijd inclusief bijbehorende opstelling.
@wedstrijden_bp.route("/wedstrijden/delete/<int:wedstrijd_id>", endpoint="wedstrijden_delete")
@login_required
def wedstrijden_delete(wedstrijd_id):
    if session.get("role") != "trainer":
        return redirect(url_for("wedstrijden.wedstrijden_list"))
    query_db(
        "DELETE FROM wedstrijd_spelers WHERE wedstrijd_id = ?",
        (wedstrijd_id,),
        commit=True,
    )
    query_db("DELETE FROM wedstrijden WHERE id=?", (wedstrijd_id,), commit=True)
    return redirect(url_for("wedstrijden.wedstrijden_list"))
