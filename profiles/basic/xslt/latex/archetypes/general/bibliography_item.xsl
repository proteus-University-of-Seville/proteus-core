<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : bibliography_item.xsl                                    -->
<!-- Content : PROTEUS LaTeX XSLT for bibliography item                 -->
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
       The bibliography-item template has priority="2" to avoid being
       overridden by the glossary-item template, which is its superclass.
  -->
  <!-- ================================================================ -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' bibliography-item ')]"
    name="bibliography_item_template"
    priority="2"
  >
    <!-- [name] authors. details. -->
    <xsl:text>&#10;</xsl:text>
    <xsl:call-template name="anchor"/>
    <xsl:text>\textbf{[</xsl:text>
    <xsl:call-template name="tex">
      <xsl:with-param name="text" select="properties/*[@name=':Proteus-name']"/>
    </xsl:call-template>
    <xsl:text>]} </xsl:text>
    <xsl:call-template name="tex">
      <xsl:with-param name="text" select="properties/*[@name='publication_authors']"/>
    </xsl:call-template>
    <xsl:text>. </xsl:text>
    <xsl:call-template name="generate_markdown">
      <xsl:with-param name="content" select="properties/*[@name='publication_details']"/>
    </xsl:call-template>
    <xsl:text>.\par&#10;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
