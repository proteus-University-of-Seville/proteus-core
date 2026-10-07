<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : symbolic_link.xsl                                        -->
<!-- Content : PROTEUS LaTeX XSLT for symbolic link                     -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/10/07                                               -->
<!-- Version : 1.0                                                      -->
<!-- ================================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
  exclude-result-prefixes="proteus proteus-utils"
>
  <!-- ================================================================ -->
  <!-- NOTE
       The linked objects are rendered again inside a proteuslink
       environment (see proteus.sty), which disables \ProteusLabel and
       \ProteusAnchor so that labels are not defined twice. It is an
       indented block with a title, not a box, because the property cards
       (long tables) cannot be placed inside boxes.
  -->
  <!-- ================================================================ -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' symbolic-link ')]"
    name="symbolic_link_template"
    priority="1"
  >
    <xsl:for-each select="properties/*[@name='link']/trace">
      <xsl:variable name="target_object" select="//object[@id = current()/@target]" />

      <xsl:if test="$target_object">
        <xsl:text>&#10;\begin{proteuslink}{</xsl:text>
        <xsl:call-template name="label">
          <xsl:with-param name="key" select="'xslt.symlink_tooltip'"/>
        </xsl:call-template>
        <xsl:text>}&#10;</xsl:text>
        <xsl:apply-templates select="$target_object" />
        <xsl:text>\end{proteuslink}&#10;</xsl:text>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

</xsl:stylesheet>
