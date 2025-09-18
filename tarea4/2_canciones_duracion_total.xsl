<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" indent="yes" encoding="UTF-8"/>
    
    <!-- Template para convertir duración MM:SS a segundos -->
    <xsl:template name="duracion-a-segundos">
        <xsl:param name="duracion"/>
        <xsl:variable name="minutos" select="substring-before($duracion, ':')"/>
        <xsl:variable name="segundos" select="substring-after($duracion, ':')"/>
        <xsl:value-of select="number($minutos) * 60 + number($segundos)"/>
    </xsl:template>
    
    <!-- Template para convertir segundos a formato MM:SS -->
    <xsl:template name="segundos-a-duracion">
        <xsl:param name="segundos"/>
        <xsl:variable name="min" select="floor($segundos div 60)"/>
        <xsl:variable name="sec" select="$segundos mod 60"/>
        <xsl:value-of select="$min"/>:<xsl:if test="$sec &lt; 10">0</xsl:if><xsl:value-of select="$sec"/>
    </xsl:template>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Catálogo de Música - Canciones con Duración Total</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }
                    .album-section { margin-bottom: 30px; border: 2px solid #ecf0f1; border-radius: 8px; overflow: hidden; }
                    .album-header { background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 15px; }
                    .album-titulo { font-size: 20px; font-weight: bold; margin: 0; }
                    .album-info { font-size: 14px; opacity: 0.9; margin: 5px 0 0 0; }
                    table { width: 100%; border-collapse: collapse; }
                    th { background: #34495e; color: white; padding: 12px; text-align: left; font-weight: bold; }
                    td { padding: 10px 12px; border-bottom: 1px solid #ecf0f1; }
                    tr:nth-child(even) { background-color: #f8f9fa; }
                    tr:hover { background-color: #e3f2fd; }
                    .duracion { font-family: 'Courier New', monospace; font-weight: bold; color: #27ae60; }
                    .total-row { background: linear-gradient(135deg, #f39c12, #e67e22) !important; color: white; font-weight: bold; }
                    .total-row td { border-top: 2px solid #d35400; }
                    .numero { text-align: center; color: #7f8c8d; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎵 Catálogo de Música - Canciones con Duración Total</h1>
                    
                    <xsl:for-each select="catalogo/artista">
                        <xsl:for-each select="album">
                            <div class="album-section">
                                <div class="album-header">
                                    <h2 class="album-titulo">
                                        📀 <xsl:value-of select="@titulo"/>
                                    </h2>
                                    <p class="album-info">
                                        🎤 <xsl:value-of select="../@nombre"/> • 
                                        📅 <xsl:value-of select="@year"/> • 
                                        🎼 <xsl:value-of select="@genero"/>
                                    </p>
                                </div>
                                
                                <table>
                                    <thead>
                                        <tr>
                                            <th width="50">#</th>
                                            <th>Título de la Canción</th>
                                            <th width="100">Duración</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <xsl:for-each select="cancion">
                                            <tr>
                                                <td class="numero"><xsl:value-of select="position()"/></td>
                                                <td>🎵 <xsl:value-of select="@titulo"/></td>
                                                <td class="duracion"><xsl:value-of select="@duracion"/></td>
                                            </tr>
                                        </xsl:for-each>
                                        
                                        <!-- Fila de duración total -->
                                        <tr class="total-row">
                                            <td></td>
                                            <td><strong>⏱️ DURACIÓN TOTAL DEL ÁLBUM</strong></td>
                                            <td class="duracion">
                                                <xsl:variable name="total-segundos">
                                                    <xsl:call-template name="sumar-duraciones">
                                                        <xsl:with-param name="canciones" select="cancion"/>
                                                        <xsl:with-param name="index" select="1"/>
                                                        <xsl:with-param name="total" select="0"/>
                                                    </xsl:call-template>
                                                </xsl:variable>
                                                <xsl:call-template name="segundos-a-duracion">
                                                    <xsl:with-param name="segundos" select="$total-segundos"/>
                                                </xsl:call-template>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </xsl:for-each>
                    </xsl:for-each>
                </div>
            </body>
        </html>
    </xsl:template>
    
    <!-- Template recursivo para sumar duraciones -->
    <xsl:template name="sumar-duraciones">
        <xsl:param name="canciones"/>
        <xsl:param name="index"/>
        <xsl:param name="total"/>
        
        <xsl:choose>
            <xsl:when test="$index &lt;= count($canciones)">
                <xsl:variable name="duracion-actual">
                    <xsl:call-template name="duracion-a-segundos">
                        <xsl:with-param name="duracion" select="$canciones[$index]/@duracion"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:call-template name="sumar-duraciones">
                    <xsl:with-param name="canciones" select="$canciones"/>
                    <xsl:with-param name="index" select="$index + 1"/>
                    <xsl:with-param name="total" select="$total + $duracion-actual"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$total"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
