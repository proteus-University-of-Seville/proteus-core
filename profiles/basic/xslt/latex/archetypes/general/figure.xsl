<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : figure.xsl                                               -->
<!-- Content : PROTEUS LaTeX XSLT for figure                            -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/10/07                                               -->
<!-- Version : 1.0                                                      -->
<!-- ================================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <!-- ================================================================ -->
  <!-- NOTE #1
       Figures are not floating ([H]), so they stay where they are in the
       document, as in the HTML view. LaTeX numbers them.

       NOTE #2
       Remote figures (url property) are written as
       \ProteusRemoteImage{width}{URL}, with the URL unescaped. The export
       strategies download the image and replace that command by
       \includegraphics (or by \ProteusMissingImage if the download fails),
       so it never reaches LaTeX.
  -->
  <!-- ================================================================ -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' figure ')]"
    name="figure_template"
    priority="1"
  >
    <xsl:variable name="figure_path" select="normalize-space(properties/*[@name='file'])"/>
    <xsl:variable name="figure_url" select="normalize-space(properties/*[@name='url'])"/>

    <xsl:text>&#10;\begin{figure}[H]&#10;\centering&#10;</xsl:text>

    <xsl:choose>
      <xsl:when test="$figure_path">
        <xsl:text>\includegraphics[width=</xsl:text>
        <xsl:call-template name="image_width">
          <xsl:with-param name="width" select="properties/*[@name='width']"/>
        </xsl:call-template>
        <xsl:text>\linewidth]{assets/</xsl:text>
        <xsl:value-of select="$figure_path"/>
        <xsl:text>}&#10;</xsl:text>
      </xsl:when>
      <xsl:when test="$figure_url">
        <!-- Replaced on export by the downloaded image (see proteus.sty) -->
        <xsl:text>\ProteusRemoteImage{</xsl:text>
        <xsl:call-template name="image_width">
          <xsl:with-param name="width" select="properties/*[@name='width']"/>
        </xsl:call-template>
        <xsl:text>}{</xsl:text>
        <xsl:value-of select="$figure_url"/>
        <xsl:text>}&#10;</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="tbd"/>
        <xsl:text>&#10;</xsl:text>
      </xsl:otherwise>
    </xsl:choose>

    <!-- Caption -->
    <xsl:text>\caption{</xsl:text>
    <xsl:call-template name="generate_markdown">
      <xsl:with-param name="content" select="properties/*[@name='description']"/>
    </xsl:call-template>
    <xsl:text>}\ProteusLabel{</xsl:text>
    <xsl:value-of select="@id"/>
    <xsl:text>}&#10;\end{figure}&#10;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
