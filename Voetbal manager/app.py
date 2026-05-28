from flask import Flask
from datetime import datetime
import create_db

# Formatteert datumwaarden van YYYY-MM-DD naar DD/MM/YYYY voor gebruik in templates.
def format_date(value):
    if not value:
        return ""
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
        return parsed.strftime("%d/%m/%Y")
    except ValueError:
        return value

# Bouwt en configureert de Flask-applicatie met alle blueprints.
def create_app():
    # Zorg dat de database en benodigde tabellen aanwezig zijn.
    create_db.create_database()
    app = Flask(__name__, static_folder="style")
    app.secret_key = "supersecret_exam_key"
    app.jinja_env.filters["datetimeformat"] = format_date

    # Importeer blueprints nadat de app is aangemaakt om importloops te voorkomen.
    from auth import auth_bp
    from dashboard import dashboard_bp
    from players import players_bp
    from training import training_bp
    from wedstrijden import wedstrijden_bp
    from chat import chat_bp

    # Registreer alle routes in de applicatie.
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(players_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(wedstrijden_bp)
    app.register_blueprint(chat_bp)

    return app


app = create_app()


if __name__ == "__main__":
    print("Database wordt gecontroleerd en aangemaakt...")
    app.run(debug=True)
