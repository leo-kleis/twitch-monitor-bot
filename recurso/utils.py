import os
import json
import random

def get_user_color(username, user_colors):
    if username not in user_colors:
        excluded_colors = [0, 1, 3, 5, 7]  # Números a excluir
        available_colors = [i for i in range(1, 8) if i not in excluded_colors]
        user_colors[username] = f'\033[9{random.choice(available_colors)}m'
    return user_colors[username]

def save_user_colors(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file)

def load_user_colors(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}

def save_user_followers(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file)

def load_user_followers(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}

def rol_user(user) -> str:
    roles_map = {
        'moderator': "MOD",
        'vip': "Vip",
        'artist': "Art",
        'subscriber': "Sub",
        'turbo' : "Turbo",
        'prime': "Primer"
    }
    
    # Recolectar roles activos
    active_roles = [emoji for attr, emoji in roles_map.items() if getattr(user, attr, False)]
    
    # Si no hay roles, retornar cadena vacía
    if not active_roles:
        return ""
    
    return f"[{' | '.join(active_roles)}] "