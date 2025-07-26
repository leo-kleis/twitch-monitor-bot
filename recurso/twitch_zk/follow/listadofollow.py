import os
import requests
import csv
import glob
from tqdm import tqdm
from datetime import datetime
from dotenv import load_dotenv

def main():
    if os.environ.get('ENVIRONMENT') != 'production':
        load_dotenv()

    def get_followers(token, user_id, client_id):
        followers = []
        url = f'https://api.twitch.tv/helix/channels/followers?broadcaster_id={user_id}'
        headers = {
            'Client-ID': client_id,
            'Authorization': f'Bearer {token}'
        }

        response = requests.get(url, headers=headers)
        print(response)
        response.raise_for_status()
        data = response.json()

        total_followers = data['total']

        with tqdm(total=total_followers) as pbar:
            while url:
                # Guardamos user_id, user_name y followed_at (cambiado el orden)
                new_followers = [(follower['user_id'], follower['user_name'], follower['followed_at']) for follower in data['data']]
                followers.extend(new_followers)
                pbar.update(len(new_followers))
                cursor = data['pagination'].get('cursor')
                if cursor:
                    url = f'https://api.twitch.tv/helix/channels/followers?broadcaster_id={user_id}&after={cursor}'
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                else:
                    break

        total_followers = len(followers)
        # Reorganizado: ahora tenemos rank, user_id, username, fecha
        followers = [(total_followers - i, user_id, name, datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ').strftime('%d/%m/%y')) 
                    for i, (user_id, name, date) in enumerate(followers)]

        return followers

    user_id = os.getenv('BROADCASTER_ID')
    client_id = os.getenv('TTG_BOT_CLIENT_ID')
    token = os.getenv('TTG_BOT_TOKEN')

    followers = get_followers(token, user_id, client_id)
    date = datetime.now().strftime('%y-%m-%d')
    year = datetime.now().strftime('%Y')
    folder_path = os.path.join('recurso/twitch_zk/follow/follow', year)
    filename = f'[{date}] Followers.csv'
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    counter = 1
    full_path = os.path.join(folder_path, filename)
    while os.path.isfile(full_path):
        filename = f'[{date}] ({counter}) Followers.csv'
        full_path = os.path.join(folder_path, filename)
        counter += 1

    with open(full_path, 'w', newline='') as file:
        writer = csv.writer(file)
        # Modificado el orden de las columnas segun lo solicitado
        writer.writerow(["#", "User ID", "Username", "Followed At"])
        for follower in followers:
            writer.writerow(follower)  # Ya no necesitamos ajustar nada, el orden ya esta correcto
    
    print(f"Archivo generado: {full_path}")
    
    # Realizar comparación con el archivo anterior
    comparar_con_archivo_anterior(full_path, folder_path)

def leer_csv_seguidores(archivo_path):
    """Lee un archivo CSV de seguidores y retorna un diccionario con user_id como clave"""
    seguidores = {}
    try:
        with open(archivo_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Saltar header
            for row in reader:
                if len(row) >= 4:
                    rank, user_id, username, followed_at = row
                    seguidores[user_id] = {
                        'rank': rank,
                        'username': username,
                        'followed_at': followed_at
                    }
    except Exception as e:
        print(f"Error al leer archivo {archivo_path}: {e}")
    return seguidores

def obtener_archivo_anterior(archivo_actual, folder_path):
    """Encuentra el archivo CSV anterior al actual"""
    # Obtener todos los archivos CSV del directorio ordenados por fecha de modificación
    patron = os.path.join(folder_path, "*Followers.csv")
    archivos = glob.glob(patron)
    
    if len(archivos) < 2:
        return None
    
    # Ordenar por fecha de modificación (más reciente primero)
    archivos.sort(key=os.path.getmtime, reverse=True)
    
    # El archivo actual debe ser el primero, el anterior el segundo
    archivo_actual_nombre = os.path.basename(archivo_actual)
    
    for i, archivo in enumerate(archivos):
        if os.path.basename(archivo) == archivo_actual_nombre and i + 1 < len(archivos):
            return archivos[i + 1]
    
    # Si no encontramos el actual en la posición 0, el segundo archivo es el anterior
    return archivos[1] if len(archivos) > 1 else None

def comparar_con_archivo_anterior(archivo_actual, folder_path):
    """Compara el archivo actual con el anterior y muestra las diferencias"""
    archivo_anterior = obtener_archivo_anterior(archivo_actual, folder_path)
    
    if not archivo_anterior:
        print("\n=== ANALISIS DE SEGUIDORES ===")
        print("No hay archivo anterior para comparar.")
        return
    
    print(f"\n=== ANALISIS DE SEGUIDORES ===")
    print(f"Archivo anterior: {os.path.basename(archivo_anterior)}")
    print(f"Archivo actual: {os.path.basename(archivo_actual)}")
    
    seguidores_anteriores = leer_csv_seguidores(archivo_anterior)
    seguidores_actuales = leer_csv_seguidores(archivo_actual)
    
    # Encontrar nuevos seguidores
    nuevos_seguidores = []
    for user_id, datos in seguidores_actuales.items():
        if user_id not in seguidores_anteriores:
            nuevos_seguidores.append((user_id, datos))
    
    # Encontrar seguidores que se fueron
    seguidores_perdidos = []
    for user_id, datos in seguidores_anteriores.items():
        if user_id not in seguidores_actuales:
            seguidores_perdidos.append((user_id, datos))
    
    # Mostrar resultados
    print(f"\n--- RESUMEN ---")
    print(f"Seguidores anteriores: {len(seguidores_anteriores)}")
    print(f"Seguidores actuales: {len(seguidores_actuales)}")
    print(f"Cambio neto: {len(seguidores_actuales) - len(seguidores_anteriores):+d}")
    
    if nuevos_seguidores:
        print(f"\n+ NUEVOS SEGUIDORES ({len(nuevos_seguidores)}):")
        for user_id, datos in sorted(nuevos_seguidores, key=lambda x: int(x[1]['rank'])):
            print(f"  #{datos['rank']} - {datos['username']} (ID: {user_id}) - {datos['followed_at']}")
    
    if seguidores_perdidos:
        print(f"\n- SEGUIDORES PERDIDOS ({len(seguidores_perdidos)}):")
        for user_id, datos in sorted(seguidores_perdidos, key=lambda x: int(x[1]['rank'])):
            print(f"  #{datos['rank']} - {datos['username']} (ID: {user_id}) - {datos['followed_at']}")
    
    if not nuevos_seguidores and not seguidores_perdidos:
        print("\nNo hay cambios en la lista de seguidores.")
    
    print("\n" + "="*50)

if __name__ == '__main__':
    main()