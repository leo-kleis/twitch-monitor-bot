import sqlite3
import os

# Ruta para la base de datos
db_path = os.path.join('bd/data', 'zkleisbotv_twitch.db')

# Asegurar que el directorio existe
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Conectar a la base de datos (se creara si no existe)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Crear la tabla usuarios
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id_user TEXT PRIMARY KEY,
    user_name TEXT UNIQUE NOT NULL,
    nickname TEXT,
    follow_date TEXT,
    color TEXT
);
''')

# Guardar cambios y cerrar conexion
conn.commit()
conn.close()

print(f"Base de datos y tabla creadas correctamente en: {db_path}")