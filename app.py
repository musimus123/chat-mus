from flask import Flask, render_template, jsonify, request, redirect, session
from flask_socketio import SocketIO, send, emit
import sqlite3
import json

usuarios_conectados = 0

app = Flask(__name__)
app.secret_key = "electronica_bernal_2026"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login_admin", methods=["GET", "POST"])
def login_admin():

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]

        if usuario == "admin" and password == "edwin":

            session["admin"] = True

            return redirect("/admin")

    return render_template("login_admin.html")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login_admin")

@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/login_admin")

    conexion = sqlite3.connect("database/chat.db")

    cursor = conexion.cursor()

    # Total mensajes
    cursor.execute("SELECT COUNT(*) FROM mensajes")
    total_mensajes = cursor.fetchone()[0]

    # Usuarios únicos
    cursor.execute("""
        SELECT COUNT(DISTINCT usuario)
        FROM mensajes
    """)
    usuarios_unicos = cursor.fetchone()[0]

    # Mensajes de hoy
    cursor.execute("""
        SELECT COUNT(*)
        FROM mensajes
        WHERE DATE(fecha)=DATE('now')
    """)
    mensajes_hoy = cursor.fetchone()[0]

    # Últimos mensajes
    cursor.execute("""
        SELECT usuario,mensaje,fecha
        FROM mensajes
        ORDER BY id DESC
        LIMIT 20
    """)

    mensajes = cursor.fetchall()

    conexion.close()

    return render_template(
        "admin.html",
        total_mensajes=total_mensajes,
        usuarios_unicos=usuarios_unicos,
        mensajes_hoy=mensajes_hoy,
        usuarios=usuarios_conectados,
        mensajes=mensajes
    )


@app.route("/historial")
def historial():

    conexion = sqlite3.connect("database/chat.db")

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT usuario,mensaje,fecha
        FROM mensajes
        ORDER BY id DESC
        LIMIT 50
    """)

    datos = cursor.fetchall()

    conexion.close()

    mensajes = []

    for fila in reversed(datos):

        mensajes.append({
            "user": fila[0],
            "text": fila[1],
            "time": fila[2]
        })

    return jsonify(mensajes)


@socketio.on("connect")
def conectado():

    global usuarios_conectados

    usuarios_conectados += 1

    emit(
        "usuarios",
        usuarios_conectados,
        broadcast=True
    )

    print("Usuarios conectados:", usuarios_conectados)


@socketio.on("disconnect")
def desconectado():

    global usuarios_conectados

    if usuarios_conectados > 0:
        usuarios_conectados -= 1

    emit(
        "usuarios",
        usuarios_conectados,
        broadcast=True
    )

    print("Usuarios conectados:", usuarios_conectados)


@socketio.on("message")
def recibir_mensaje(msg):

    try:

        data = json.loads(msg)

        usuario = data["user"]
        mensaje = data["text"]

        conexion = sqlite3.connect("database/chat.db")

        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO mensajes(usuario,mensaje)
            VALUES (?,?)
            """,
            (usuario, mensaje)
        )

        conexion.commit()
        conexion.close()

    except Exception as e:

        print("Error:", e)

    send(msg, broadcast=True)


if __name__ == "__main__":

    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=True
    )