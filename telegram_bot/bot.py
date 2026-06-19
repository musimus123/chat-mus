from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from datetime import datetime
import sqlite3

BOT_APP = None
socketio_ref = None


def configurar_socketio(socketio):
    global socketio_ref
    socketio_ref = socketio


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
🐺 Bienvenido a WolfTrónica

🔧 Servicios:

✔ Lavadoras
✔ Refrigeradores
✔ Microondas
✔ Televisores

Comandos:

/menu
/contacto
"""
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
🔧 MENÚ

1. Lavadoras
2. Refrigeradores
3. Microondas
4. Televisores
"""
    )


async def contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
📞 WolfTrónica

Telegram:
@wlftronica_bot
"""
    )


async def recibir_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):

    usuario = update.effective_user.first_name
    mensaje = update.message.text

    print(f"📱 Telegram -> {usuario}: {mensaje}")

    hora = datetime.now().strftime("%H:%M:%S")

    try:

        conexion = sqlite3.connect("database/chat.db")
        cursor = conexion.cursor()

        cursor.execute(
            """
            INSERT INTO mensajes(usuario,mensaje)
            VALUES (?,?)
            """,
            (f"📱 {usuario}", mensaje)
        )

        conexion.commit()
        conexion.close()

        print("✅ GUARDADO EN BD")

    except Exception as e:

        print("❌ ERROR SQLITE:", e)

    if socketio_ref:

        datos = {
            "user": f"📱 {usuario}",
            "text": mensaje,
            "time": hora
        }

        print("✅ ENVIANDO A WEB Y ADMIN")

    if socketio_ref:

        datos = {
        "user": f"📱 {usuario}",
        "text": mensaje,
        "time": hora
    }

    print("ENVIANDO A WEB Y ADMIN")

    socketio_ref.emit(
    "message",
    datos,
    broadcast=True
)

    socketio_ref.emit(
    "nuevo_mensaje_admin",
    datos,
    broadcast=True
)

def iniciar_bot(token):

    global BOT_APP

    BOT_APP = (
        ApplicationBuilder()
        .token(token)
        .build()
    )

    BOT_APP.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    BOT_APP.add_handler(
        CommandHandler(
            "menu",
            menu
        )
    )

    BOT_APP.add_handler(
        CommandHandler(
            "contacto",
            contacto
        )
    )

    BOT_APP.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            recibir_mensaje
        )
    )

    BOT_APP.run_polling()