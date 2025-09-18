<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" indent="yes" encoding="UTF-8"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Catálogo de Música - Índice Alfabético de Artistas</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #f39c12; padding-bottom: 10px; }
                    .artist-section { margin-bottom: 30px; border: 2px solid #ecf0f1; border-radius: 8px; overflow: hidden; }
                    .artist-header { background: linear-gradient(135deg, #f39c12, #e67e22); color: white; padding: 15px; }
                    .artist-name { font-size: 24px; font-weight: bold; margin: 0; }
                    .artist-country { font-size: 14px; opacity: 0.9; margin: 5px 0 0 0; }
                    .albums-list { padding: 15px; }
                    .album-item { background: #f8f9fa; border-left: 4px solid #f39c12; padding: 12px 15px; margin: 8px 0; border-radius: 0 5px 5px 0; display: flex; justify-content: space-between; align-items: center; }
                    .album-item:hover { background: #fff3cd; border-left-color: #e67e22; }
                    .album-info { flex-grow: 1; }
                    .album-titulo { font-weight: bold; color: #2c3e50; font-size: 16px; margin-bottom: 5px; }
                    .album-genero { color: #7f8c8d; font-size: 14px; }
                    .album-year { background: #e74c3c; color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold; margin-left: 15px; }
                    .navigation { background: #34495e; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; }
                    .nav-link { color: #3498db; text-decoration: none; margin: 0 10px; font-weight: bold; }
                    .nav-link:hover { color: #2980b9; text-decoration: underline; }
                    .stats { background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; }
                    .stat-item { display: inline-block; margin: 0 20px; }
                    .stat-number { font-size: 24px; font-weight: bold; color: #2c3e50; }
                    .stat-label { font-size: 14px; color: #7f8c8d; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎵 Índice Alfabético de Artistas</h1>
                    
                    <!-- Estadísticas -->
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-number"><xsl:value-of select="count(catalogo/artista)"/></div>
                            <div class="stat-label">Artistas</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number"><xsl:value-of select="count(//album)"/></div>
                            <div class="stat-label">Álbumes</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number"><xsl:value-of select="count(//cancion)"/></div>
                            <div class="stat-label">Canciones</div>
                        </div>
                    </div>
                    
                    <!-- Navegación alfabética -->
                    <div class="navigation">
                        <strong>Ir a artista:</strong>
                        <xsl:for-each select="catalogo/artista">
                            <xsl:sort select="@nombre"/>
                            <a class="nav-link" href="#{generate-id(.)}">
                                <xsl:value-of select="@nombre"/>
                            </a>
                        </xsl:for-each>
                    </div>
                    
                    <!-- Lista de artistas ordenada alfabéticamente -->
                    <xsl:for-each select="catalogo/artista">
                        <xsl:sort select="@nombre"/>
                        <div class="artist-section" id="{generate-id(.)}">
                            <div class="artist-header">
                                <h2 class="artist-name">
                                    🎤 <xsl:value-of select="@nombre"/>
                                </h2>
                                <p class="artist-country">
                                    🌍 <xsl:value-of select="@pais"/> • 
                                    📀 <xsl:value-of select="count(album)"/> álbum(es)
                                </p>
                            </div>
                            
                            <div class="albums-list">
                                <!-- Álbumes ordenados por año de lanzamiento -->
                                <xsl:for-each select="album">
                                    <xsl:sort select="@year" data-type="number"/>
                                    <div class="album-item">
                                        <div class="album-info">
                                            <div class="album-titulo">
                                                📀 <xsl:value-of select="@titulo"/>
                                            </div>
                                            <div class="album-genero">
                                                🎼 <xsl:value-of select="@genero"/> • 
                                                🎵 <xsl:value-of select="count(cancion)"/> canción(es)
                                            </div>
                                        </div>
                                        <div class="album-year">
                                            <xsl:value-of select="@year"/>
                                        </div>
                                    </div>
                                </xsl:for-each>
                            </div>
                        </div>
                    </xsl:for-each>
                    
                    <!-- Pie de página con información adicional -->
                    <div class="stats">
                        <p><strong>Nota:</strong> Los álbumes están ordenados cronológicamente por año de lanzamiento dentro de cada artista.</p>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
