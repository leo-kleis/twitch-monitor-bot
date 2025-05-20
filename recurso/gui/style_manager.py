from enum import Enum

class MessageType(Enum):
    """Enumeración de los tipos de mensajes posibles"""
    CHAT = "chat"                  # Mensajes normales del chat
    WEBSOCKET = "websocket"        # Mensajes del sistema websocket
    VIEWER_COUNT = "viewer_count"  # Contador de espectadores
    STREAM_INFO = "stream_info"    # Información del stream
    SYSTEM = "system"              # Mensajes de sistema
    ERROR = "error"                # Mensajes de error
    SUCCESS = "success"            # Mensajes de éxito/confirmación
    WARNING = "warning"            # Advertencias
    COMMAND = "command"            # Comandos ejecutados
    BOT = "bot"                    # Mensajes enviados por el bot

class StyleManager:
    """Gestiona los estilos y colores para diferentes tipos de mensajes"""
    
    # Configuración de fuente
    FONT = {
        'family': "'Kanit', sans-serif",
        'default_size': '14px',
        'small_size': '12px',
        'large_size': '16px',
        'monospace': "'Consolas', monospace"
    }
    
    # Colores base (palette)
    COLORS = {
        'white': '#ffffff',
        'light_gray': '#c0c0c0',
        'gray': '#a0a0a0',
        'dark_gray': '#555555',
        'red': '#ff6a6a',
        'green': '#8aff8a',
        'bright_green': '#4aff4a',
        'blue': '#8c9cff',
        'cyan': '#88ffff',
        'yellow': '#ffcc66',
        'orange': '#ffc966',
        'purple': '#ff88ff',
        'pink': '#ff9eee',
    }
    
    # Estilos base (pueden ser combinados)
    STYLES = {
        'normal': '',
        'bold': 'font-weight: bold;',
        'underline': 'text-decoration: underline;',
        'italic': 'font-style: italic;',
    }
    
    # Configuración de estilo para cada tipo de mensaje
    MESSAGE_STYLES = {
        MessageType.CHAT: {
            'color': COLORS['white'],
            'styles': [],
            'font_size': FONT['default_size'],
            'margin': '2px 0'
        },
        MessageType.WEBSOCKET: {
            'color': COLORS['cyan'],
            'styles': [],
            'font_size': FONT['default_size'],
            'margin': '3px 0'
        },
        MessageType.SYSTEM: {
            'color': COLORS['blue'],
            'styles': ['bold'],
            'font_size': FONT['default_size'],
            'margin': '3px 0'
        },
        MessageType.ERROR: {
            'color': COLORS['red'],
            'styles': ['bold'],
            'font_size': FONT['default_size'],
            'margin': '3px 0'
        },
        MessageType.SUCCESS: {
            'color': COLORS['bright_green'],
            'styles': ['bold', 'underline'],
            'font_size': FONT['default_size'],
            'margin': '3px 0'
        },
        MessageType.WARNING: {
            'color': COLORS['yellow'],
            'styles': ['bold'],
            'font_size': FONT['default_size'],
            'margin': '3px 0'
        },
        MessageType.COMMAND: {
            'color': COLORS['orange'],
            'styles': ['bold'],
            'font_size': FONT['default_size'],
            'margin': '3px 0'
        },
        MessageType.BOT: {
            'color': COLORS['purple'],
            'styles': ['bold'],
            'font_size': FONT['default_size'],
            'margin': '3px 0'
        }
    }
    
    @classmethod
    def format_message(cls, message, msg_type_str):
        """Formatea un mensaje según su tipo"""
        # Convertir string a enum si es necesario
        try:
            msg_type = MessageType(msg_type_str)
        except ValueError:
            # Si el tipo no está en la enumeración, usar SYSTEM como fallback
            msg_type = MessageType.SYSTEM
        
        # Obtener configuración de estilo
        if msg_type in cls.MESSAGE_STYLES:
            style_config = cls.MESSAGE_STYLES[msg_type]
        else:
            # Estilo por defecto si no hay configuración específica
            style_config = {
                'color': cls.COLORS['white'],
                'styles': [],
                'font_size': cls.FONT['default_size'],
                'margin': '3px 0'
            }
        
        # Construir el estilo CSS
        style = f"color: {style_config['color']};"
        for style_name in style_config['styles']:
            if style_name in cls.STYLES:
                style += f" {cls.STYLES[style_name]}"
        
        style += f" font-size: {style_config['font_size']};"
        style += f" font-family: {cls.FONT['family']};"
        
        # Crear el HTML formateado
        formatted_message = f'<div style="margin: {style_config["margin"]}; display: block;"><span style="{style}">{message}</span><br></div>'
        
        return formatted_message
    
    @classmethod
    def get_ansi_colors(cls):
        """Devuelve el mapa de colores ANSI a HTML para la conversión"""
        font_family = cls.FONT['family']
        
        return {
            # Colores normales con fuente Kanit
            '\033[30m': f'<span style="color:{cls.COLORS["gray"]}; font-family: {font_family};">',
            '\033[31m': f'<span style="color:{cls.COLORS["red"]}; font-family: {font_family};">',
            '\033[32m': f'<span style="color:{cls.COLORS["green"]}; font-family: {font_family};">',
            '\033[33m': f'<span style="color:{cls.COLORS["yellow"]}; font-family: {font_family};">',
            '\033[34m': f'<span style="color:{cls.COLORS["blue"]}; font-family: {font_family};">',
            '\033[35m': f'<span style="color:{cls.COLORS["purple"]}; font-family: {font_family};">',
            '\033[36m': f'<span style="color:{cls.COLORS["cyan"]}; font-family: {font_family};">',
            '\033[37m': f'<span style="color:{cls.COLORS["white"]}; font-family: {font_family};">',
            
            # Colores brillantes con fuente Kanit
            '\033[90m': f'<span style="color:{cls.COLORS["light_gray"]}; font-family: {font_family};">',
            '\033[91m': f'<span style="color:{cls.COLORS["red"]}; font-family: {font_family};">',
            '\033[92m': f'<span style="color:{cls.COLORS["green"]}; font-family: {font_family};">',
            '\033[93m': f'<span style="color:{cls.COLORS["yellow"]}; font-family: {font_family};">',
            '\033[94m': f'<span style="color:{cls.COLORS["blue"]}; font-family: {font_family};">',
            '\033[95m': f'<span style="color:{cls.COLORS["pink"]}; font-family: {font_family};">',
            '\033[96m': f'<span style="color:{cls.COLORS["cyan"]}; font-family: {font_family};">',
            '\033[97m': f'<span style="color:{cls.COLORS["white"]}; font-family: {font_family};">',
            
            # Estilos con fuente Kanit
            '\033[0m': '</span>',
            '\033[1m': f'<span style="{cls.STYLES["bold"]} font-family: {font_family};">',
            '\033[42m': f'<span style="color:{cls.COLORS["bright_green"]}; {cls.STYLES["bold"]} {cls.STYLES["underline"]} font-family: {font_family};">',
            '\033[43m': f'<span style="color:{cls.COLORS["orange"]}; {cls.STYLES["bold"]} {cls.STYLES["underline"]} font-family: {font_family};">',
        }
    
    @classmethod
    def get_timestamp_style(cls):
        """Estilo para los timestamps"""
        return f"color:{cls.COLORS['gray']}; font-family: {cls.FONT['monospace']};"
    
    @classmethod
    def format_label_value(cls, label, value, label_color='white', value_color='green'):
        """Formatea una etiqueta y su valor con colores diferentes"""
        label_color_hex = cls.COLORS[label_color]
        value_color_hex = cls.COLORS[value_color]
        
        return (f'<span style="color:{label_color_hex}; font-family:{cls.FONT["family"]};">{label}: </span>'
                f'<span style="color:{value_color_hex}; font-family:{cls.FONT["family"]};">{value}</span>')