"""
Módulo que contiene los modelos de datos para el clasificador de modelos de nube.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ResultadoClasificacion:
    """
    Modelo de datos para el resultado de la clasificación.
    
    Attributes:
        modelo: Modelo predicho (IaaS, PaaS, SaaS, FaaS, Error)
        confianza: Nivel de confianza (0.0 a 1.0)
        puntajes: Diccionario con puntajes para cada modelo
        texto_original: Texto original sin procesar
        texto_procesado: Texto después del preprocesamiento
        metodo: Método usado para la clasificación
    """
    modelo: str
    confianza: float
    puntajes: Dict[str, float]
    texto_original: str
    texto_procesado: str
    metodo: str