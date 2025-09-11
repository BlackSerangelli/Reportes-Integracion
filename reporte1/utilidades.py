"""
Módulo de utilidades para el preprocesamiento de texto y validaciones.
"""

import re
from typing import Tuple


def preprocesar_texto(texto: str) -> str:
    """
    Preprocesa el texto para la clasificación.
    
    Args:
        texto: Texto a preprocesar
        
    Returns:
        str: Texto preprocesado
    """
    # Convertir a minúsculas
    texto = texto.lower()
    
    # Remover caracteres especiales pero mantener espacios
    texto = re.sub(r'[^\w\s]', ' ', texto)
    
    # Normalizar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto)
    
    # Remover espacios al inicio y final
    texto = texto.strip()
    
    return texto


def validar_entrada(texto: str, longitud_minima: int = 3, longitud_maxima: int = 1000) -> Tuple[bool, str]:
    """
    Valida el texto de entrada.
    
    Args:
        texto: Texto a validar
        longitud_minima: Longitud mínima permitida
        longitud_maxima: Longitud máxima permitida
        
    Returns:
        Tuple[bool, str]: (es_valido, mensaje_error)
    """
    if not isinstance(texto, str):
        return False, "El texto debe ser una cadena de caracteres"
    
    if not texto:
        return False, "El texto no puede estar vacío"
    
    if len(texto) < longitud_minima:
        return False, f"El texto debe tener al menos {longitud_minima} caracteres"
    
    if len(texto) > longitud_maxima:
        return False, f"El texto no puede tener más de {longitud_maxima} caracteres"
    
    return True, ""


def extraer_modelo_de_respuesta(respuesta: str) -> str:
    """
    Extrae el modelo de la respuesta de DeepSeek.
    
    Args:
        respuesta: Respuesta de la API
        
    Returns:
        str: Modelo extraído
    """
    # Limpiar la respuesta
    respuesta = respuesta.strip().lower()
    
    # Buscar los modelos en la respuesta con el formato correcto
    if 'iaas' in respuesta:
        return "IaaS"
    elif 'paas' in respuesta:
        return "PaaS"
    elif 'saas' in respuesta:
        return "SaaS"
    elif 'faas' in respuesta:
        return "FaaS"
    
    # Si no se encuentra ningún modelo específico
    return "No determinado"


def calcular_confianza_de_respuesta(respuesta: str) -> float:
    """
    Calcula la confianza basada en la claridad de la respuesta.
    
    Args:
        respuesta: Respuesta de la API
        
    Returns:
        float: Nivel de confianza (0.0 a 1.0)
    """
    # Limpiar la respuesta
    respuesta = respuesta.strip().lower()
    
    # Factores que aumentan la confianza
    factores_positivos = 0
    factores_negativos = 0
    
    # Respuesta clara y directa
    if len(respuesta) < 20 and any(modelo in respuesta for modelo in ['iaas', 'paas', 'saas', 'faas']):
        factores_positivos += 2
    
    # Respuesta con explicación
    if len(respuesta) > 20:
        factores_positivos += 1
    
    # Respuesta confusa o múltiples modelos
    if respuesta.count('iaas') + respuesta.count('paas') + respuesta.count('saas') + respuesta.count('faas') > 1:
        factores_negativos += 1
    
    # Palabras que indican incertidumbre
    palabras_incertidumbre = ['quizás', 'tal vez', 'posiblemente', 'probablemente', 'no estoy seguro']
    if any(palabra in respuesta for palabra in palabras_incertidumbre):
        factores_negativos += 1
    
    # Calcular confianza base
    confianza_base = 0.8
    
    # Ajustar según factores
    confianza = confianza_base + (factores_positivos * 0.1) - (factores_negativos * 0.2)
    
    # Asegurar que esté en el rango [0.0, 1.0]
    return max(0.0, min(1.0, confianza))