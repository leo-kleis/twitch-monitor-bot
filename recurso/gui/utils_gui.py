import re
from datetime import datetime
from recurso.gui.style_manager import StyleManager

def ansi_to_html(text):
    """Convierte códigos ANSI de color a HTML"""
    # Usar colores del StyleManager
    ansi_colors = StyleManager.get_ansi_colors()

    # Procesar códigos ANSI
    for ansi, html in ansi_colors.items():
        if ansi in text:
            text = text.replace(ansi, html)
    
    # Limpiar cualquier código ANSI restante
    text = re.sub(r'\033\[[0-9;]*m', '', text)
    
    # Asegurar que todos los spans estén cerrados
    open_spans = text.count('<span')
    close_spans = text.count('</span>')
    if open_spans > close_spans:
        text += '</span>' * (open_spans - close_spans)
        
    return text

def log_and_callback(self, message, msg_type):
    """Registra un mensaje en el log y lo envía al callback si está definido"""
    self.LOGGER.info(message)  # Siempre registra en consola
    
    # Solo envía al callback si existe (modo GUI)
    if self.message_callback:
        # En lugar de eliminar los códigos ANSI, conviértelos a HTML
        html_message = ansi_to_html(message)
        
        # Obtener la hora actual en formato HH:MM:SS
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Añadir la hora al mensaje con el estilo de timestamp del StyleManager
        timestamp_style = StyleManager.get_timestamp_style()
        html_message = f'<span style="{timestamp_style}">({current_time})</span> {html_message}'
        
        # Enviar el mensaje con hora al callback
        self.message_callback(html_message, msg_type)