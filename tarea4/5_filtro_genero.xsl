<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" indent="yes" encoding="UTF-8"/>
    
    <!-- Parámetro para el género a filtrar (por defecto Rock) -->
    <xsl:param name="genero-filtro" select="'Rock'"/>
    
    <xsl:template match="/">
        <html>
            <head>
                <title>Catálogo de Música - Filtro por Género</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #2c3e50; text-align: center; border-bottom: 3px solid #1abc9c; padding-bottom: 10px; }
                    .filter-info { background: linear-gradient(135deg, #1abc9c, #16a085); color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; }
                    .filter-title { font-size: 20px; font-weight: bold; margin-bottom: 5px; }
                    .filter-description { font-size: 14px; opacity: 0.9; }
                    .genre-selector { background: #34495e; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; }
                    .genre-button { background: #3498db; color: white; padding: 8px 15px; margin: 0 5px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
                    .genre-button:hover { background: #2980b9; }
                    .genre-button.active { background: #e74c3c; }
                    .album-section { margin-bottom: 25px; border: 2px solid #ecf0f1; border-radius: 8px; overflow: hidden; }
                    .album-header { background: linear-gradient(135deg, #1abc9c, #16a085); color: white; padding: 15px; }
                    .album-titulo { font-size: 18px; font-weight: bold; margin: 0; }
                    .album-info { font-size: 14px; opacity: 0.9; margin: 5px 0 0 0; }
                    .songs-list { padding: 15px; }
                    .song-item { background: #f8f9fa; border-left: 4px solid #1abc9c; padding: 10px 15px; margin: 5px 0; border-radius: 0 5px 5px 0; display: flex; justify-content: space-between; align-items: center; }
                    .song-item:hover { background: #e8f8f5; }
                    .song-titulo { color: #2c3e50; }
                    .song-duracion { background: #27ae60; color: white; padding: 3px 10px; border-radius: 12px; font-family: 'Courier New', monospace; font-size: 12px; }
                    .single-badge { background: #e74c3c; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px; margin-left: 8px; }
                    .no-results { text-align: center; padding: 40px; color: #7f8c8d; }
                    .stats { background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; }
                    .stat-item { display: inline-block; margin: 0 15px; }
                    .stat-number { font-size: 20px; font-weight: bold; color: #2c3e50; }
                    .stat-label { font-size: 12px; color: #7f8c8d; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎵 Catálogo de Música - Filtro por Género</h1>
                    
                    <!-- Información del filtro actual -->
                    <div class="filter-info">
                        <div class="filter-title">
                            🎼 Género Seleccionado: <xsl:value-of select="$genero-filtro"/>
                        </div>
                        <div class="filter-description">
                            Mostrando solo los álbumes del género "<xsl:value-of select="$genero-filtro"/>"
                        </div>
                    </div>
                    
                    <!-- Selector de géneros disponibles -->
                    <div class="genre-selector">
                        <strong style="color: white; margin-right: 15px;">Géneros disponibles:</strong>
                        <xsl:for-each select="//album[not(@genero = preceding::album/@genero)]">
                            <xsl:sort select="@genero"/>
                            <span class="genre-button">
                                <xsl:if test="@genero = $genero-filtro">
                                    <xsl:attribute name="class">genre-button active</xsl:attribute>
                                </xsl:if>
                                <xsl:value-of select="@genero"/>
                            </span>
                        </xsl:for-each>
                    </div>
                    
                    <!-- Estadísticas del filtro -->
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-number">
                                <xsl:value-of select="count(//album[@genero = $genero-filtro])"/>
                            </div>
                            <div class="stat-label">Álbumes</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">
                                <xsl:value-of select="count(//album[@genero = $genero-filtro]/cancion)"/>
                            </div>
                            <div class="stat-label">Canciones</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">
                                <xsl:value-of select="count(//album[@genero = $genero-filtro]/cancion[@single='true'])"/>
                            </div>
                            <div class="stat-label">Sencillos</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">
                                <xsl:value-of select="count(//artista[album[@genero = $genero-filtro]])"/>
                            </div>
                            <div class="stat-label">Artistas</div>
                        </div>
                    </div>
                    
                    <!-- Lista de álbumes filtrados -->
                    <xsl:choose>
                        <xsl:when test="//album[@genero = $genero-filtro]">
                            <xsl:for-each select="catalogo/artista[album[@genero = $genero-filtro]]">
                                <xsl:for-each select="album[@genero = $genero-filtro]">
                                    <div class="album-section">
                                        <div class="album-header">
                                            <h2 class="album-titulo">
                                                📀 <xsl:value-of select="@titulo"/>
                                            </h2>
                                            <p class="album-info">
                                                🎤 <xsl:value-of select="../@nombre"/> 
                                                (<xsl:value-of select="../@pais"/>) • 
                                                📅 <xsl:value-of select="@year"/> • 
                                                🎵 <xsl:value-of select="count(cancion)"/> canción(es)
                                            </p>
                                        </div>
                                        
                                        <div class="songs-list">
                                            <xsl:for-each select="cancion">
                                                <div class="song-item">
                                                    <div class="song-titulo">
                                                        🎵 <xsl:value-of select="@titulo"/>
                                                        <xsl:if test="@single='true'">
                                                            <span class="single-badge">SINGLE</span>
                                                        </xsl:if>
                                                    </div>
                                                    <div class="song-duracion">
                                                        <xsl:value-of select="@duracion"/>
                                                    </div>
                                                </div>
                                            </xsl:for-each>
                                        </div>
                                    </div>
                                </xsl:for-each>
                            </xsl:for-each>
                        </xsl:when>
                        <xsl:otherwise>
                            <div class="no-results">
                                <h2>😔 No se encontraron álbumes</h2>
                                <p>No hay álbumes del género "<xsl:value-of select="$genero-filtro"/>" en el catálogo.</p>
                            </div>
                        </xsl:otherwise>
                    </xsl:choose>
                    
                    <!-- Instrucciones -->
                    <div class="stats">
                        <p><strong>💡 Instrucciones:</strong> Para cambiar el género, modifica el parámetro "genero-filtro" en el procesador XSLT.</p>
                        <p><strong>Ejemplo:</strong> genero-filtro="Pop" para mostrar solo álbumes de Pop.</p>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>
</xsl:stylesheet>
