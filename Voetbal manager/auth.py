from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query_db

# ============================================================================
# AUTHENTIFICATIE EN ACCOUNTBEHEER
# ============================================================================
# Dit bestand verzorgt:
# - Login/logout voor trainers en spelers
# - Registratie van nieuwe spelers
# - Sessie beheer en verificatie

auth_bp = Blueprint("auth", __name__)

# DECORATOR: login_required
# Deze decorator beschermt routes zodat alleen ingelogde gebruikers deze kunnen bezoeken.
# Als je niet ingelogd bent, word je naar de login-pagina gestuurd.
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Controleer of er een gebruiker in de sessie staat
        if "user" not in session:
            # Geen gebruiker -> stuur naar login-pagina
            return redirect(url_for("auth.login"))
        # Gebruiker is ingelogd -> voer de beveiligde functie uit
        return f(*args, **kwargs)

    return wrapper

# ROUTE: Homepagina
# De standaard pagina "/" dirigeert alle bezoekers naar de login-pagina
@auth_bp.route("/", endpoint="index")
def index():
    return redirect(url_for("auth.login"))

# ROUTE: Login-pagina
# GET: Toont het login-formulier
# POST: Verwerkt inlogpoging (controleert gebruikersnaam en wachtwoord)
@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    # Als je al ingelogd bent, ga naar het dashboard
    if session.get("user"):
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        # Haal inloggegevens uit het formulier en verwijder spaties
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        # ---- TRAINER LOGIN ----
        # Het trainer-account heeft een vast wachtwoord
        if username == "trainer" and password == "voetbal123":
            # Sla trainer-info in de sessie op
            session["user"] = "trainer"
            session["role"] = "trainer"  # Rol bepaalt wat de trainer kan doen
            return redirect(url_for("dashboard.dashboard"))

        # ---- SPELER LOGIN ----
        # Zoek de speler in de database met gegeven gebruikersnaam en wachtwoord
        speler = query_db(
            "SELECT * FROM spelers WHERE username=? AND password=?",
            (username, password),
            one=True,
        )
        if speler:
            # Speler gevonden! Sla zijn gegevens in de sessie op
            session["user"] = speler["username"]
            session["role"] = "speler"  # Deze speler heeft rol 'speler'
            session["speler_id"] = speler["id"]  # Onthoud speler-ID voor latere queries

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
