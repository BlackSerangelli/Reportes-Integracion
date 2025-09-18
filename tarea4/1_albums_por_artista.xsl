<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" indent="yes" encoding="UTF-8"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Catálogo de Música - Álbumes por Artista</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
                    .artista { margin-bottom: 30px; border: 2px solid #ecf0f1; border-radius: 8px; padding: 15px; }
                    .artista-header { background: linear-gradient(135deg, #3498db, #2980b9); color: white; padding: 15px; border-radius: 5px; margin-bottom: 15px; }
                    .artista-nombre { font-size: 24px; font-weight: bold; margin: 0; }
                    .artista-pais { font-size: 14px; opacity: 0.9; margin: 5px 0 0 0; }
                    .album { background: #f8f9fa; border-left: 4px solid #3498db; padding: 10px 15px; margin: 10px 0; border-radius: 0 5px 5px 0; }
                    .album-titulo { font-weight: bold; color: #2c3e50; font-size: 18px; }
                    .album-info { color: #7f8c8d; font-size: 14px; margin-top: 5px; }
                    .year { background: #e74c3c; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
                    .genre { background: #27ae60; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 10px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎵 Catálogo de Música - Álbumes por Artista</h1>
                    
                    <xsl:for-each select="catalogo/artista">
                        <div class="artista">
                            <div class="artista-header">
                                <h2 class="artista-nombre">
                                    <xsl:value-of select="@nombre"/>
                                </h2>
                                <p class="artista-pais">
                                    🌍 País de origen: <xsl:value-of select="@pais"/>
                                </p>
                            </div>
                            
                            <xsl:for-each select="album">
                                <div class="album">
                                    <div class="album-titulo">
                                        📀 <xsl:value-of select="@titulo"/>
                                    </div>
                                    <div class="album-info">
                                        <span class="year"><xsl:value-of select="@year"/></span>
                                        <span class="genre"><xsl:value-of select="@genero"/></span>
                                    </div>
                                </div>
                            </xsl:for-each>
                        </div>
                    </xsl:for-each>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
