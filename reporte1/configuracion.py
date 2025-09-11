"""
Módulo de configuración para el clasificador de modelos de nube.
Carga las variables de entorno desde el archivo de configuración.
"""

import os
from pathlib import Path
from typing import Optional


class Configuracion:
    """Clase para manejar la configuración del clasificador."""
    
    def __init__(self):
        """Inicializa la configuración cargando las variables de entorno."""
        self._cargar_variables_entorno()
    
    def _cargar_variables_entorno(self):
        """Carga las variables de entorno desde el archivo config.env."""
        try:
            # Buscar el archivo config.env en el directorio config/
            config_path = Path(__file__).parent.parent / "config" / "config.env"
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️  Advertencia: No se pudo cargar config.env: {e}")
    
    @property
    def clave_api(self) -> str:
        """Retorna la clave API de OpenRouter."""
        return os.getenv('OPENROUTER_API_KEY', '')
    
    @property
    def url_api(self) -> str:
        """Retorna la URL de la API de OpenRouter."""
        return os.getenv('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1/chat/completions')
    
    @property
    def modelo(self) -> str:
        """Retorna el modelo de DeepSeek a usar."""
        return os.getenv('DEEPSEEK_MODEL', 'deepseek/deepseek-chat')
    
    @property
    def max_tokens(self) -> int:
        """Retorna el número máximo de tokens."""
        return int(os.getenv('MAX_TOKENS', '50'))
    
    @property
    def temperature(self) -> float:
        """Retorna la temperatura para la generación."""
        return float(os.getenv('TEMPERATURE', '0.1'))
    
    @property
    def longitud_minima_texto(self) -> int:
        """Retorna la longitud mínima de texto válido."""
        return int(os.getenv('MIN_TEXT_LENGTH', '3'))
    
    @property
    def longitud_maxima_texto(self) -> int:
        """Retorna la longitud máxima de texto válido."""
        return int(os.getenv('MAX_TEXT_LENGTH', '1000'))