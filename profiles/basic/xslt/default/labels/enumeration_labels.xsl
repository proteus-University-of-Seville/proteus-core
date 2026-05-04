<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : enumeration_labels.xsl                         -->
<!-- Content : PROTEUS enumeration labels XSLT file           -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/05/02                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->

<!-- ======================================================== -->
<!-- exclude-result-prefixes="proteus" must be set in all     -->
<!-- files to avoid xmlsn:proteus="." to appear in HTML tags. -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
  exclude-result-prefixes="proteus proteus-utils"
  extension-element-prefixes="exsl"
>

<!-- NOTE: that would not be necessary in XSLT 2.0,  -->
<!-- where variable names can be computed in runtime -->

  <!-- PROTEUS enumeration labels dictionary -->
  <xsl:variable name="enum_labels_dictionary">
      <label key="awaiting-qa"><xsl:value-of select="$proteus:lang_awaiting_qa"/></label>
      <label key="awaiting-validation"><xsl:value-of select="$proteus:lang_awaiting_validation"/></label>
      <label key="critical"><xsl:value-of select="$proteus:lang_critical"/></label>
      <label key="customer"><xsl:value-of select="$proteus:lang_customer"/></label>
      <label key="developer"><xsl:value-of select="$proteus:lang_developer"/></label>
      <label key="draft"><xsl:value-of select="$proteus:lang_draft"/></label>
      <label key="high"><xsl:value-of select="$proteus:lang_high"/></label>
      <label key="low"><xsl:value-of select="$proteus:lang_low"/></label>
      <label key="medium"><xsl:value-of select="$proteus:lang_medium"/></label>
      <label key="optional"><xsl:value-of select="$proteus:lang_optional"/></label>
      <label key="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></label>
      <label key="user"><xsl:value-of select="$proteus:lang_user"/></label>
      <label key="validated"><xsl:value-of select="$proteus:lang_validated"/></label>
  </xsl:variable>

  <!-- This is needed because of limitations of XSLT 1.0 -->
  <!-- Note the use of the node-set() extension function -->
  <xsl:variable name="enum_labels" select="exsl:node-set($enum_labels_dictionary)"/>

</xsl:stylesheet>

