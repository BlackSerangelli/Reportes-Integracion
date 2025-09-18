<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Salario Promedio por Departamento</title>
                <meta charset="UTF-8"/>
                <link rel="stylesheet" type="text/css" href="empleados.css"/>
            </head>
            <body>
                <h1>Salario Promedio por Departamento</h1>
                
                <table>
                    <thead>
                        <tr>
                            <th>Departamento</th>
                            <th>Número de Empleados</th>
                            <th>Salario Total</th>
                            <th>Salario Promedio</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Iteramos por cada departamento -->
                        <xsl:for-each select="company/department">
                            <xsl:variable name="totalSalary" select="sum(employee/salary)"/>
                            <xsl:variable name="employeeCount" select="count(employee)"/>
                            <xsl:variable name="averageSalary" select="$totalSalary div $employeeCount"/>
                            
                            <tr>
                                <td class="employee-name">
                                    <xsl:value-of select="@name"/>
                                </td>
                                <td style="text-align: center;">
                                    <xsl:value-of select="$employeeCount"/>
                                </td>
                                <td class="employee-salary">
                                    $<xsl:value-of select="format-number($totalSalary, '#,###')"/>
                                </td>
                                <td class="average-value">
                                    $<xsl:value-of select="format-number($averageSalary, '#,###')"/>
                                </td>
                            </tr>
                        </xsl:for-each>
                    </tbody>
                </table>
                
                <div class="average-info">
                    <h3>Resumen General</h3>
                    <xsl:variable name="totalCompanySalary" select="sum(company/department/employee/salary)"/>
                    <xsl:variable name="totalEmployees" select="count(company/department/employee)"/>
                    <xsl:variable name="overallAverage" select="$totalCompanySalary div $totalEmployees"/>
                    
                    <p><strong>Total de empleados en la empresa:</strong> <xsl:value-of select="$totalEmployees"/></p>
                    <p><strong>Nómina total de la empresa:</strong> $<xsl:value-of select="format-number($totalCompanySalary, '#,###')"/></p>
                    <p><strong>Salario promedio general:</strong> 
                        <span class="average-value">$<xsl:value-of select="format-number($overallAverage, '#,###')"/></span>
                    </p>
                </div>
                
                <h2>Análisis Detallado por Departamento</h2>
                <ul>
                    <xsl:for-each select="company/department">
                        <xsl:variable name="totalSalary" select="sum(employee/salary)"/>
                        <xsl:variable name="employeeCount" select="count(employee)"/>
                        <xsl:variable name="averageSalary" select="$totalSalary div $employeeCount"/>
                        
                        <li class="average-info">
                            <div class="employee-info">
                                <div>
                                    <strong><xsl:value-of select="@name"/></strong>
                                    <br/>
                                    <span class="employee-position">
                                        <xsl:value-of select="$employeeCount"/> empleado<xsl:if test="$employeeCount > 1">s</xsl:if>
                                    </span>
                                </div>
                                <div class="average-value">
                                    Promedio: $<xsl:value-of select="format-number($averageSalary, '#,###')"/>
                                </div>
                            </div>
                        </li>
                    </xsl:for-each>
                </ul>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
