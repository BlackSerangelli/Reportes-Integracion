<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Informe de Antigüedad de Empleados</title>
                <meta charset="UTF-8"/>
                <link rel="stylesheet" type="text/css" href="empleados.css"/>
            </head>
            <body>
                <h1>Informe de Antigüedad de Empleados</h1>
                <p style="text-align: center; color: #7f8c8d; font-style: italic;">
                    Empleados ordenados por fecha de contratación (de más antiguos a más nuevos)
                </p>
                
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Nombre Completo</th>
                            <th>Departamento</th>
                            <th>Posición</th>
                            <th>Fecha de Contratación</th>
                            <th>Años de Servicio</th>
                            <th>Salario</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Ordenamos todos los empleados por fecha de contratación (más antiguos primero) -->
                        <xsl:for-each select="company/department/employee">
                            <xsl:sort select="@hire_date" order="ascending"/>
                            
                            <tr>
                                <td style="text-align: center; font-weight: bold;">
                                    <xsl:value-of select="position()"/>
                                </td>
                                <td class="employee-name">
                                    <xsl:value-of select="first_name"/>
                                    <xsl:text> </xsl:text>
                                    <xsl:value-of select="last_name"/>
                                </td>
                                <td class="employee-position">
                                    <xsl:value-of select="../@name"/>
                                </td>
                                <td>
                                    <xsl:value-of select="position"/>
                                </td>
                                <td class="employee-date">
                                    <xsl:value-of select="@hire_date"/>
                                </td>
                                <td style="text-align: center; font-weight: bold; color: #8e44ad;">
                                    <!-- Calculamos años aproximados basados en la fecha de contratación -->
                                    <xsl:variable name="hireYear" select="substring(@hire_date, 1, 4)"/>
                                    <xsl:variable name="currentYear" select="2025"/>
                                    <xsl:value-of select="$currentYear - $hireYear"/>
                                    <xsl:text> años</xsl:text>
                                </td>
                                <td class="employee-salary">
                                    $<xsl:value-of select="format-number(salary, '#,###')"/>
                                </td>
                            </tr>
                        </xsl:for-each>
                    </tbody>
                </table>
                
                <h2>Análisis de Antigüedad</h2>
                
                <div class="average-info">
                    <h3>Estadísticas Generales</h3>
                    <xsl:variable name="oldestEmployee" select="company/department/employee[not(../employee/@hire_date &lt; @hire_date)]"/>
                    <xsl:variable name="newestEmployee" select="company/department/employee[not(../employee/@hire_date > @hire_date)]"/>
                    
                    <p><strong>Empleado más antiguo:</strong> 
                        <span class="employee-name">
                            <xsl:value-of select="$oldestEmployee/first_name"/>
                            <xsl:text> </xsl:text>
                            <xsl:value-of select="$oldestEmployee/last_name"/>
                        </span>
                        - Contratado el <xsl:value-of select="$oldestEmployee/@hire_date"/>
                    </p>
                    
                    <p><strong>Empleado más nuevo:</strong> 
                        <span class="employee-name">
                            <xsl:value-of select="$newestEmployee/first_name"/>
                            <xsl:text> </xsl:text>
                            <xsl:value-of select="$newestEmployee/last_name"/>
                        </span>
                        - Contratado el <xsl:value-of select="$newestEmployee/@hire_date"/>
                    </p>
                </div>
                
                <h3>Empleados por Rango de Antigüedad</h3>
                
                <div class="department-section">
                    <h3>Veteranos (5+ años de servicio)</h3>
                    <ul>
                        <xsl:for-each select="company/department/employee">
                            <xsl:variable name="hireYear" select="substring(@hire_date, 1, 4)"/>
                            <xsl:variable name="yearsOfService" select="2025 - $hireYear"/>
                            
                            <xsl:if test="$yearsOfService >= 5">
                                <li>
                                    <div class="employee-info">
                                        <div>
                                            <span class="employee-name">
                                                <xsl:value-of select="first_name"/>
                                                <xsl:text> </xsl:text>
                                                <xsl:value-of select="last_name"/>
                                            </span>
                                            <br/>
                                            <span class="employee-position">
                                                <xsl:value-of select="position"/> - <xsl:value-of select="../@name"/>
                                            </span>
                                        </div>
                                        <div>
                                            <span class="employee-date">
                                                <xsl:value-of select="$yearsOfService"/> años
                                            </span>
                                            <br/>
                                            <span class="employee-salary">
                                                $<xsl:value-of select="format-number(salary, '#,###')"/>
                                            </span>
                                        </div>
                                    </div>
                                </li>
                            </xsl:if>
                        </xsl:for-each>
                    </ul>
                </div>
                
                <div class="department-section">
                    <h3>Empleados Establecidos (2-4 años de servicio)</h3>
                    <ul>
                        <xsl:for-each select="company/department/employee">
                            <xsl:variable name="hireYear" select="substring(@hire_date, 1, 4)"/>
                            <xsl:variable name="yearsOfService" select="2025 - $hireYear"/>
                            
                            <xsl:if test="$yearsOfService >= 2 and $yearsOfService &lt; 5">
                                <li>
                                    <div class="employee-info">
                                        <div>
                                            <span class="employee-name">
                                                <xsl:value-of select="first_name"/>
                                                <xsl:text> </xsl:text>
                                                <xsl:value-of select="last_name"/>
                                            </span>
                                            <br/>
                                            <span class="employee-position">
                                                <xsl:value-of select="position"/> - <xsl:value-of select="../@name"/>
                                            </span>
                                        </div>
                                        <div>
                                            <span class="employee-date">
                                                <xsl:value-of select="$yearsOfService"/> años
                                            </span>
                                            <br/>
                                            <span class="employee-salary">
                                                $<xsl:value-of select="format-number(salary, '#,###')"/>
                                            </span>
                                        </div>
                                    </div>
                                </li>
                            </xsl:if>
                        </xsl:for-each>
                    </ul>
                </div>
                
                <div class="department-section">
                    <h3>Empleados Nuevos (menos de 2 años de servicio)</h3>
                    <ul>
                        <xsl:for-each select="company/department/employee">
                            <xsl:variable name="hireYear" select="substring(@hire_date, 1, 4)"/>
                            <xsl:variable name="yearsOfService" select="2025 - $hireYear"/>
                            
                            <xsl:if test="$yearsOfService &lt; 2">
                                <li>
                                    <div class="employee-info">
                                        <div>
                                            <span class="employee-name">
                                                <xsl:value-of select="first_name"/>
                                                <xsl:text> </xsl:text>
                                                <xsl:value-of select="last_name"/>
                                            </span>
                                            <br/>
                                            <span class="employee-position">
                                                <xsl:value-of select="position"/> - <xsl:value-of select="../@name"/>
                                            </span>
                                        </div>
                                        <div>
                                            <span class="employee-date">
                                                <xsl:value-of select="$yearsOfService"/> años
                                            </span>
                                            <br/>
                                            <span class="employee-salary">
                                                $<xsl:value-of select="format-number(salary, '#,###')"/>
                                            </span>
                                        </div>
                                    </div>
                                </li>
                            </xsl:if>
                        </xsl:for-each>
                    </ul>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
