<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : utilities.xsl                                  -->
<!-- Content : PROTEUS LaTeX XSLT utilities                   -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/10/07                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
  exclude-result-prefixes="proteus proteus-utils"
>
  <!-- ============================================= -->
  <!-- tex template: escaped plain text              -->
  <!-- ============================================= -->

  <xsl:template name="tex">
    <xsl:param name="text" select="string(.)"/>
    <xsl:value-of select="proteus-utils:latex_escape(string($text))"/>
  </xsl:template>

  <!-- ============================================= -->
  <!-- label template: escaped localized text        -->
  <!-- ============================================= -->

  <xsl:template name="label">
    <xsl:param name="key"/>
    <xsl:value-of select="proteus-utils:latex_escape(proteus-utils:i18n($key))"/>
  </xsl:template>

  <!-- ============================================= -->
  <!-- generate_markdown template                    -->
  <!-- ============================================= -->

  <!-- Glossary items are linked to their definitions -->
  <xsl:template name="generate_markdown">
    <xsl:param name="content" select="string(.)"/>
    <xsl:param name="glossary-items-highlight" select="true()"/>
    <xsl:value-of select="proteus-utils:markdown_to_latex(string($content), $glossary-items-highlight)"/>
  </xsl:template>

  <!-- ============================================= -->
  <!-- anchor template: hyperlink target of an object -->
  <!-- ============================================= -->

  <xsl:template name="anchor">
    <xsl:param name="id" select="@id"/>
    <xsl:text>\ProteusAnchor{</xsl:text>
    <xsl:value-of select="$id"/>
    <xsl:text>}</xsl:text>
  </xsl:template>

  <!-- ============================================= -->
  <!-- tbd template                                  -->
  <!-- ============================================= -->

  <xsl:template name="tbd">
    <xsl:param name="key" select="'xslt.tbd_expanded'"/>
    <xsl:text>\ProteusTBD{</xsl:text>
    <xsl:call-template name="label"><xsl:with-param name="key" select="$key"/></xsl:call-template>
    <xsl:text>}</xsl:text>
  </xsl:template>

  <!-- ============================================= -->
  <!-- image_width template                          -->
  <!-- ============================================= -->

  <!-- Fraction of \linewidth from a width percentage property -->
  <xsl:template name="image_width">
    <xsl:param name="width"/>
    <xsl:choose>
      <xsl:when test="number($width) > 0"><xsl:value-of select="number($width) div 100"/></xsl:when>
      <xsl:otherwise>0.5</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ============================================= -->
  <!-- generate_property_row template                -->
  <!-- ============================================= -->

  <!-- current() is the property element being processed.    -->
  <!-- 'tbd' is considered as having no content, it is shown -->
  <!-- only if it included.                                 -->

  <xsl:template name="generate_property_row">
    <xsl:param name="label" select="proteus-utils:i18n(concat('archetype.prop_name.', current()/@name))"/>
    <xsl:param name="included" select="false()"/>
    <xsl:param name="alternative"/>

    <xsl:variable name="hasContent" select="(string-length(current()//text()) > 0) and (normalize-space(current()) != 'tbd')"/>
    <xsl:variable name="hasChildren" select="boolean(current()/*)"/>

    <xsl:if test="$hasContent or $hasChildren or $included">
      <xsl:value-of select="proteus-utils:latex_escape(string($label))"/>
      <xsl:text> &amp; </xsl:text>
      <xsl:choose>
        <xsl:when test="(not($hasContent) and not($hasChildren)) or normalize-space(current()) = 'tbd'">
          <xsl:call-template name="tbd"/>
        </xsl:when>
        <xsl:when test="$alternative">
          <xsl:call-template name="tex"><xsl:with-param name="text" select="$alternative"/></xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates select="current()"/>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:text> \\ \hline&#10;</xsl:text>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>
