<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : comment.xsl                                              -->
<!-- Content : PROTEUS LaTeX XSLT for comment                           -->
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
       The comment template has priority="2" to avoid being overridden by
       the paragraph template, which is its superclass. Comments are shown
       in a proteuscomment box (see proteus.sty).
  -->
  <!-- ================================================================ -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' comment ')]"
    name="comment_template"
    priority="2"
  >
    <xsl:text>&#10;\begin{proteuscomment}</xsl:text>
    <xsl:call-template name="anchor"/>
    <xsl:text>&#10;</xsl:text>
    <xsl:call-template name="generate_markdown">
      <xsl:with-param name="content" select="properties/*[@name='text']"/>
    </xsl:call-template>
    <xsl:text>&#10;\end{proteuscomment}&#10;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
