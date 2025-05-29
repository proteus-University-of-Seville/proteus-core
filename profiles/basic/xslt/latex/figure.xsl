<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:proteus="http://proteus.us.es"
    xmlns:proteus-utils="http://proteus.us.es/utils"
    exclude-result-prefixes="proteus proteus-utils">
    
    <xsl:template match="object[contains(@classes,'figure')]"> 
        <xsl:text>
\begin{figure}[h]
    \centering
</xsl:text>
        
        <!-- Get file name with extension -->
        <xsl:variable name="figure_path" select="properties/*[@name='file']"/>
        
        <!-- Get image width percentage, default to 50% -->
        <xsl:variable name="image_width">
            <xsl:choose>
                <xsl:when test="properties/*[@name='width']">
                    <xsl:value-of select="concat(properties/*[@name='width'], 'mm')"/>
                </xsl:when>
                <xsl:otherwise>50mm</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        
        <!-- Include LaTeX figure path -->
        <xsl:text>
    \includegraphics[width=</xsl:text>
        <xsl:value-of select="$image_width"/>
        <xsl:text>]{</xsl:text>
        <xsl:value-of select="concat('assets:///', $figure_path)" disable-output-escaping="no"/>
        <xsl:text>}
</xsl:text>
        
        <!-- Generate figure caption -->
        <xsl:if test="properties/*[@name='description']">
            <xsl:text>
    \caption{</xsl:text>
            <xsl:value-of select="properties/*[@name='description']"/>
            <xsl:text>}
</xsl:text>
        </xsl:if>
        
        <xsl:text>
    \label{fig:</xsl:text>
        <xsl:value-of select="@id"/>
        <xsl:text>}
\end{figure}
</xsl:text>
    </xsl:template>
    
</xsl:stylesheet>
