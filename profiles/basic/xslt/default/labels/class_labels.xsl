<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : class_labels.xsl                               -->
<!-- Content : PROTEUS class labels XSLT file                 -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/13                                     -->
<!-- Version : 2.0                                            -->
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

  <!-- PROTEUS class labels dictionary -->
  <xsl:variable name="class_labels_dictionary">
    <label key="organization"><xsl:value-of select="$proteus:lang_organization"/></label>
    <label key="stakeholder"><xsl:value-of select="$proteus:lang_stakeholder"/></label>
  </xsl:variable>

  <!-- This is needed because of limitations of XSLT 1.0 -->
  <!-- Note the use of the node-set() extension function -->
  <!-- Usage: <xsl:value-of select="$class_labels/label[@key=@name])"/> -->
  <xsl:variable name="class_labels" select="exsl:node-set($class_labels_dictionary)"/>

</xsl:stylesheet>

