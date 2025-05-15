import os
import json
import random
import requests
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

def load_user_data_twitch(file_path):
    """Carga los datos de usuarios desde un archivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    
def save_user_data_twitch(file_path, user_data_twitch):
    """Guarda los datos de usuarios en un archivo JSON con formato legible."""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(user_data_twitch, file, ensure_ascii=False, indent=2)

def assign_random_color():
    """Asigna un color aleatorio en formato ANSI."""
    excluded_colors = [0, 1, 3, 5, 7]  # Números a excluir
    available_colors = [i for i in range(1, 8) if i not in excluded_colors]
    return f'\033[9{random.choice(available_colors)}m'

def buscar_id_usuario(user):
    headers = {
        'Client-ID': os.getenv("TTG_BOT_CLIENT_ID"),
        'Authorization': f'Bearer {os.getenv("TTG_BOT_TOKEN")}'
    }
    url = f"https://api.twitch.tv/helix/users?login={user}"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['id']
        else:
            print(f"Usuario no encontrado: {user}")
            return None
    else:
        print(f"Error al obtener usuario {user}: {response.status_code} - {response.text}")
        return None

def verificar_follow_fecha(user_id):
    broadcaster_id = os.getenv("BROADCASTER_ID")
    headers = {
        'Client-ID': os.getenv("TTG_BOT_CLIENT_ID"),
        'Authorization': f'Bearer {os.getenv("TTG_BOT_TOKEN")}'
    }
    url = f"https://api.twitch.tv/helix/channels/followers?broadcaster_id={broadcaster_id}&user_id={user_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            follow_date_iso = data['data'][0]['followed_at']
            
            follow_date = datetime.strptime(follow_date_iso, '%Y-%m-%dT%H:%M:%SZ').strftime('%d-%m-%Y')
            return follow_date
        else:
            return None
    else:
        print(f"Error al obtener usuario {user_id}: {response.status_code} - {response.text}")
        return None

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

def name_game(game: str) -> str:
    game = game.lower()
    game_map = {
        'dota 2' : "29595",
        'dota' : "29595",
        'league of legends' : "21779",
        'lol' : "21779",
        'just chatting' : "509658",
        'charlando' : "509658",
        'teamfight tactics' : "513143",
        'tft' : "513143"
    }
    return game_map.get(game, None)

def get_games() -> list:
    games = ['Dota 2 | Dota', 'League of Legends | lol', 'Just Chatting | Charlando',
             'Teamfight Tactics | TFT']
    return games

async def iniciar_gemi(self, ctx):
    load_dotenv()
    GEMINI_API = os.getenv("IA_API")
    genai.configure(api_key=GEMINI_API)

    generation_config = {
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 40
    }

    safety_settings = {
        "HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
        "HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
        "SEXUAL": "BLOCK_MEDIUM_AND_ABOVE",
        "DANGEROUS": "BLOCK_MEDIUM_AND_ABOVE"
    }
    
    tools = [{
        "function_declarations": [
            {
                "name": "change_title",
                "description": "Cambia el título del stream en Twitch",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "El nuevo título para el stream"
                        }
                    },
                    "required": ["title"]
                }
            }
            #{
            #    "name": "change_game",
            #    "description": "Cambia el juego/categoría del stream en Twitch",
            #    "parameters": {
            #        "type": "object",
            #        "properties": {
            #            "game": {
            #                "type": "string",
            #                "description": "El nombre del nuevo juego o categoría"
            #            }
            #        },
            #        "required": ["game"]
            #    }
            #}
        ]
    }]
    
    canal = await ctx.channel.fetch_channel_info(token_for=self.bot.user)
    broadcaster = canal.user.name
    titulo = canal.title
    categoria = canal.game_name

    # Modificamos la instrucción para orientar al modelo a participar en una conversación grupal
    system_instruction = f"""Eres un asistente educativo participando en una conversación grupal con múltiples personas en la plataforma de Twitch del canal {broadcaster}.
    
    INFORMACIÓN CONTEXTUAL:
    - Título actual del stream: "{titulo}"
    - Categoría/juego: "{categoria}"
    
    Utiliza esta información cuando sea relevante en tus respuestas sin necesidad de preguntar. Por ejemplo, si alguien pregunta por el título o categoría actual, responde directamente.
    
    Cada mensaje indicará quién está hablando mediante el formato "Nombre: mensaje".
    Twitch tiene un límite de 500 caracteres por mensaje, así que asegúrate de que tus respuestas sean concisas y claras.
    
    INSTRUCCIÓN IMPORTANTE SOBRE CAMBIO DE TÍTULO:
    Cuando un usuario pida cambiar el título del stream, SIEMPRE DEBES UTILIZAR LA FUNCIÓN change_title en lugar de solo responder con texto.

    Si el usuario te pide cambiar el titulo del stream y ademas te pregunta sobre algo, primero cambia el titulo y luego responde a la pregunta, en este orden:
    1. Cambia el titulo del stream usando la funcion change_title("nuevo titulo").
    2. Responde a la pregunta del usuario (SOLO EN ESTE CASO, cuando cambias titulo + respuesta, el limite sera de 300 caracteres, solo para este caso).
    
    Cuando se pregunta sobre programación, solo explica las cosas, pero no entreges código, el chat de Twitch no tiene la capacidad de mostrar salto de lineas.
    Si existe algun comportamiento inapropiado de alguna persona, ignorar y responder "No responderé a comentarios inapropiados".
    Tus respuestas no pueden contener salto de lineas, y si quieres agregar un emoji, usa el formato de Twitch para emotes.
    """

    model = genai.GenerativeModel(
        model_name='models/gemini-2.0-flash-lite',
        generation_config=generation_config,
        safety_settings=safety_settings,
        system_instruction=system_instruction,
        tools=tools
    )
    
    return model 