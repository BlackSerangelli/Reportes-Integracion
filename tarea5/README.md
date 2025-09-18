# Sistema de Registro de Empleados - XSLT

Este proyecto contiene un sistema completo de transformaciones XSLT para generar diferentes reportes de empleados basados en datos XML.

## Archivos del Proyecto

### Datos Base
- **`empleados.xml`** - Archivo XML con datos de empleados organizados por departamento
- **`empleados.css`** - Hoja de estilos CSS para las transformaciones HTML

### Transformaciones XSLT

1. **`1_empleados_por_departamento.xsl`**
   - **Propósito**: Agrupa empleados por departamento en una tabla HTML
   - **Características**: Muestra nombre completo, posición, salario y tipo de contrato
   - **Punto clave**: Agrupación por elemento `<department>`

2. **`2_salario_promedio_departamento.xsl`**
   - **Propósito**: Calcula y muestra el salario promedio por departamento
   - **Características**: Incluye estadísticas generales y análisis detallado
   - **Punto clave**: Suma y promedia valores numéricos en XSLT

3. **`3_empleados_tiempo_completo.xsl`**
   - **Propósito**: Filtra y muestra solo empleados de tiempo completo
   - **Características**: Incluye análisis por departamento y porcentajes
   - **Punto clave**: Uso de condiciones XSLT (`<xsl:if>` y `<xsl:choose>`)

4. **`4_informe_antiguedad.xsl`**
   - **Propósito**: Ordena empleados por fecha de contratación (más antiguos primero)
   - **Características**: Calcula años de servicio y categoriza por antigüedad
   - **Punto clave**: Ordenamiento por atributo `hire_date`

5. **`5_vista_jerarquica.xsl`**
   - **Propósito**: Vista jerárquica de departamentos y empleados
   - **Características**: Estructura visual con iconos y resumen ejecutivo
   - **Punto clave**: Visualización jerárquica basada en estructura XML

## Cómo Usar las Transformaciones

### Opción 1: Navegador Web (Recomendado)
1. Abrir cualquier archivo XSLT en un navegador web moderno
2. El navegador aplicará automáticamente la transformación al XML
3. Se mostrará el resultado HTML con estilos CSS aplicados

### Opción 2: Herramientas de Línea de Comandos

#### Con `xsltproc` (Linux/Mac):
```bash
# Instalar xsltproc si no está disponible
# Ubuntu/Debian: sudo apt-get install xsltproc
# Mac: brew install libxslt

# Generar reportes HTML
xsltproc 1_empleados_por_departamento.xsl empleados.xml > reporte1.html
xsltproc 2_salario_promedio_departamento.xsl empleados.xml > reporte2.html
xsltproc 3_empleados_tiempo_completo.xsl empleados.xml > reporte3.html
xsltproc 4_informe_antiguedad.xsl empleados.xml > reporte4.html
xsltproc 5_vista_jerarquica.xsl empleados.xml > reporte5.html
```

#### Con Saxon (Java):
```bash
# Descargar Saxon-HE desde https://saxon.sourceforge.net/
java -jar saxon-he-12.3.jar -s:empleados.xml -xsl:1_empleados_por_departamento.xsl -o:reporte1.html
```

### Opción 3: Editores XML
- XMLSpy, Oxygen XML Editor, Visual Studio Code con extensiones XML

## Estructura de Datos XML

```xml
<company>
  <department name="Nombre del Departamento">
    <employee id="001" hire_date="2020-03-15">
      <first_name>Nombre</first_name>
      <last_name>Apellido</last_name>
      <position>Cargo</position>
      <salary>50000</salary>
      <contract_type>tiempo_completo|tiempo_parcial</contract_type>
    </employee>
  </department>
</company>
```

## Características Técnicas Implementadas

### 1. Agrupación y Ordenamiento
- Agrupación por departamento usando `<xsl:for-each>`
- Ordenamiento por fecha usando `<xsl:sort>`
- Ordenamiento alfabético y numérico

### 2. Cálculos Matemáticos
- Suma de salarios con `sum()`
- Cálculo de promedios con `div`
- Conteo de elementos con `count()`
- Formateo de números con `format-number()`

### 3. Filtrado Condicional
- Filtros con `<xsl:if>`
- Condiciones múltiples con `<xsl:choose>`
- Comparaciones de cadenas y números

### 4. Manipulación de Fechas
- Extracción de año con `substring()`
- Cálculos de antigüedad
- Comparaciones de fechas

### 5. Presentación Visual
- CSS moderno con flexbox y grid
- Diseño responsivo
- Iconos y elementos visuales
- Esquemas de color profesionales

## Datos de Ejemplo

El archivo incluye 12 empleados distribuidos en 4 departamentos:
- **Recursos Humanos**: 3 empleados
- **Tecnología**: 4 empleados  
- **Ventas**: 3 empleados
- **Marketing**: 2 empleados

Cada empleado tiene información completa incluyendo fechas de contratación desde 2018 hasta 2023.

## Extensibilidad

El sistema está diseñado para ser fácilmente extensible:
- Agregar nuevos departamentos al XML
- Crear nuevas transformaciones XSLT
- Modificar estilos CSS
- Agregar nuevos campos a los empleados

## Compatibilidad

- **XSLT**: Versión 1.0 (máxima compatibilidad)
- **CSS**: CSS3 con fallbacks
- **HTML**: HTML 4.01 Strict
- **Navegadores**: Chrome, Firefox, Safari, Edge
