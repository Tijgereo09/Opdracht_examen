from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import create_db
from datetime import datetime

# database altijd controleren en aanmaken bij starten
create_db.create_database()

app = Flask(__name__)
app.secret_key = "supersecret_exam_key"

def format_date(value):
    if not value:
        return ""
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
        return parsed.strftime("%d/%m/%Y")
    except ValueError:
        return value

app.jinja_env.filters["datetimeformat"] = format_date

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


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


# ---------- LOGIN / REGISTER ----------
@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        # hardcoded trainer
        if username == "trainer" and password == "voetbal123":
            session["user"] = "trainer"
            session["role"] = "trainer"
            return redirect(url_for("dashboard"))

        speler = query_db(
            "SELECT * FROM spelers WHERE username=? AND password=?",
            (username, password),
            one=True,
        )
        if speler:
            session["user"] = speler["username"]
            session["role"] = "speler"
            session["speler_id"] = speler["id"]
            return redirect(url_for("dashboard"))

        flash("Ongeldige login.", "error")

    return render_template("login/login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        positie = request.form.get("positie", "").strip()
        rugnummer = request.form.get("rugnummer", "").strip()
        team = request.form.get("team", "").strip()

        # rugnummer check
        if not rugnummer.isdigit() or int(rugnummer) < 1 or int(rugnummer) > 99:
            flash("Rugnummer moet tussen 1 en 99 liggen.", "error")
            return redirect(url_for("register"))

        # uniek rugnummer
        existing = query_db(
            "SELECT id FROM spelers WHERE rugnummer=?",
            (rugnummer,),
            one=True,
        )
        if existing:
            flash("Dit rugnummer is al in gebruik.", "error")
            return redirect(url_for("register"))

        # verplichte velden
        if not username or not password:
            flash("Gebruikersnaam en wachtwoord zijn verplicht.", "error")
            return redirect(url_for("register"))

        # speler opslaan
        query_db(
            "INSERT INTO spelers (username, password, positie, rugnummer, team) "
            "VALUES (?,?,?,?,?)",
            (username, password, positie, rugnummer, team),
            commit=True,
        )

        flash("Account aangemaakt, je kan nu inloggen.", "success")
        return redirect(url_for("login"))

    return render_template("login/register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- LOGIN REQUIRED ----------
def login_required(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return wrapper


# ---------- DASHBOARD ----------
@app.route("/dashboard")
@login_required
def dashboard():
    role = session.get("role")
    if role == "trainer":
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
    else:
        speler_id = session.get("speler_id")
        speler = query_db("SELECT * FROM spelers WHERE id=?", (speler_id,), one=True)
        trainingen = query_db("SELECT * FROM trainingen ORDER BY datum, tijd LIMIT 5")
        wedstrijden = query_db("SELECT * FROM wedstrijden ORDER BY datum, tijd LIMIT 5")
        return render_template(
            "basis/dashboard.html",
            role=role,
            speler=speler,
            trainingen=trainingen,
            wedstrijden=wedstrijden,
        )


# ---------- PLAYERS ----------
@app.route("/players")
@login_required
def players_list():
    if session.get("role") != "trainer":
        return redirect(url_for("dashboard"))
    spelers = query_db("SELECT * FROM spelers ORDER BY username")
    return render_template("players/players.html", spelers=spelers)


@app.route("/players/add", methods=["GET", "POST"])
@login_required
def players_add():
    if session.get("role") != "trainer":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        positie = request.form.get("positie", "").strip()
        rugnummer = request.form.get("rugnummer", "").strip()
        team = request.form.get("team", "").strip()

        # rugnummer check
        if not rugnummer.isdigit() or int(rugnummer) < 1 or int(rugnummer) > 99:
            flash("Rugnummer moet tussen 1 en 99 liggen.", "error")
            return redirect(url_for("players_add"))

        # uniek rugnummer
        existing = query_db(
            "SELECT id FROM spelers WHERE rugnummer=?",
            (rugnummer,),
            one=True,
        )
        if existing:
            flash("Dit rugnummer is al in gebruik.", "error")
            return redirect(url_for("players_add"))

        if not username or not password:
            flash("Gebruikersnaam en wachtwoord zijn verplicht.", "error")
            return redirect(url_for("players_add"))

        query_db(
            "INSERT INTO spelers (username, password, positie, rugnummer, team) "
            "VALUES (?,?,?,?,?)",
            (username, password, positie, rugnummer, team),
            commit=True,
        )
        return redirect(url_for("players_list"))

    return render_template("players/players_add.html")


@app.route("/players/edit/<int:speler_id>", methods=["GET", "POST"])
@login_required
def players_edit(speler_id):
    if session.get("role") != "trainer":
        return redirect(url_for("dashboard"))

    speler = query_db("SELECT * FROM spelers WHERE id=?", (speler_id,), one=True)
    if not speler:
        return redirect(url_for("players_list"))

    if request.method == "POST":
        username = request.form["username"].strip()
        positie = request.form.get("positie", "").strip()
        rugnummer = request.form.get("rugnummer", "").strip()
        team = request.form.get("team", "").strip()

        # rugnummer check
        if not rugnummer.isdigit() or int(rugnummer) < 1 or int(rugnummer) > 99:
            flash("Rugnummer moet tussen 1 en 99 liggen.", "error")
            return redirect(url_for("players_edit", speler_id=speler_id))

        # uniek rugnummer (behalve voor zichzelf)
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
        return redirect(url_for("players_list"))

    return render_template("players/players_edit.html", speler=speler)


@app.route("/players/delete/<int:speler_id>")
@login_required
def players_delete(speler_id):
    if session.get("role") != "trainer":
        return redirect(url_for("dashboard"))
    query_db("DELETE FROM spelers WHERE id=?", (speler_id,), commit=True)
    return redirect(url_for("players_list"))


# ---------- TRAINING ----------
@app.route("/training")
@login_required
def training_list():
    trainingen = query_db("SELECT * FROM trainingen ORDER BY datum, tijd")
    return render_template("training/training.html", trainingen=trainingen)


@app.route("/training/add", methods=["GET", "POST"])
@login_required
def training_add():
    if session.get("role") != "trainer":
        return redirect(url_for("training_list"))

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
        return redirect(url_for("training_list"))

    return render_template("training/training_detail.html", training=None)


@app.route("/training/<int:training_id>", methods=["GET", "POST"])
@login_required
def training_detail(training_id):
    training = query_db(
        "SELECT * FROM trainingen WHERE id=?", (training_id,), one=True
    )
    if not training:
        return redirect(url_for("training_list"))

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
        return redirect(url_for("training_list"))

    return render_template("training/training_detail.html", training=training)


@app.route("/training/delete/<int:training_id>")
@login_required
def training_delete(training_id):
    if session.get("role") != "trainer":
        return redirect(url_for("training_list"))
    query_db("DELETE FROM trainingen WHERE id=?", (training_id,), commit=True)
    return redirect(url_for("training_list"))


# ---------- WEDSTRIJDEN ----------
@app.route("/wedstrijden")
@login_required
def wedstrijden_list():
    wedstrijden = query_db("SELECT * FROM wedstrijden ORDER BY datum, tijd")
    return render_template("wedstrijden/wedstrijden.html", wedstrijden=wedstrijden)


@app.route("/wedstrijden/add", methods=["GET", "POST"])
@login_required
def wedstrijden_add():
    if session.get("role") != "trainer":
        return redirect(url_for("wedstrijden_list"))

    if request.method == "POST":
        tegenstander = request.form["tegenstander"].strip()
        datum = request.form["datum"].strip()
        tijd = request.form["tijd"].strip()
        locatie = request.form.get("locatie", "").strip()
        thuis_uit = request.form.get("thuis_uit", "").strip()
        resultaat = request.form.get("resultaat", "").strip()

        query_db(
            "INSERT INTO wedstrijden (tegenstander, datum, tijd, locatie, thuis_uit, resultaat) "
            "VALUES (?,?,?,?,?,?)",
            (tegenstander, datum, tijd, locatie, thuis_uit, resultaat),
            commit=True,
        )
        return redirect(url_for("wedstrijden_list"))

    return render_template("wedstrijden/wedstrijd_detail.html", wedstrijd=None)


@app.route("/wedstrijden/<int:wedstrijd_id>", methods=["GET", "POST"])
@login_required
def wedstrijden_detail(wedstrijd_id):
    wedstrijd = query_db(
        "SELECT * FROM wedstrijden WHERE id=?", (wedstrijd_id,), one=True
    )
    if not wedstrijd:
        return redirect(url_for("wedstrijden_list"))

    if request.method == "POST" and session.get("role") == "trainer":
        tegenstander = request.form["tegenstander"].strip()
        datum = request.form["datum"].strip()
        tijd = request.form["tijd"].strip()
        locatie = request.form.get("locatie", "").strip()
        thuis_uit = request.form.get("thuis_uit", "").strip()
        resultaat = request.form.get("resultaat", "").strip()

        query_db(
            "UPDATE wedstrijden SET tegenstander=?, datum=?, tijd=?, locatie=?, thuis_uit=?, resultaat=? "
            "WHERE id=?",
            (tegenstander, datum, tijd, locatie, thuis_uit, resultaat, wedstrijd_id),
            commit=True,
        )
        return redirect(url_for("wedstrijden_list"))

    return render_template("wedstrijden/wedstrijd_detail.html", wedstrijd=wedstrijd)


@app.route("/wedstrijden/delete/<int:wedstrijd_id>")
@login_required
def wedstrijden_delete(wedstrijd_id):
    if session.get("role") != "trainer":
        return redirect(url_for("wedstrijden_list"))
    query_db("DELETE FROM wedstrijden WHERE id=?", (wedstrijd_id,), commit=True)
    return redirect(url_for("wedstrijden_list"))

if __name__ == "__main__":
    print("Database wordt gecontroleerd en aangemaakt...")
    create_db.create_database()   # altijd uitvoeren
    print("Database klaar!")
    app.run(debug=True)
