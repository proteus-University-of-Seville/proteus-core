<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : glossary_item.xsl                                        -->
<!-- Content : PROTEUS LaTeX XSLT for glossary item                     -->
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
       The glossary-item template has priority="1" to avoid being
       overridden by the bibliography-item template, which is a subclass
       of glossary-item.
  -->
  <!-- ================================================================ -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' glossary-item ')]"
    name="glossary_item_template"
    priority="1"
  >
    <xsl:variable name="description" select="properties/*[@name='description']"/>
    <xsl:variable name="synonyms" select="properties/*[@name='synonyms']"/>
    <xsl:variable name="image_path" select="normalize-space(properties/*[@name='image'])"/>

    <!-- Name -->
    <xsl:text>&#10;</xsl:text>
    <xsl:call-template name="anchor"/>
    <xsl:text>\textbf{</xsl:text>
    <xsl:call-template name="tex">
      <xsl:with-param name="text" select="properties/*[@name=':Proteus-name']"/>
    </xsl:call-template>
    <xsl:text>:} </xsl:text>

    <!-- Description -->
    <xsl:choose>
      <xsl:when test="not(normalize-space($description))">
        <xsl:call-template name="tbd"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="generate_markdown">
          <xsl:with-param name="content" select="$description"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>

    <!-- Synonyms -->
    <xsl:if test="normalize-space($synonyms)">
      <xsl:text> \textit{</xsl:text>
      <xsl:call-template name="label">
        <xsl:with-param name="key" select="'archetype.prop_name.synonyms'"/>
      </xsl:call-template>
      <xsl:text>:} </xsl:text>
      <xsl:call-template name="tex">
        <xsl:with-param name="text" select="$synonyms"/>
      </xsl:call-template>
      <xsl:text>.</xsl:text>
    </xsl:if>

    <!-- Image -->
    <xsl:if test="$image_path">
      <xsl:text>\par{\centering </xsl:text>
      <xsl:apply-templates select="properties/*[@name='image']"/>
      <xsl:text>\par}</xsl:text>
    </xsl:if>

    <xsl:text>\par&#10;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
