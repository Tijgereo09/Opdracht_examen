from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query_db
from auth import login_required

chat_bp = Blueprint("chat", __name__)

# ============================================================================
# HELPER: Naam van afzender bepalen
# ============================================================================
def get_sender_name():
    return "Trainer" if session.get("role") == "trainer" else session.get("user")


# ============================================================================
# GLOBALE CHAT (iedereen ziet alles)
# ============================================================================
@chat_bp.route("/chat", methods=["GET", "POST"], endpoint="chat_global")
@login_required
def chat_global():

    # Markeer globale berichten als gelezen
    query_db("UPDATE messages SET seen=1 WHERE recipient_id=-1", commit=True)

    if request.method == "POST":
        content = request.form.get("content", "").strip()

        # Globale chat gebruikt recipient_id = -1
        query_db(
            """
            INSERT INTO messages (sender_id, sender_name, sender_role, recipient_id, content)
            VALUES (?,?,?,?,?)
            """,
            (
                session.get("speler_id") if session.get("role") == "speler" else 0,
                get_sender_name(),
                session.get("role"),
                -1,
                content,
            ),
            commit=True,
        )

        return redirect(url_for("chat.chat_global"))

    messages = query_db(
        "SELECT * FROM messages WHERE recipient_id=-1 ORDER BY created_at ASC"
    )

    return render_template("chat/chat.html", messages=messages, form_visible=True)


# ============================================================================
# PRIVÉCHAT: speler → trainer (1-op-1)
# ============================================================================
@chat_bp.route("/chat/trainer", methods=["GET", "POST"], endpoint="chat_trainer")
@login_required
def chat_trainer():

    # Alleen spelers mogen deze chat openen
    if session.get("role") != "speler":
        flash("Alleen spelers kunnen privé met de trainer chatten.", "error")
        return redirect(url_for("chat.chat_global"))

    speler_id = session.get("speler_id")

    # Markeer berichten als gelezen
    query_db(
        "UPDATE messages SET seen=1 WHERE recipient_id=?",
        (0,),
        commit=True
    )

    if request.method == "POST":
        content = request.form.get("content", "").strip()

        query_db(
            """
            INSERT INTO messages (sender_id, sender_name, sender_role, recipient_id, content)
            VALUES (?,?,?,?,?)
            """,
            (speler_id, session.get("user"), "speler", 0, content),
            commit=True
        )

        return redirect(url_for("chat.chat_trainer"))

    # Haal ALLE berichten op tussen speler ↔ trainer
    messages = query_db(
        """
        SELECT * FROM messages
        WHERE (sender_id=? AND recipient_id=0)
           OR (sender_id=0 AND recipient_id=?)
        ORDER BY created_at ASC
        """,
        (speler_id, speler_id)
    )

    return render_template("chat/chat.html", messages=messages, form_visible=True)


# ============================================================================
# PRIVÉCHAT: trainer → speler (1-op-1)
# ============================================================================
@chat_bp.route("/chat/player/<int:speler_id>", methods=["GET", "POST"], endpoint="chat_player")
@login_required
def chat_player(speler_id):

    # Alleen trainer mag deze chat openen
    if session.get("role") != "trainer":
        flash("Alleen trainers kunnen deze chat openen.", "error")
        return redirect(url_for("chat.chat_global"))

    # Markeer berichten als gelezen
    query_db(
        "UPDATE messages SET seen=1 WHERE recipient_id=?",
        (speler_id,),
        commit=True
    )

    if request.method == "POST":
        content = request.form.get("content", "").strip()

        query_db(
            """
            INSERT INTO messages (sender_id, sender_name, sender_role, recipient_id, content)
            VALUES (?,?,?,?,?)
            """,
            (0, "Trainer", "trainer", speler_id, content),
            commit=True
        )

        return redirect(url_for("chat.chat_player", speler_id=speler_id))

    # Haal ALLE berichten op tussen trainer ↔ speler
    messages = query_db(
        """
        SELECT * FROM messages
        WHERE (sender_id=? AND recipient_id=0)
           OR (sender_id=0 AND recipient_id=?)
        ORDER BY created_at ASC
        """,
        (speler_id, speler_id)
    )

    return render_template("chat/chat.html", messages=messages, form_visible=True)


# ============================================================================
# BERICHT VERWIJDEREN (alleen trainer)
# ============================================================================
@chat_bp.route("/chat/delete/<int:message_id>", endpoint="chat_delete")
@login_required
def chat_delete(message_id):

    if session.get("role") != "trainer":
        flash("Alleen trainers mogen berichten verwijderen.", "error")
        return redirect(url_for("chat.chat_global"))

    query_db("DELETE FROM messages WHERE id=?", (message_id,), commit=True)
    flash("Bericht verwijderd.", "success")

    return redirect(request.referrer or url_for("chat.chat_global"))
