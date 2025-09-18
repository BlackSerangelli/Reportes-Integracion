<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" indent="yes" encoding="UTF-8"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Catálogo de Música - Solo Sencillos</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #9b59b6; padding-bottom: 10px; }
                    .album-section { margin-bottom: 25px; border: 2px solid #ecf0f1; border-radius: 8px; overflow: hidden; }
                    .album-header { background: linear-gradient(135deg, #9b59b6, #8e44ad); color: white; padding: 15px; }
                    .album-titulo { font-size: 18px; font-weight: bold; margin: 0; }
                    .album-info { font-size: 14px; opacity: 0.9; margin: 5px 0 0 0; }
                    .singles-list { padding: 15px; }
                    .single-item { background: #f8f9fa; border-left: 4px solid #9b59b6; padding: 12px 15px; margin: 8px 0; border-radius: 0 5px 5px 0; display: flex; justify-content: space-between; align-items: center; }
                    .single-item:hover { background: #e8f5e8; border-left-color: #27ae60; }
                    .single-titulo { font-weight: bold; color: #2c3e50; font-size: 16px; }
                    .single-duracion { background: #27ae60; color: white; padding: 4px 12px; border-radius: 15px; font-family: 'Courier New', monospace; font-weight: bold; }
                    .no-singles { text-align: center; padding: 20px; color: #7f8c8d; font-style: italic; }
                    .singles-count { background: #e74c3c; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎵 Catálogo de Música - Solo Sencillos</h1>
                    
                    <xsl:for-each select="catalogo/artista">
                        <xsl:for-each select="album">
                            <!-- Solo mostrar álbumes que tengan al menos un sencillo -->
                            <xsl:if test="cancion[@single='true']">
                                <div class="album-section">
                                    <div class="album-header">
                                        <h2 class="album-titulo">
                                            📀 <xsl:value-of select="@titulo"/>
                                            <span class="singles-count">
                                                <xsl:value-of select="count(cancion[@single='true'])"/> sencillo(s)
                                            </span>
                                        </h2>
                                        <p class="album-info">
                                            🎤 <xsl:value-of select="../@nombre"/> • 
                                            📅 <xsl:value-of select="@year"/> • 
                                            🎼 <xsl:value-of select="@genero"/>
                                        </p>
                                    </div>
                                    
                                    <div class="singles-list">
                                        <xsl:for-each select="cancion[@single='true']">
                                            <div class="single-item">
                                                <div class="single-titulo">
                                                    ⭐ <xsl:value-of select="@titulo"/>
                                                </div>
                                                <div class="single-duracion">
                                                    <xsl:value-of select="@duracion"/>
                                                </div>
                                            </div>
                                        </xsl:for-each>
                                    </div>
                                </div>
                            </xsl:if>
                        </xsl:for-each>
                    </xsl:for-each>
                    
                    <!-- Sección de resumen -->
                    <div class="album-section">
                        <div class="album-header">
                            <h2 class="album-titulo">📊 Resumen de Sencillos</h2>
                        </div>
                        <div class="singles-list">
                            <div class="single-item">
                                <div class="single-titulo">
                                    🔢 Total de sencillos en el catálogo:
                                </div>
                                <div class="single-duracion">
                                    <xsl:value-of select="count(//cancion[@single='true'])"/>
                                </div>
                            </div>
                            <div class="single-item">
                                <div class="single-titulo">
                                    📀 Álbumes con sencillos:
                                </div>
                                <div class="single-duracion">
                                    <xsl:value-of select="count(//album[cancion[@single='true']])"/>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
