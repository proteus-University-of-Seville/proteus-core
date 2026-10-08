<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : paragraph.xsl                                            -->
<!-- Content : PROTEUS LaTeX XSLT for paragraph                         -->
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
  <!-- NOTE
       The paragraph template has priority="1" to avoid being overridden by
       the comment template, which is a subclass of paragraph.
  -->
  <!-- ================================================================ -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' paragraph ')]"
    name="paragraph_template"
    priority="1"
  >
    <xsl:variable name="content" select="properties/*[@name='text']"/>

    <xsl:text>&#10;</xsl:text>
    <xsl:call-template name="anchor"/>

    <xsl:choose>
      <xsl:when test="not(normalize-space($content))">
        <xsl:text>[</xsl:text>
        <xsl:call-template name="tbd">
          <xsl:with-param name="key" select="'xslt.empty_paragraph'"/>
        </xsl:call-template>
        <xsl:text>]</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="generate_markdown">
          <xsl:with-param name="content" select="$content"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>

    <xsl:text>\par&#10;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
