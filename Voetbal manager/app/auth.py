from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .db import query_db

auth_bp = Blueprint("auth", __name__)

# Decorator om routes te beschermen zodat alleen ingelogde gebruikers toegang krijgen.
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return wrapper

# Standaard homepagina: redirect naar login.
@auth_bp.route("/", endpoint="index")
def index():
    return redirect(url_for("auth.login"))

# Login-pagina: toont formulier bij GET en verwerkt inloggegevens bij POST.
@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if session.get("user"):
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        # Traineraccount met vast wachtwoord.
        if username == "trainer" and password == "voetbal123":
            session["user"] = "trainer"
            session["role"] = "trainer"
            return redirect(url_for("dashboard.dashboard"))

        # Speleraccount ophalen uit de database.
        speler = query_db(
            "SELECT * FROM spelers WHERE username=? AND password=?",
            (username, password),
            one=True,
        )
        if speler:
            session["user"] = speler["username"]
            session["role"] = "speler"
            session["speler_id"] = speler["id"]

            # Toon meldingen voor actuele wedstrijden van de speler.
            wedstrijden = query_db(
                "SELECT w.tegenstander, w.datum, w.tijd, ws.positie, ws.bank "
                "FROM wedstrijden w "
                "JOIN wedstrijd_spelers ws ON w.id = ws.wedstrijd_id "
                "WHERE ws.speler_id = ? "
                "ORDER BY w.datum, w.tijd",
                (speler["id"],),
            )
            for wedstrijd in wedstrijden:
                position_label = wedstrijd["positie"].replace("_", " ").title() if wedstrijd["positie"] else ""
                if wedstrijd["bank"] == 1:
                    if position_label:
                        flash(
                            f"Je staat op de bank als {position_label} voor de wedstrijd tegen {wedstrijd['tegenstander']} op {wedstrijd['datum']} om {wedstrijd['tijd']}",
                            "success",
                        )
                    else:
                        flash(
                            f"Je staat op de bank voor de wedstrijd tegen {wedstrijd['tegenstander']} op {wedstrijd['datum']} om {wedstrijd['tijd']}",
                            "success",
                        )
                else:
                    if position_label:
                        flash(
                            f"Je bent geselecteerd als {position_label} voor de wedstrijd tegen {wedstrijd['tegenstander']} op {wedstrijd['datum']} om {wedstrijd['tijd']}",
                            "success",
                        )
                    else:
                        flash(
                            f"Je bent geselecteerd voor de wedstrijd tegen {wedstrijd['tegenstander']} op {wedstrijd['datum']} om {wedstrijd['tijd']}",
                            "success",
                        )

            return redirect(url_for("dashboard.dashboard"))

        flash("Ongeldige login.", "error")

    return render_template("login/login.html")

# Registratiepagina: controleert invoer en maakt een nieuwe speler aan.
@auth_bp.route("/register", methods=["GET", "POST"], endpoint="register")
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        positie = request.form.get("positie", "").strip()
        rugnummer = request.form.get("rugnummer", "").strip()
        team = request.form.get("team", "").strip()

        if not rugnummer.isdigit() or int(rugnummer) < 1 or int(rugnummer) > 99:
            flash("Rugnummer moet tussen 1 en 99 liggen.", "error")
            return redirect(url_for("auth.register"))

        existing_rugnummer = query_db(
            "SELECT id FROM spelers WHERE rugnummer=?",
            (rugnummer,),
            one=True,
        )
        if existing_rugnummer:
            flash("Dit rugnummer is al in gebruik.", "error")
            return redirect(url_for("auth.register"))

        existing_username = query_db(
            "SELECT id FROM spelers WHERE username=?",
            (username,),
            one=True,
        )
        if existing_username:
            flash("Deze gebruikersnaam bestaat al.", "error")
            return redirect(url_for("auth.register"))

        if not username or not password:
            flash("Gebruikersnaam en wachtwoord zijn verplicht.", "error")
            return redirect(url_for("auth.register"))

        try:
            query_db(
                "INSERT INTO spelers (username, password, positie, rugnummer, team) "
                "VALUES (?,?,?,?,?)",
                (username, password, positie, rugnummer, team),
                commit=True,
            )
        except Exception:
            flash("Er ging iets mis bij het aanmaken van je account.", "error")
            return redirect(url_for("auth.register"))

        flash("Account aangemaakt, je kan nu inloggen.", "success")
        return redirect(url_for("auth.login"))

    return render_template("login/register.html")

# Logt de gebruiker uit door de sessie leeg te maken.
@auth_bp.route("/logout", endpoint="logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
