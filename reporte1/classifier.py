"""
Clasificador principal de modelos de nube usando NLP con DeepSeek.
"""

import requests
from typing import Optional
from .configuracion import Configuracion
from .modelos import ResultadoClasificacion
from .utilidades import (
    preprocesar_texto,
    validar_entrada,
    extraer_modelo_de_respuesta,
    calcular_confianza_de_respuesta
)


class ClasificadorModelosNube:
    """Clasificador de modelos de nube usando NLP con DeepSeek."""
    
    def __init__(self, usar_nlp: bool = True, clave_api: Optional[str] = None):
        """
        Inicializa el clasificador.
        
        Args:
            usar_nlp: Si usar NLP para clasificación
            clave_api: Clave API personalizada (opcional)
        """
        self.usar_nlp = usar_nlp
        self.config = Configuracion()
        
        # Usar clave API personalizada si se proporciona
        if clave_api:
            self.config._clave_api = clave_api
    
    def clasificar_con_nlp(self, texto: str) -> ResultadoClasificacion:
        """
        Clasifica el texto usando NLP con DeepSeek.
        
        Args:
            texto: Texto a clasificar
            
        Returns:
            ResultadoClasificacion: Resultado de la clasificación
        """
        texto_procesado = preprocesar_texto(texto)
        
        try:
            # Configurar la petición a la API
            clave_api = self.config.clave_api
            url_api = self.config.url_api
            modelo = self.config.modelo
            max_tokens = self.config.max_tokens
            temperature = self.config.temperature
            
            if not clave_api:
                raise ValueError("No se encontró la clave API de OpenRouter")
            
            # Preparar la petición
            encabezados = {
                'Authorization': f'Bearer {clave_api}',
                'Content-Type': 'application/json'
            }
            
            instruccion = f"""Analiza el siguiente texto y determina a qué modelo de servicio en la nube corresponde:

Texto: "{texto}"

Los modelos posibles son:
- IaaS (Infrastructure as a Service): Servicios de infraestructura como servidores, almacenamiento, redes
- PaaS (Platform as a Service): Plataformas de desarrollo y despliegue
- SaaS (Software as a Service): Aplicaciones de software accesibles desde navegador
- FaaS (Function as a Service): Servicios de funciones sin servidor

Responde únicamente con el modelo correspondiente (IaaS, PaaS, SaaS o FaaS)."""

            datos_peticion = {
                "model": modelo,
                "messages": [
                    {"role": "user", "content": instruccion}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Realizar la petición
            respuesta = requests.post(url_api, json=datos_peticion, headers=encabezados)
            
            if respuesta.status_code != 200:
                raise Exception(f"Error en la API: {respuesta.status_code}")
            
            # Procesar la respuesta
            datos_respuesta = respuesta.json()
            contenido_respuesta = datos_respuesta['choices'][0]['message']['content']
            
            # Extraer el modelo y calcular confianza
            modelo_extraido = extraer_modelo_de_respuesta(contenido_respuesta)
            confianza = calcular_confianza_de_respuesta(contenido_respuesta)
            
            # Crear puntajes (simplificado para respuestas de DeepSeek)
            puntajes = {
                'IaaS': 1.0 if modelo_extraido == 'IaaS' else 0.0,
                'PaaS': 1.0 if modelo_extraido == 'PaaS' else 0.0,
                'SaaS': 1.0 if modelo_extraido == 'SaaS' else 0.0,
                'FaaS': 1.0 if modelo_extraido == 'FaaS' else 0.0
            }
            
            return ResultadoClasificacion(
                modelo=modelo_extraido,
                confianza=confianza,
                puntajes=puntajes,
                texto_original=texto,
                texto_procesado=texto_procesado,
                metodo="deepseek_nlp"
            )
            
        except Exception as e:
            # En caso de error, retornar resultado de error
            return ResultadoClasificacion(
                modelo="Error",
                confianza=0.0,
                puntajes={'IaaS': 0.0, 'PaaS': 0.0, 'SaaS': 0.0, 'FaaS': 0.0},
                texto_original=texto,
                texto_procesado=texto_procesado,
                metodo="error"
            )
    
    def clasificar(self, texto: str) -> ResultadoClasificacion:
        """
        Clasifica el texto usando el método configurado.
        
        Args:
            texto: Texto a clasificar
            
        Returns:
            ResultadoClasificacion: Resultado de la clasificación
        """
        # Validar entrada
        es_valido, mensaje_error = validar_entrada(
            texto, 
            self.config.longitud_minima_texto,
            self.config.longitud_maxima_texto
        )
        
        if not es_valido:
            raise ValueError(mensaje_error)
        
        # Usar NLP si está habilitado
        if self.usar_nlp:
            return self.clasificar_con_nlp(texto)
        else:
            # Fallback a método básico (no implementado en esta versión)
            raise NotImplementedError("El modo sin NLP no está implementado")