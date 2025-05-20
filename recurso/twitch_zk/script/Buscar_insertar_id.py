import os
import json
import requests
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
CLIENT_ID = os.getenv("TTG_BOT_CLIENT_ID")
TOKEN = os.getenv("TTG_BOT_TOKEN")
# Corregir la ruta del archivo JSON
JSON_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                             'recurso', 'twitch_zk', 'data', 'user_data_twitch.json')

def get_user_info(username, oauth_token):
    """Obtiene información de un usuario de Twitch."""
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {oauth_token}'
    }
    url = f"https://api.twitch.tv/helix/users?login={username}"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data['data']:  # Si hay datos
            return data['data'][0]
        else:
            print(f"Usuario no encontrado: {username}")
            return None
    else:
        print(f"Error al obtener usuario {username}: {response.status_code} - {response.text}")
        return None

def load_user_data():
    """Carga los datos de usuarios desde un archivo JSON."""
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error al cargar el archivo JSON: {e}")
        return {}

def save_user_data(user_data):
    """Guarda los datos de usuarios en un archivo JSON con formato legible."""
    # Reorganizar todos los datos con el orden deseado
    reorganized_data = {}
    for username, user_info in user_data.items():
        reorganized_data[username] = {
            "id": user_info.get("id", ""),
            "follow_date": user_info.get("follow_date", "New"),
            "color": user_info.get("color", "\u001b[97m"),
            "nickname": user_info.get("nickname", "")
        }
    
    with open(JSON_FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(reorganized_data, file, ensure_ascii=False, indent=2)
    return reorganized_data

def main():
    # Cargar datos de usuarios
    user_data = load_user_data()
    if not user_data:
        print("No se pudieron cargar los datos de usuarios.")
        return
    
    print(f"Archivo JSON cargado desde: {JSON_FILE_PATH}")
    
    # Contador para estadísticas
    total_users = len(user_data)
    updated_users = 0
    not_found_users = 0
    
    print(f"Procesando {total_users} usuarios...")
    
    # Procesar cada usuario
    for i, (username, user_info) in enumerate(user_data.items()):
        print(f"[{i+1}/{total_users}] Procesando {username}...", end=" ")
        
        # Verificar si ya tiene ID con valor no vacío
        if user_info.get("id"):
            print(f"Ya tiene ID: {user_info['id']}")
            updated_users += 1
            continue
        
        # Obtener información del usuario
        user_data_from_api = get_user_info(username, TOKEN)
        
        if user_data_from_api:
            # Crear un nuevo diccionario con el orden correcto
            updated_info = {
                "id": user_data_from_api["id"],
                "follow_date": user_info.get("follow_date", "New"),
                "color": user_info.get("color", "\u001b[97m"),
                "nickname": user_info.get("nickname", "")
            }
            # Actualizar con el nuevo diccionario ordenado
            user_data[username] = updated_info
            print(f"ID obtenido: {updated_info['id']}")
            updated_users += 1
        else:
            # Si no se encuentra, asignar un ID vacío pero mantener el orden
            user_data[username] = {
                "id": "",
                "follow_date": user_info.get("follow_date", "New"),
                "color": user_info.get("color", "\u001b[97m"),
                "nickname": user_info.get("nickname", "")
            }
            print("No se encontró en Twitch")
            not_found_users += 1
        
        # Guardar periódicamente y pausa para no exceder los límites de la API
        if (i + 1) % 10 == 0:
            print(f"Guardando datos después de {i + 1} usuarios...")
            user_data = save_user_data(user_data)
        
        # Pausa entre solicitudes para no exceder límites de la API
        time.sleep(0.5)
    
    # Guardar cambios finales asegurando el orden correcto
    save_user_data(user_data)
    
    print(f"\nProceso completado:")
    print(f"- Total de usuarios: {total_users}")
    print(f"- Usuarios actualizados: {updated_users}")
    print(f"- Usuarios no encontrados: {not_found_users}")

if __name__ == "__main__":
    main()