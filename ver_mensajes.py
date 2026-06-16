import sqlite3

conexion = sqlite3.connect("database/chat.db")

cursor = conexion.cursor()

cursor.execute("SELECT * FROM mensajes")

datos = cursor.fetchall()

for fila in datos:
    print(fila)

conexion.close()