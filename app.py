from flask import Flask, render_template, jsonify, request, redirect, session
from flask_socketio import SocketIO, send, emit

import os
import sqlite3
import json
import asyncio

from threading import Thread

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from flask import send_file
from datetime import datetime

from telegram_bot.bot import (
    iniciar_bot,
    configurar_socketio
)

import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

usuarios_conectados = 0
usuarios_socket = {}
nombres_activos = []

app = Flask(__name__)
app.secret_key = "electronica_bernal_2026"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

configurar_socketio(socketio)

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

    cursor.execute("SELECT COUNT(*) FROM mensajes")
    total_mensajes = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT usuario)
        FROM mensajes
    """)
    usuarios_unicos = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM mensajes
        WHERE DATE(fecha)=DATE('now')
    """)
    mensajes_hoy = cursor.fetchone()[0]

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

@app.route("/pdf")
def exportar_pdf():

    conexion = sqlite3.connect("database/chat.db")
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT usuario,mensaje,fecha
        FROM mensajes
        ORDER BY id DESC
    """)

    datos = cursor.fetchall()

    conexion.close()

    archivo = "mensajes.pdf"

    doc = SimpleDocTemplate(archivo)

    estilos = getSampleStyleSheet()

    contenido = []

    contenido.append(
        Paragraph(
            "Historial de Mensajes WolfTrónica",
            estilos["Title"]
        )
    )

    contenido.append(
        Spacer(1,12)
    )

    for fila in datos:

        contenido.append(
            Paragraph(
                f"<b>{fila[0]}</b>: {fila[1]} ({fila[2]})",
                estilos["BodyText"]
            )
        )

    doc.build(contenido)

    return send_file(
        archivo,
        as_attachment=True
    )


# =====================================
# SOCKET EVENTS
# =====================================

@socketio.on("connect")
def conectado():

    global usuarios_conectados

    usuarios_conectados += 1

    socketio.emit(
        "usuarios",
        usuarios_conectados
    )

    print("Usuarios conectados:", usuarios_conectados)


@socketio.on("disconnect")
def desconectado():

    global usuarios_conectados
    global nombres_activos

    nombre = usuarios_socket.get(request.sid)

    if nombre:

        print("SALIÓ:", nombre)

        if nombre in nombres_activos:
            nombres_activos.remove(nombre)

        socketio.emit(
            "mensaje_sistema",
            f"🔴 {nombre} salió del chat"
        )

        usuarios_socket.pop(
            request.sid,
            None
        )

    if usuarios_conectados > 0:
        usuarios_conectados -= 1

    socketio.emit(
        "usuarios",
        usuarios_conectados
    )

    print(
        "Usuarios conectados:",
        usuarios_conectados
    )

@socketio.on("usuario_conectado")
def usuario_conectado(nombre):

    global nombres_activos

    if nombre in nombres_activos:

        emit("nombre_ocupado")

        return

    nombres_activos.append(nombre)

    usuarios_socket[request.sid] = nombre

    print("ENTRÓ:", nombre)

    socketio.emit(
        "mensaje_sistema",
        f"🟢 {nombre} se conectó"
    )


@socketio.on("escribiendo")
def escribiendo(nombre):

    print(nombre + " está escribiendo")

    socketio.emit(
        "mostrar_escribiendo",
        nombre,
        include_self=False
    )

@socketio.on("message")
def recibir_mensaje(msg):

    try:

        # WEB
        if isinstance(msg, str):

            data = json.loads(msg)

        # TELEGRAM
        else:

            data = msg

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

        datos = {
            "user": usuario,
            "text": mensaje,
            "time": datetime.now().strftime("%H:%M:%S")
        }

        socketio.emit(
            "message",
            datos
        )

        socketio.emit(
            "nuevo_mensaje_admin",
            datos
        )

    except Exception as e:

        print("ERROR MESSAGE:", e)

import asyncio

def iniciar_telegram():

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    iniciar_bot(
        TELEGRAM_TOKEN
    )

if __name__ == "__main__":

    telegram_thread = Thread(
        target=iniciar_telegram,
        daemon=True
    )

    telegram_thread.start()

    socketio.run(
    app,
    host="0.0.0.0",
    port=5000,
    debug=False,
    allow_unsafe_werkzeug=True
)
