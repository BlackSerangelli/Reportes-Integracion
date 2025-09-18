<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Empleados por Departamento</title>
                <meta charset="UTF-8"/>
                <link rel="stylesheet" type="text/css" href="empleados.css"/>
            </head>
            <body>
                <h1>Empleados Agrupados por Departamento</h1>
                
                <!-- Iteramos por cada departamento -->
                <xsl:for-each select="company/department">
                    <div class="department-section">
                        <div class="department-header">
                            <xsl:value-of select="@name"/>
                        </div>
                        
                        <table>
                            <thead>
                                <tr>
                                    <th>Nombre Completo</th>
                                    <th>Posición</th>
                                    <th>Salario</th>
                                    <th>Tipo de Contrato</th>
                                </tr>
                            </thead>
                            <tbody>
                                <!-- Iteramos por cada empleado en el departamento -->
                                <xsl:for-each select="employee">
                                    <tr>
                                        <td class="employee-name">
                                            <xsl:value-of select="first_name"/>
                                            <xsl:text> </xsl:text>
                                            <xsl:value-of select="last_name"/>
                                        </td>
                                        <td class="employee-position">
                                            <xsl:value-of select="position"/>
                                        </td>
                                        <td class="employee-salary">
                                            $<xsl:value-of select="format-number(salary, '#,###')"/>
                                        </td>
                                        <td>
                                            <span>
                                                <xsl:attribute name="class">
                                                    contract-type <xsl:value-of select="contract_type"/>
                                                </xsl:attribute>
                                                <xsl:choose>
                                                    <xsl:when test="contract_type = 'tiempo_completo'">
                                                        Tiempo Completo
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        Tiempo Parcial
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </span>
                                        </td>
                                    </tr>
                                </xsl:for-each>
                            </tbody>
                        </table>
                    </div>
                </xsl:for-each>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
