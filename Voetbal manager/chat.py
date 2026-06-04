from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query_db
from auth import login_required

# ============================================================================
# CHATFUNCTIONALITEIT
# ============================================================================
# Dit bestand bevat alle chat-functies:
# - Globale chat: iedereen kan berichten lezen en schrijven
# - Privéberichten: spelers kunnen priv\u00e9 met trainer chatten

chat_bp = Blueprint("chat", __name__)

# HULPFUNCTIE: get_sender_name()
# Bepaalt de naam van de bericht-afzender op basis van sessie
# Return: "Trainer" of speler-username
def get_sender_name():
    if session.get("role") == "trainer":
        return "Trainer"
    return session.get("user", "Onbekend")

# ROUTE: Globale chat
# GET: Toont alle globale berichten
# POST: Voegt nieuw bericht toe aan globale chat
@chat_bp.route("/chat", methods=["GET", "POST"], endpoint="chat_global")
@login_required
def chat_global():
    if request.method == "POST":
        # Haal bericht inhoud op
        content = request.form.get("content", "").strip()
        
        # Validatie: controleer dat het bericht niet leeg is
        if not content:
            flash("Vul eerst een bericht in voordat je het verstuurt.", "error")
        else:
            # ---- OPSLAAN: Sla bericht op in database ----
            # Recipient_role="all" betekent dat het bericht voor iedereen is
            query_db(
                "INSERT INTO messages (sender_id, sender_name, sender_role, recipient_role, content) VALUES (?,?,?,?,?)",
                (session.get("speler_id") if session.get("role") == "speler" else None,
                 get_sender_name(), session.get("role"), "all", content),
                commit=True,
            )
            return redirect(url_for("chat.chat_global"))

    # Haal alle globale berichten op, sorteer op tijd (oudste eerst)
    messages = query_db(
        "SELECT * FROM messages WHERE recipient_role = ? ORDER BY created_at ASC",
        ("all",),
    )
    
    # Toon globale chat
    return render_template(
        "chat/chat.html",
        title="Globale chat",
        heading="Globale chat",
        messages=messages,
        form_action=url_for("chat.chat_global"),
        form_visible=True,
        other_url=url_for("chat.chat_trainer"),
        other_label="Privé-chat met trainer",
        empty_label="Er zijn nog geen berichten in de globale chat.",
        thread_mode=False,
    )

# ROUTE: Privé-chat met trainer
# Spelers kunnen privéberichten naar trainer sturen
# Trainers kunnen berichten van alle spelers zien en erop antwoorden
@chat_bp.route("/chat/trainer", methods=["GET", "POST"], endpoint="chat_trainer")
@login_required
def chat_trainer():
    # ============================================================
    # SPELER: Privé-chat met trainer
    # ============================================================
    if session.get("role") == "speler":
        player_id = session.get("speler_id")
        
        if request.method == "POST":
            # Haal bericht inhoud op
            content = request.form.get("content", "").strip()
            
            # Validatie
            if not content:
                flash("Vul eerst een bericht in voordat je het verstuurt.", "error")
            else:
                # ---- OPSLAAN: Sla privébericht op ----
                # recipient_role="trainer" betekent dat dit een privébericht is
                query_db(
                    "INSERT INTO messages (sender_id, sender_name, sender_role, recipient_role, recipient_id, content) VALUES (?,?,?,?,?,?)",
                    (player_id, get_sender_name(), session.get("role"), "trainer", None, content),
                    commit=True,
                )
                return redirect(url_for("chat.chat_trainer"))

        # Haal alle berichten op tussen deze speler en trainer
        messages = query_db(
            "SELECT * FROM messages WHERE "
            "(sender_id = ? AND recipient_role = 'trainer') "
            "OR (recipient_role = 'player' AND recipient_id = ?) "
            "ORDER BY created_at ASC",
            (player_id, player_id),
        )
        
        # Toon speler privéberichten view
        return render_template(
            "chat/chat.html",
            title="Privé-chat met trainer",
            heading="Privé-chat met trainer",
            messages=messages,
            form_action=url_for("chat.chat_trainer"),
            form_visible=True,
            other_url=url_for("chat.chat_global"),
            other_label="Terug naar globale chat",
            empty_label="Je hebt nog geen privéberichten met de trainer.",
            thread_mode=True,
        )

    # ============================================================
    # TRAINER: Privé-chat met spelers
    # ============================================================
    # Haal alle spelers op
    players = query_db("SELECT id, username FROM spelers ORDER BY username")
    
    # Check welke speler geselecteerd is uit het menu
    selected_player_id = request.args.get("player_id", type=int)
    selected_player = None
    messages = []
    
    if selected_player_id:
        # Zoek de geselecteerde speler
        selected_player = query_db(
            "SELECT id, username FROM spelers WHERE id = ?",
            (selected_player_id,),
            one=True,
        )
        
        if selected_player:
            # Haal berichten op van deze speler
            messages = query_db(
                "SELECT * FROM messages WHERE "
                "(sender_id = ? AND recipient_role = 'trainer') "
                "OR (recipient_role = 'player' AND recipient_id = ?) "
                "ORDER BY created_at ASC",
                (selected_player_id, selected_player_id),
            )
    
    if request.method == "POST" and selected_player_id:
        # Haal bericht inhoud op
        content = request.form.get("content", "").strip()
        
        # Validatie
        if not content:
            flash("Vul eerst een bericht in voordat je het verstuurt.", "error")
        else:
            # ---- OPSLAAN: Sla trainer-antwoord op ----
            query_db(
                "INSERT INTO messages (sender_name, sender_role, recipient_role, recipient_id, content) VALUES (?,?,?,?,?)",
                (get_sender_name(), session.get("role"), "player", selected_player_id, content),
                commit=True,
            )
            return redirect(url_for("chat.chat_trainer", player_id=selected_player_id))

    # Toon trainer privéberichten view (met speler-selectie)
    return render_template(
        "chat/chat.html",
        title="Privé-chat met speler",
        heading="Privé-chat met speler",
        messages=messages,
        form_action=url_for("chat.chat_trainer", player_id=selected_player_id) if selected_player_id else url_for("chat.chat_trainer"),
        form_visible=selected_player_id is not None,
        other_url=url_for("chat.chat_global"),
        other_label="Terug naar globale chat",
        empty_label="Selecteer eerst een speler om met hem te chatten.",
        players=players,
        selected_player=selected_player,
        thread_mode=True,
    )
