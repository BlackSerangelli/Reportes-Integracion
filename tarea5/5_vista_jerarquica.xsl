<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" doctype-public="-//W3C//DTD HTML 4.01//EN" doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Vista Jerárquica de la Empresa</title>
                <meta charset="UTF-8"/>
                <link rel="stylesheet" type="text/css" href="empleados.css"/>
            </head>
            <body>
                <h1>Estructura Jerárquica de la Empresa</h1>
                <p style="text-align: center; color: #7f8c8d; font-style: italic;">
                    Organización por departamentos con información detallada de empleados
                </p>
                
                <div class="hierarchy-container">
                    <!-- Iteramos por cada departamento -->
                    <xsl:for-each select="company/department">
                        <div class="hierarchy-department">
                            📁 <xsl:value-of select="@name"/>
                            <span style="float: right; font-size: 0.8em; font-weight: normal;">
                                <xsl:value-of select="count(employee)"/> empleado<xsl:if test="count(employee) > 1">s</xsl:if>
                            </span>
                        </div>
                        
                        <div class="hierarchy-employees">
                            <!-- Ordenamos empleados por posición (gerentes primero) y luego por nombre -->
                            <xsl:for-each select="employee">
                                <xsl:sort select="contains(position, 'Gerente') or contains(position, 'Director')" order="descending"/>
                                <xsl:sort select="first_name"/>
                                
                                <div class="hierarchy-employee">
                                    <div class="employee-info">
                                        <div>
                                            <span class="employee-name">
                                                👤 <xsl:value-of select="first_name"/>
                                                <xsl:text> </xsl:text>
                                                <xsl:value-of select="last_name"/>
                                            </span>
                                            <br/>
                                            <span class="employee-position">
                                                🏢 <xsl:value-of select="position"/>
                                            </span>
                                            <br/>
                                            <span class="employee-date">
                                                📅 Contratado: <xsl:value-of select="@hire_date"/>
                                            </span>
                                        </div>
                                        <div style="text-align: right;">
                                            <div class="employee-salary">
                                                💰 $<xsl:value-of select="format-number(salary, '#,###')"/>
                                            </div>
                                            <br/>
                                            <span>
                                                <xsl:attribute name="class">
                                                    contract-type <xsl:value-of select="contract_type"/>
                                                </xsl:attribute>
                                                <xsl:choose>
                                                    <xsl:when test="contract_type = 'tiempo_completo'">
                                                        ⏰ Tiempo Completo
                                                    </xsl:when>
                                                    <xsl:otherwise>
                                                        ⏳ Tiempo Parcial
                                                    </xsl:otherwise>
                                                </xsl:choose>
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </xsl:for-each>
                        </div>
                        
                        <!-- Resumen del departamento -->
                        <div class="average-info" style="margin: 20px 0 40px 20px;">
                            <h4>📊 Resumen de <xsl:value-of select="@name"/></h4>
                            <xsl:variable name="deptTotalSalary" select="sum(employee/salary)"/>
                            <xsl:variable name="deptEmployeeCount" select="count(employee)"/>
                            <xsl:variable name="deptAverageSalary" select="$deptTotalSalary div $deptEmployeeCount"/>
                            <xsl:variable name="fullTimeCount" select="count(employee[contract_type='tiempo_completo'])"/>
                            <xsl:variable name="partTimeCount" select="count(employee[contract_type='tiempo_parcial'])"/>
                            
                            <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
                                <div>
                                    <p><strong>👥 Total empleados:</strong> <xsl:value-of select="$deptEmployeeCount"/></p>
                                    <p><strong>⏰ Tiempo completo:</strong> <xsl:value-of select="$fullTimeCount"/></p>
                                    <p><strong>⏳ Tiempo parcial:</strong> <xsl:value-of select="$partTimeCount"/></p>
                                </div>
                                <div>
                                    <p><strong>💰 Nómina total:</strong> $<xsl:value-of select="format-number($deptTotalSalary, '#,###')"/></p>
                                    <p><strong>📈 Salario promedio:</strong> 
                                        <span class="average-value">$<xsl:value-of select="format-number($deptAverageSalary, '#,###')"/></span>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </xsl:for-each>
                </div>
                
                <h2>📈 Resumen Ejecutivo de la Empresa</h2>
                <div class="average-info">
                    <xsl:variable name="totalEmployees" select="count(company/department/employee)"/>
                    <xsl:variable name="totalDepartments" select="count(company/department)"/>
                    <xsl:variable name="totalSalary" select="sum(company/department/employee/salary)"/>
                    <xsl:variable name="overallAverage" select="$totalSalary div $totalEmployees"/>
                    <xsl:variable name="totalFullTime" select="count(company/department/employee[contract_type='tiempo_completo'])"/>
                    <xsl:variable name="totalPartTime" select="count(company/department/employee[contract_type='tiempo_parcial'])"/>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                        <div>
                            <h4>🏢 Estructura Organizacional</h4>
                            <p><strong>Departamentos:</strong> <xsl:value-of select="$totalDepartments"/></p>
                            <p><strong>Total empleados:</strong> <xsl:value-of select="$totalEmployees"/></p>
                            <p><strong>Promedio por depto:</strong> <xsl:value-of select="format-number($totalEmployees div $totalDepartments, '#.#')"/> empleados</p>
                        </div>
                        
                        <div>
                            <h4>💼 Tipos de Contrato</h4>
                            <p><strong>Tiempo completo:</strong> <xsl:value-of select="$totalFullTime"/> 
                                (<xsl:value-of select="format-number(($totalFullTime div $totalEmployees) * 100, '#.#')"/>%)
                            </p>
                            <p><strong>Tiempo parcial:</strong> <xsl:value-of select="$totalPartTime"/> 
                                (<xsl:value-of select="format-number(($totalPartTime div $totalEmployees) * 100, '#.#')"/>%)
                            </p>
                        </div>
                        
                        <div>
                            <h4>💰 Información Salarial</h4>
                            <p><strong>Nómina total:</strong> $<xsl:value-of select="format-number($totalSalary, '#,###')"/></p>
                            <p><strong>Salario promedio:</strong> 
                                <span class="average-value">$<xsl:value-of select="format-number($overallAverage, '#,###')"/></span>
                            </p>
                        </div>
                    </div>
                </div>
                
                <h3>🏆 Departamentos por Tamaño</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Departamento</th>
                            <th>Empleados</th>
                            <th>% del Total</th>
                            <th>Nómina</th>
                            <th>Salario Promedio</th>
                        </tr>
                    </thead>
                    <tbody>
                        <xsl:for-each select="company/department">
                            <xsl:sort select="count(employee)" order="descending"/>
                            
                            <xsl:variable name="deptEmployees" select="count(employee)"/>
                            <xsl:variable name="deptSalary" select="sum(employee/salary)"/>
                            <xsl:variable name="deptAverage" select="$deptSalary div $deptEmployees"/>
                            <xsl:variable name="totalEmp" select="count(../../department/employee)"/>
                            
                            <tr>
                                <td class="employee-name">
                                    <xsl:value-of select="@name"/>
                                </td>
                                <td style="text-align: center;">
                                    <xsl:value-of select="$deptEmployees"/>
                                </td>
                                <td style="text-align: center;">
                                    <xsl:value-of select="format-number(($deptEmployees div $totalEmp) * 100, '#.#')"/>%
                                </td>
                                <td class="employee-salary">
                                    $<xsl:value-of select="format-number($deptSalary, '#,###')"/>
                                </td>
                                <td class="average-value">
                                    $<xsl:value-of select="format-number($deptAverage, '#,###')"/>
                                </td>
                            </tr>
                        </xsl:for-each>
                    </tbody>
                </table>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
