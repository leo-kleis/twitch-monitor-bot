import sqlite3
import json
import os

# Rutas
json_path = os.path.join('recurso/twitch_zk/data', 'user_data_twitch.json')
db_path = os.path.join('bd/data', 'zkleisbotv_twitch.db')

# Cargar datos del JSON
with open(json_path, 'r', encoding='utf-8') as file:
    user_data = json.load(file)

# Conectar a la base de datos
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Insertar datos en la tabla
inserted_count = 0
skipped_count = 0
no_id_count = 0

for user_name, data in user_data.items():
    try:
        # Extraer datos
        id_user = data.get('id', '')
        nickname = data.get('nickname', '')
        follow_date = data.get('follow_date', '')
        color = data.get('color', '')
        
        # Si el ID esta vacio, saltamos este usuario
        if not id_user:
            print(f"Saltando usuario {user_name} porque no tiene ID")
            no_id_count += 1
            continue
        
        # Insertar en la base de datos solo si tiene ID
        cursor.execute('''
            INSERT OR REPLACE INTO Usuarios (id_user, user_name, nickname, follow_date, color)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_user, user_name, nickname, follow_date, color))
        
        inserted_count += 1
        
    except Exception as e:
        print(f"Error al insertar usuario {user_name}: {e}")
        skipped_count += 1

# Guardar cambios
conn.commit()

# Verificar la migracion
cursor.execute("SELECT COUNT(*) FROM Usuarios")
total_users = cursor.fetchone()[0]

# Cerrar conexion
conn.close()

print(f"Migracion completada:")
print(f"- Usuarios insertados: {inserted_count}")
print(f"- Usuarios sin ID (omitidos): {no_id_count}")
print(f"- Usuarios con error (omitidos): {skipped_count}")
print(f"- Total en base de datos: {total_users}")