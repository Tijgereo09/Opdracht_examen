from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query_db

# ============================================================================
# AUTHENTICATIE MODULE
# ============================================================================
# Dit bestand beheert:
# - Login voor trainer en spelers
# - Registratie van nieuwe spelers
# - Logout
# - Decorator voor beveiligde routes
# ============================================================================

auth_bp = Blueprint("auth", __name__)


# ----------------------------------------------------------------------------
# DECORATOR: login_required
# ----------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


# ----------------------------------------------------------------------------
# ROUTE: Index naar redirect naar login
# ----------------------------------------------------------------------------
@auth_bp.route("/", endpoint="index")
def index():
    return redirect(url_for("auth.login"))


# ----------------------------------------------------------------------------
# ROUTE: Login
# - Trainer logt in met vast wachtwoord
# - Spelers loggen in via database
# ----------------------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    # Als gebruiker al ingelogd is direct naar dashboard
    if session.get("user"):
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        # --- Trainer login ---
        if username == "trainer" and password == "voetbal123":
            session["user"] = "trainer"
            session["role"] = "trainer"
            return redirect(url_for("dashboard.dashboard"))

        # --- Speler login ---
        speler = query_db(
            "SELECT * FROM spelers WHERE username=? AND wachtwoord=?",
            (username, password),
            one=True,
        )

        if speler:
            session["user"] = speler["username"]
            session["role"] = "speler"
            session["speler_id"] = speler["id"]
            return redirect(url_for("dashboard.dashboard"))

        # Ongeldige login
        flash("Ongeldige gebruikersnaam of wachtwoord.", "error")

    return render_template("login/login.html")


# ----------------------------------------------------------------------------
# ROUTE: Registratie van nieuwe spelers
# ----------------------------------------------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"], endpoint="register")
def register():

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        positie = request.form.get("positie", "").strip()
        rugnummer = request.form.get("rugnummer", "").strip()
        team = request.form.get("team", "").strip()

        # Helper om formulier opnieuw te tonen met ingevulde waarden
        def rerender():
            return render_template(
                "login/register.html",
                username=username,
                positie=positie,
                rugnummer=rugnummer,
                team=team,
            )

        # --- Validatie: rugnummer ---
        if not rugnummer.isdigit() or not (1 <= int(rugnummer) <= 99):
            flash("Rugnummer moet tussen 1 en 99 liggen.", "error")
            return rerender()

        if query_db("SELECT id FROM spelers WHERE rugnummer=?", (rugnummer,), one=True):
            flash("Dit rugnummer is al in gebruik.", "error")
            return rerender()

        # --- Validatie: gebruikersnaam ---
        if query_db("SELECT id FROM spelers WHERE username=?", (username,), one=True):
            flash("Deze gebruikersnaam bestaat al.", "error")
            return rerender()

        if not username or not password:
            flash("Gebruikersnaam en wachtwoord zijn verplicht.", "error")
            return rerender()

        # --- Opslaan in database ---
        query_db(
            "INSERT INTO spelers (username, wachtwoord, positie, rugnummer, team) "
            "VALUES (?,?,?,?,?)",
            (username, password, positie, rugnummer, team),
            commit=True,
        )

        flash("Account succesvol aangemaakt. Je kan nu inloggen.", "success")
        return redirect(url_for("auth.login"))

    return render_template("login/register.html")


# ----------------------------------------------------------------------------
# ROUTE: Logout
# ----------------------------------------------------------------------------
@auth_bp.route("/logout", endpoint="logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
