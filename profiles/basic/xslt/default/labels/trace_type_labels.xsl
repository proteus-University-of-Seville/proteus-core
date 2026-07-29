<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : trace_type_labels.xsl                          -->
<!-- Content : PROTEUS trace type labels XSLT file            -->
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

  <!-- PROTEUS trace types dictionary -->
  <xsl:variable name="trace_types_dictionary">
    <label key=":Proteus-affected"><xsl:value-of select="$proteus:lang_trace_type_proteus_affected"/></label>
    <label key=":Proteus-author"><xsl:value-of select="$proteus:lang_trace_type_proteus_author"/></label>
    <label key=":Proteus-dependency"><xsl:value-of select="$proteus:lang_trace_type_proteus_dependency"/></label>
    <label key=":Proteus-information-source"><xsl:value-of select="$proteus:lang_trace_type_proteus_information_source"/></label>
    <label key=":Proteus-works-for"><xsl:value-of select="$proteus:lang_trace_type_proteus_works_for"/></label>
  </xsl:variable>

  <!-- This is needed because of limitations of XSLT 1.0 -->
  <!-- Note the use of the node-set() extension function -->
  <!-- Usage: <xsl:value-of select="$trace-types/label[@key=@name])"/> -->
  <xsl:variable name="trace_types" select="exsl:node-set($trace_types_dictionary)"/>

</xsl:stylesheet>

