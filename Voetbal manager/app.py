from flask import Flask
from datetime import datetime
import create_db

# ============================================================================
# VOETBALMANAGER APPLICATIE - HOOFDBESTAND
# ============================================================================
# Dit bestand bevat de Flask-applicatieconfiguratie en alle blueprints.
# De applicatie ondersteunt trainers en spelers met dashboards, chat, en meer.

# Functie om datumnotatie om te zetten van YYYY-MM-DD naar DD/MM/YYYY
# Dit zorgt ervoor dat datums mooier worden weergegeven in de webpagina's.
def format_date(value):
    if not value:
        return ""
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
        return parsed.strftime("%d/%m/%Y")
    except ValueError:
        return value

# Functie die de Flask-applicatie aanmaakt en configureert
# Deze functie:
# - Maakt de database aan (of controleert deze)
# - Initialiseert Flask met statische bestanden
# - Voegt alle blueprints (functionaliteit modules) toe
# - Stelt het datumfilter in voor templates
def create_app():
    # Zorg ervoor dat de database bestaat met alle benodigde tabellen
    create_db.create_database()
    
    # Maak de Flask-applicatie aan
    # static_folder="style" geeft aan waar CSS-bestanden staan
    app = Flask(__name__, static_folder="style")
    
    # Stel een geheime sleutel in voor sessiebeheer en beveiliging
    app.secret_key = "supersecret_exam_key"
    
    # Registreer het datumfilter zodat templates datums correct formatteren
    app.jinja_env.filters["datetimeformat"] = format_date

    # Importeer alle blueprints (functionaliteitmodules)
    # Dit doen we hier om circulariteit te voorkomen
    from auth import auth_bp              # Login/logout functionaliteit
    from dashboard import dashboard_bp    # Hoofdpagina voor trainer en speler
    from players import players_bp        # Spelerbeheer (trainers)
    from training import training_bp      # Trainingbeheer
    from wedstrijden import wedstrijden_bp  # Wedstrijden en opstelling
    from chat import chat_bp              # Chat functionaliteit

    # Registreer alle blueprints in de Flask-app
    # Dit maakt alle routes beschikbaar
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(players_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(wedstrijden_bp)
    app.register_blueprint(chat_bp)

    return app


# Maak de applicatie aan
app = create_app()

# ============================================================================
# APPLICATIE STARTEN
# ============================================================================
if __name__ == "__main__":
    print("Database wordt gecontroleerd en aangemaakt...")
    # Start de Flask-applicatie in debug-modus
    # debug=True zorgt voor automatisch herladen bij code-wijzigingen
    app.run(debug=True)
