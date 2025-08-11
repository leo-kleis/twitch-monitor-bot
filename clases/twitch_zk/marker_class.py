import aiohttp
import asyncio
import os
import logging
from typing import Optional

LOGGER = logging.getLogger("MARKER")
LOGGER.setLevel(logging.INFO)

class TwitchMarkerManager:
    """Clase para gestionar la creación de marcadores en streams de Twitch"""

    def __init__(self, token=None, client_id=None, user_id=None):
        """
        Inicializar el gestor de marcadores
        
        Args:
            client_id: ID de cliente de la aplicación Twitch
            token: Token OAuth del bot
            user_id: ID del usuario en Twitch
        """
        self.client_id = client_id
        self.token = token
        self.user_id = user_id
        self.base_url = "https://api.twitch.tv/helix"
        self._session: Optional[aiohttp.ClientSession] = None  # Sesión reutilizable
        
        # Validar que tenemos los datos necesarios
        if not all([self.client_id, self.token, self.user_id]):
            raise ValueError("Se requieren TTG_CLIENT_ID, TTG_BOT_TOKEN y TTG_ID en el archivo .env")

    async def _get_session(self):
        """Obtener o crear una sesión de aiohttp reutilizable"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Cerrar la sesión de aiohttp si está abierta"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def create_stream_marker(self, description=None):
        """
        Crear un marcador en el stream actual
        
        Args:
            description: Descripción opcional del marcador (máximo 140 caracteres)
            
        Returns:
            Dict con la respuesta de la API de Twitch o información de error
        """
        try:
            # Validar que tenemos los datos necesarios
            if not self.token or not self.client_id:
                return {
                    'success': False,
                    'error': 'OAuth token o Client ID no están disponibles'
                }
            
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Client-Id': self.client_id,
                'Content-Type': 'application/json'
            }
            
            # Datos para crear el marcador
            data = {
                'user_id': self.user_id
            }
            
            # Agregar descripción si se proporciona
            if description:
                # Truncar descripción si excede 140 caracteres
                description = description[:140] if len(description) > 140 else description
                data['description'] = description
            
            url = f"{self.base_url}/streams/markers"
            
            # Usar la sesión reutilizable con timeout
            session = await self._get_session()
            timeout = aiohttp.ClientTimeout(total=10.0)  # 10 segundos de timeout
            
            async with session.post(url, headers=headers, json=data, timeout=timeout) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # La API de Twitch devuelve la data en response_data['data'][0]
                    marker_data = response_data.get('data', [{}])[0] if response_data.get('data') else {}
                    marker_description = marker_data.get('description', description or 'Sin descripción')
                    LOGGER.info(f"Marcador creado exitosamente: {marker_description}")
                    return {
                        'success': True,
                        'data': response_data,
                        'message': 'Marcador creado exitosamente'
                    }
                else:
                    LOGGER.error(f"Error al crear marcador: {response.status} - {response_data}")
                    return {
                        'success': False,
                        'error': f'Error HTTP {response.status}',
                        'details': response_data
                    }
                    
        except asyncio.TimeoutError:
            LOGGER.error("Timeout al crear marcador")
            return {
                'success': False,
                'error': 'Timeout al conectar con la API de Twitch'
            }
        except Exception as e:
            LOGGER.error(f"Excepción al crear marcador: {e}")
            return {
                'success': False,
                'error': f'Excepción: {str(e)}'
            }
            