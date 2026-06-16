from flask import Flask, render_template
from flask_socketio import SocketIO, send
import sqlite3
import json

app = Flask(__name__)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

@app.route("/")
def index():
    return render_template("index.html")

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