<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Empleados de Tiempo Completo</title>
                <meta charset="UTF-8"/>
                <link rel="stylesheet" type="text/css" href="empleados.css"/>
            </head>
            <body>
                <h1>Empleados de Tiempo Completo</h1>
                
                <div class="average-info">
                    <h3>Resumen</h3>
                    <xsl:variable name="totalFullTime" select="count(company/department/employee[contract_type='tiempo_completo'])"/>
                    <xsl:variable name="totalEmployees" select="count(company/department/employee)"/>
                    <p><strong>Total de empleados de tiempo completo:</strong> <xsl:value-of select="$totalFullTime"/></p>
                    <p><strong>Total de empleados:</strong> <xsl:value-of select="$totalEmployees"/></p>
                    <p><strong>Porcentaje de tiempo completo:</strong> 
                        <span class="average-value">
                            <xsl:value-of select="format-number(($totalFullTime div $totalEmployees) * 100, '##.#')"/>%
                        </span>
                    </p>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Nombre Completo</th>
                            <th>Departamento</th>
                            <th>Posición</th>
                            <th>Salario</th>
                            <th>Fecha de Contratación</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Filtramos solo empleados de tiempo completo -->
                        <xsl:for-each select="company/department/employee[contract_type='tiempo_completo']">
                            <!-- Ordenamos por departamento y luego por nombre -->
                            <xsl:sort select="../@name"/>
                            <xsl:sort select="first_name"/>
                            
                            <tr>
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
                                <td class="employee-salary">
                                    $<xsl:value-of select="format-number(salary, '#,###')"/>
                                </td>
                                <td class="employee-date">
                                    <xsl:value-of select="@hire_date"/>
                                </td>
                            </tr>
                        </xsl:for-each>
                    </tbody>
                </table>
                
                <h2>Análisis por Departamento</h2>
                <xsl:for-each select="company/department">
                    <xsl:variable name="deptFullTime" select="count(employee[contract_type='tiempo_completo'])"/>
                    <xsl:variable name="deptTotal" select="count(employee)"/>
                    
                    <xsl:if test="$deptFullTime > 0">
                        <div class="department-section">
                            <h3><xsl:value-of select="@name"/></h3>
                            <div class="average-info">
                                <p><strong>Empleados de tiempo completo:</strong> <xsl:value-of select="$deptFullTime"/> de <xsl:value-of select="$deptTotal"/></p>
                                <p><strong>Porcentaje:</strong> 
                                    <span class="average-value">
                                        <xsl:value-of select="format-number(($deptFullTime div $deptTotal) * 100, '##.#')"/>%
                                    </span>
                                </p>
                            </div>
                            
                            <ul>
                                <xsl:for-each select="employee[contract_type='tiempo_completo']">
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
                                                    <xsl:value-of select="position"/>
                                                </span>
                                            </div>
                                            <div class="employee-salary">
                                                $<xsl:value-of select="format-number(salary, '#,###')"/>
                                            </div>
                                        </div>
                                    </li>
                                </xsl:for-each>
                            </ul>
                        </div>
                    </xsl:if>
                </xsl:for-each>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
