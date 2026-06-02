from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query_db
from auth import login_required

# Chatfunctionaliteit voor globale en privéberichten.
chat_bp = Blueprint("chat", __name__)

# Haal de afzendernaam op uit de sessie.
def get_sender_name():
    if session.get("role") == "trainer":
        return "Trainer"
    return session.get("user", "Onbekend")

# Globale chat waar iedereen berichten kan lezen en plaatsen.
@chat_bp.route("/chat", methods=["GET", "POST"], endpoint="chat_global")
@login_required
def chat_global():
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if not content:
            flash("Vul eerst een bericht in voordat je het verstuurt.", "error")
        else:
            query_db(
                "INSERT INTO messages (sender_id, sender_name, sender_role, recipient_role, content) VALUES (?,?,?,?,?)",
                (session.get("speler_id") if session.get("role") == "speler" else None,
                 get_sender_name(), session.get("role"), "all", content),
                commit=True,
            )
            return redirect(url_for("chat.chat_global"))

    messages = query_db(
        "SELECT * FROM messages WHERE recipient_role = ? ORDER BY created_at ASC",
        ("all",),
    )
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

# Privéchat voor berichten naar de trainer.
@chat_bp.route("/chat/trainer", methods=["GET", "POST"], endpoint="chat_trainer")
@login_required
def chat_trainer():
    if session.get("role") == "speler":
        player_id = session.get("speler_id")
        if request.method == "POST":
            content = request.form.get("content", "").strip()
            if not content:
                flash("Vul eerst een bericht in voordat je het verstuurt.", "error")
            else:
                query_db(
                    "INSERT INTO messages (sender_id, sender_name, sender_role, recipient_role, recipient_id, content) VALUES (?,?,?,?,?,?)",
                    (player_id, get_sender_name(), session.get("role"), "trainer", None, content),
                    commit=True,
                )
                return redirect(url_for("chat.chat_trainer"))

        messages = query_db(
            "SELECT * FROM messages WHERE "
            "(sender_id = ? AND recipient_role = 'trainer') "
            "OR (recipient_role = 'player' AND recipient_id = ?) "
            "ORDER BY created_at ASC",
            (player_id, player_id),
        )
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

    # Trainer route: kies een speler om een een-op-een chat te tonen.
    players = query_db("SELECT id, username FROM spelers ORDER BY username")
    selected_player_id = request.args.get("player_id", type=int)
    selected_player = None
    messages = []
    if selected_player_id:
        selected_player = query_db(
            "SELECT id, username FROM spelers WHERE id = ?",
            (selected_player_id,),
            one=True,
        )
        if selected_player:
            messages = query_db(
                "SELECT * FROM messages WHERE "
                "(sender_id = ? AND recipient_role = 'trainer') "
                "OR (recipient_role = 'player' AND recipient_id = ?) "
                "ORDER BY created_at ASC",
                (selected_player_id, selected_player_id),
            )
    if request.method == "POST" and selected_player_id:
        content = request.form.get("content", "").strip()
        if not content:
            flash("Vul eerst een bericht in voordat je het verstuurt.", "error")
        else:
            query_db(
                "INSERT INTO messages (sender_name, sender_role, recipient_role, recipient_id, content) VALUES (?,?,?,?,?)",
                (get_sender_name(), session.get("role"), "player", selected_player_id, content),
                commit=True,
            )
            return redirect(url_for("chat.chat_trainer", player_id=selected_player_id))

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
