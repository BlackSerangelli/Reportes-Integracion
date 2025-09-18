# Catálogo de Música - Transformaciones XSLT

Este proyecto implementa un catálogo de música con 5 transformaciones XSLT diferentes que demuestran técnicas avanzadas de procesamiento XML.

## 📁 Estructura del Proyecto

```
tarea4/
├── catalogo_musica.xml              # Archivo XML base con datos del catálogo
├── 1_albums_por_artista.xsl         # XSLT: Agrupación por artista
├── 2_canciones_duracion_total.xsl   # XSLT: Canciones con duración total
├── 3_filtro_sencillos.xsl          # XSLT: Filtro de sencillos
├── 4_indice_artistas.xsl           # XSLT: Índice alfabético
├── 5_filtro_genero.xsl             # XSLT: Filtro por género
├── *.html                          # Archivos HTML generados
└── README.md                       # Este archivo
```

## 🎯 Transformaciones Implementadas

### 1. **Álbumes por Artista** (`1_albums_por_artista.xsl`)
- **Objetivo**: Agrupa álbumes por artista mostrando información del artista y sus álbumes
- **Técnicas XSLT**: 
  - Agrupación con `<xsl:for-each>`
  - Acceso a atributos con `@nombre`, `@pais`
  - Navegación de elementos padre-hijo
- **Salida**: `1_albums_por_artista.html`

### 2. **Canciones con Duración Total** (`2_canciones_duracion_total.xsl`)
- **Objetivo**: Lista canciones de cada álbum con cálculo de duración total
- **Técnicas XSLT**:
  - Templates personalizados para conversión de tiempo
  - Recursión para sumar duraciones
  - Cálculos matemáticos con `floor()` y operadores
- **Salida**: `2_canciones_duracion_total.html`

### 3. **Filtro de Sencillos** (`3_filtro_sencillos.xsl`)
- **Objetivo**: Muestra solo canciones marcadas como sencillos
- **Técnicas XSLT**:
  - Filtrado condicional con `[@single='true']`
  - Conteo con `count()`
  - Condicionales con `<xsl:if>`
- **Salida**: `3_filtro_sencillos.html`

### 4. **Índice Alfabético de Artistas** (`4_indice_artistas.xsl`)
- **Objetivo**: Índice alfabético con álbumes ordenados por año
- **Técnicas XSLT**:
  - Ordenamiento con `<xsl:sort select="@nombre"`
  - Ordenamiento numérico con `data-type="number"`
  - Generación de IDs únicos con `generate-id()`
  - Navegación interna con enlaces
- **Salida**: `4_indice_artistas.html`

### 5. **Filtro por Género** (`5_filtro_genero.xsl`)
- **Objetivo**: Filtra álbumes por género musical específico
- **Técnicas XSLT**:
  - Parámetros externos con `<xsl:param>`
  - Filtrado avanzado con expresiones XPath
  - Condicionales complejas con `<xsl:choose>/<xsl:when>/<xsl:otherwise>`
  - Eliminación de duplicados con `preceding::`
- **Salida**: `5_filtro_genero_rock.html`, `5_filtro_genero_pop.html`

## 🚀 Cómo Ver las Transformaciones XSLT

### Prerequisitos
- Tener Python 3 instalado (incluido en macOS y la mayoría de distribuciones Linux)

### Método Recomendado: Servidor Local

Para evitar las restricciones de seguridad del navegador con archivos locales, levanta un servidor HTTP simple:

```bash
# 1. Levantar servidor local en el directorio del proyecto
python3 -m http.server 8000

# 2. Abrir las transformaciones en tu navegador:
# http://localhost:8000/catalogo_albums_artista.xml    - Álbumes por artista
# http://localhost:8000/catalogo_duracion_total.xml    - Canciones con duración total  
# http://localhost:8000/catalogo_sencillos.xml         - Solo sencillos
# http://localhost:8000/catalogo_indice.xml            - Índice alfabético
# http://localhost:8000/catalogo_musica.xml            - Catálogo completo con CSS

# 3. Para detener el servidor: Ctrl+C
```

### Filtro por Género (Requiere parámetros)

Para el filtro de género, genera los HTML con parámetros específicos:

```bash
# Filtro de Rock
xsltproc --stringparam genero-filtro "Rock" 5_filtro_genero.xsl catalogo_musica.xml > filtro_rock.html

# Filtro de Pop  
xsltproc --stringparam genero-filtro "Pop" 5_filtro_genero.xsl catalogo_musica.xml > filtro_pop.html

# Luego ver en: http://localhost:8000/filtro_rock.html y http://localhost:8000/filtro_pop.html
```

## 📊 Datos del Catálogo

El catálogo incluye:
- **5 Artistas**: The Beatles, Michael Jackson, Queen, Madonna, Led Zeppelin
- **8 Álbumes** con información completa
- **70+ Canciones** con duraciones y marcadores de sencillos
- **2 Géneros**: Rock y Pop
- **Países**: Reino Unido, Estados Unidos

## 🎨 Características de Diseño

Todas las transformaciones incluyen:
- ✨ **CSS moderno** con gradientes y efectos hover
- 📱 **Diseño responsive** y centrado
- 🎯 **Iconos emoji** para mejor UX
- 📊 **Estadísticas** y conteos dinámicos
- 🎨 **Colores temáticos** únicos por transformación

## 🔧 Técnicas XSLT Avanzadas Implementadas

1. **Agrupación y Ordenamiento**
   - `<xsl:for-each>` con `<xsl:sort>`
   - Ordenamiento alfabético y numérico

2. **Cálculos Matemáticos**
   - Conversión de formatos de tiempo
   - Suma recursiva de duraciones
   - Operaciones con `floor()`, `mod`, `div`

3. **Filtrado Condicional**
   - Predicados XPath complejos
   - `<xsl:if>` y `<xsl:choose>`
   - Filtros por atributos y valores

4. **Parámetros y Variables**
   - `<xsl:param>` para parámetros externos
   - `<xsl:variable>` para cálculos intermedios

5. **Templates Personalizados**
   - Templates con nombre para reutilización
   - Recursión para procesamiento iterativo

6. **Navegación XML**
   - Ejes XPath (`preceding::`, `ancestor::`)
   - Generación de IDs únicos
   - Acceso a elementos padre y hermanos

## 📝 Notas Técnicas

- **Versión XSLT**: 1.0 (máxima compatibilidad)
- **Codificación**: UTF-8
- **Salida**: HTML5 válido con CSS embebido
- **Compatibilidad**: Todos los navegadores modernos

## 🎓 Objetivos Pedagógicos Cumplidos

✅ **Agrupación de elementos** por artista  
✅ **Cálculo de sumas** (duración total)  
✅ **Filtrado condicional** (sencillos y géneros)  
✅ **Ordenamiento** alfabético y cronológico  
✅ **Uso de parámetros** externos  
✅ **Templates personalizados** y recursión  
✅ **Navegación compleja** en XML  
✅ **Generación de HTML** estilizado  

Este proyecto demuestra un dominio completo de las técnicas XSLT para transformación y presentación de datos XML.
