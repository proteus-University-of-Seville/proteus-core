<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : cover.xsl                                      -->
<!-- Content : PROTEUS LaTeX XSLT for the document cover      -->
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
  <!-- current() is the document object -->
  <xsl:template name="document_cover">
    <xsl:text>\begin{titlepage}&#10;\centering&#10;</xsl:text>
    <xsl:call-template name="anchor"/>
    <xsl:text>&#10;</xsl:text>

    <!-- Project name -->
    <xsl:text>{\Large </xsl:text>
    <xsl:call-template name="label"><xsl:with-param name="key" select="'xslt.project'"/></xsl:call-template>
    <xsl:text> </xsl:text>
    <xsl:call-template name="tex">
      <xsl:with-param name="text" select="parent::*/parent::*/properties/stringProperty[@name=':Proteus-name']"/>
    </xsl:call-template>
    <xsl:text>\par}&#10;\vspace{3cm}&#10;</xsl:text>

    <!-- Logo -->
    <xsl:text>\includegraphics[width=0.35\linewidth]{resources/images/logo_us.png}\par&#10;\vspace{2cm}&#10;</xsl:text>

    <!-- Document name, version and date -->
    <xsl:text>{\Huge\bfseries </xsl:text>
    <xsl:call-template name="tex"><xsl:with-param name="text" select="properties/*[@name=':Proteus-name']"/></xsl:call-template>
    <xsl:text>\par}&#10;\vspace{1.5cm}&#10;{\large </xsl:text>
    <xsl:call-template name="label"><xsl:with-param name="key" select="'archetype.prop_name.version'"/></xsl:call-template>
    <xsl:text> </xsl:text>
    <xsl:call-template name="tex"><xsl:with-param name="text" select="properties/*[@name='version']"/></xsl:call-template>
    <xsl:text>\par </xsl:text>
    <xsl:call-template name="label"><xsl:with-param name="key" select="'archetype.prop_name.date'"/></xsl:call-template>
    <xsl:text> </xsl:text>
    <xsl:call-template name="tex"><xsl:with-param name="text" select="properties/*[@name=':Proteus-date']"/></xsl:call-template>
    <xsl:text>\par}&#10;\vfill&#10;</xsl:text>

    <!-- Prepared for / prepared by -->
    <xsl:for-each select="properties/traceProperty[@name='prepared-for' or @name='prepared-by']">
      <xsl:text>\textbf{</xsl:text>
      <xsl:call-template name="label"><xsl:with-param name="key" select="concat('archetype.prop_name.', @name)"/></xsl:call-template>
      <xsl:text>:}\par&#10;</xsl:text>
      <xsl:choose>
        <xsl:when test="trace">
          <xsl:apply-templates select="." mode="paragraph"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>\ProteusTBD{?}\par&#10;</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:text>\medskip&#10;</xsl:text>
    </xsl:for-each>

    <xsl:text>\end{titlepage}&#10;&#10;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
