"""
Módulo de demostración para mostrar el uso del clasificador de modelos de nube.
"""

from . import ClasificadorModelosNube


class DemostradorClasificador:
    """Clase para demostrar el uso del clasificador."""
    
    def __init__(self):
        """Inicializa el demostrador."""
        self.clasificador = ClasificadorModelosNube(usar_nlp=True)
    
    def ejecutar_demo_basica(self):
        """Ejecuta una demostración básica del clasificador."""
        print("=== DEMOSTRACIÓN BÁSICA DEL CLASIFICADOR ===")
        print("🤖 Usando DeepSeek a través de OpenRouter para análisis de texto real\n")
        
        ejemplos = [
            "AWS EC2 proporciona servidores virtuales escalables en la nube",
            "Heroku ofrece una plataforma para desplegar aplicaciones web fácilmente",
            "Salesforce es una aplicación CRM que se accede desde el navegador",
            "AWS Lambda ejecuta funciones sin servidor basadas en eventos",
            "Google Cloud Storage es un servicio de almacenamiento en la nube"
        ]
        
        for i, texto in enumerate(ejemplos, 1):
            print(f"📋 Ejemplo {i}:")
            print(f"Texto: {texto}")
            
            try:
                resultado = self.clasificador.clasificar(texto)
                
                if resultado.modelo == "Error":
                    print(f"❌ Error en la clasificación")
                else:
                    print(f"🎯 Modelo predicho: {resultado.modelo}")
                    print(f"📊 Confianza: {resultado.confianza:.2f}")
                    print("📈 Puntajes:")
                    for tipo_modelo, puntaje in resultado.puntajes.items():
                        print(f"  {tipo_modelo}: {puntaje:.2f}")
                
            except ValueError as e:
                print(f"❌ Error de validación: {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("-" * 50)
    
    def clasificar_texto_personalizado(self, texto: str):
        """
        Clasifica un texto personalizado proporcionado por el usuario.
        
        Args:
            texto: Texto a clasificar
        """
        print(f"\n🔍 CLASIFICANDO TEXTO PERSONALIZADO")
        print(f"Texto: {texto}")
        print("-" * 50)
        
        try:
            resultado = self.clasificador.clasificar(texto)
            
            if resultado.modelo == "Error":
                print(f"❌ Error en la clasificación")
            else:
                print(f"🎯 Modelo predicho: {resultado.modelo}")
                print(f"📊 Confianza: {resultado.confianza:.2f}")
                print("📈 Puntajes:")
                for tipo_modelo, puntaje in resultado.puntajes.items():
                    print(f"  {tipo_modelo}: {puntaje:.2f}")
                
                print(f"\n📝 Información adicional:")
                print(f"  Texto original: {resultado.texto_original}")
                print(f"  Texto procesado: {resultado.texto_procesado}")
                print(f"  Método usado: {resultado.metodo}")
            
        except ValueError as e:
            print(f"❌ Error de validación: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def mostrar_informacion_clasificador(self):
        """Muestra información sobre el clasificador."""
        print("ℹ️  INFORMACIÓN DEL CLASIFICADOR")
        print("=" * 50)
        print("• Usa NLP real con DeepSeek a través de OpenRouter")
        print("• Clasifica en 4 modelos: IaaS, PaaS, SaaS, FaaS")
        print("• Maneja errores ortográficos y texto mal escrito")
        print("• Proporciona nivel de confianza para cada clasificación")
        print("• Configuración flexible mediante variables de entorno")
        print("=" * 50)


def ejecutar_demo():
    """Función para ejecutar la demostración completa."""
    demostrador = DemostradorClasificador()
    
    # Mostrar información
    demostrador.mostrar_informacion_clasificador()
    
    # Ejecutar demo básica
    demostrador.ejecutar_demo_basica()
    
    # Ejemplo de texto personalizado
    texto_personalizado = "Microsoft Azure proporciona servicios de computación en la nube"
    demostrador.clasificar_texto_personalizado(texto_personalizado)