import sqlite3

conexion = sqlite3.connect("database/chat.db")

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS mensajes(
id INTEGER PRIMARY KEY AUTOINCREMENT,
usuario TEXT NOT NULL,
mensaje TEXT NOT NULL,
fecha DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conexion.commit()
conexion.close()

print("Base de datos creada correctamente")
