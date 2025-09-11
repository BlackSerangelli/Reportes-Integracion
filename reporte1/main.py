"""
Script principal para ejecutar el clasificador de modelos de nube.
Soporta ejecución interactiva y por línea de comandos.
"""

import argparse
import sys
from . import ClasificadorModelosNube


def clasificar_texto(texto: str):
    """
    Clasifica un texto y muestra los resultados.
    
    Args:
        texto: Texto a clasificar
    """
    try:
        clasificador = ClasificadorModelosNube(usar_nlp=True)
        resultado = clasificador.clasificar(texto)
        
        if resultado.modelo == "Error":
            print(f"❌ Error en la clasificación")
            return False
        
        # Mostrar resultado
        print(f"🎯 Modelo: {resultado.modelo}")
        print(f"📊 Confianza: {resultado.confianza:.2f}")
        print("📈 Puntajes:")
        for tipo_modelo, puntaje in resultado.puntajes.items():
            print(f"  {tipo_modelo}: {puntaje:.2f}")
        
        return True
        
    except ValueError as e:
        print(f"❌ Error de validación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def modo_interactivo():
    """Ejecuta el clasificador en modo interactivo."""
    print("🤖 CLASIFICADOR DE MODELOS DE NUBE CON NLP")
    print("=" * 60)
    print("Clasifica textos en modelos de nube: IaaS, PaaS, SaaS, FaaS")
    print("Usa DeepSeek a través de OpenRouter para análisis inteligente")
    print("=" * 60)
    print("\n🔄 MODO INTERACTIVO")
    print("Escribe 'salir' para terminar\n")
    
    while True:
        try:
            texto = input("📝 Ingresa el texto a clasificar: ").strip()
            
            if texto.lower() in ['salir', 'exit', 'quit']:
                print("👋 ¡Hasta luego!")
                break
            
            if not texto:
                print("⚠️  Por favor ingresa algún texto")
                continue
            
            print("-" * 50)
            clasificar_texto(texto)
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except EOFError:
            print("\n👋 ¡Hasta luego!")
            break


def modo_demo():
    """Ejecuta la demostración del clasificador."""
    from setup.demo import ejecutar_demo
    ejecutar_demo()


def configurar_argumentos():
    """Configura los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Clasificador de modelos de nube usando NLP con DeepSeek",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                                    # Modo interactivo
  python main.py -t "AWS EC2 servidores virtuales"  # Clasificar texto
  python main.py --demo                             # Ejecutar demostración
        """
    )
    
    # Grupo de modos de ejecución
    grupo_modos = parser.add_mutually_exclusive_group(required=False)
    
    grupo_modos.add_argument(
        '-t', '--texto',
        type=str,
        help='Texto a clasificar'
    )
    
    grupo_modos.add_argument(
        '--demo',
        action='store_true',
        help='Ejecutar demostración completa'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Clasificador de Modelos de Nube v1.0.0'
    )
    
    return parser


def main():
    """Función principal del programa."""
    parser = configurar_argumentos()
    args = parser.parse_args()
    
    # Si no se proporcionan argumentos, ejecutar modo interactivo
    if len(sys.argv) == 1:
        modo_interactivo()
        return
    
    # Procesar argumentos
    if args.demo:
        modo_demo()
    
    elif args.texto:
        print("🤖 CLASIFICADOR DE MODELOS DE NUBE CON NLP")
        print("=" * 60)
        print("Clasifica textos en modelos de nube: IaaS, PaaS, SaaS, FaaS")
        print("Usa DeepSeek a través de OpenRouter para análisis inteligente")
        print("=" * 60)
        print(f"\n📝 Clasificando: {args.texto}")
        print("-" * 50)
        clasificar_texto(args.texto)
    
    else:
        # Modo interactivo por defecto
        modo_interactivo()


if __name__ == "__main__":
    main()