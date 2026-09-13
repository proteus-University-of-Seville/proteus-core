<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : any_archetype.xsl                              -->
<!-- Content : PROTEUS default XSLT for any archetype         -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/09                                     -->
<!-- Version : 2.0                                            -->
<!-- ======================================================== -->

<!-- ======================================================== -->
<!-- exclude-result-prefixes="proteus" must be set in all     -->
<!-- files to avoid xmlsn:proteus="." to appear in HTML tags. -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
  exclude-result-prefixes="proteus proteus-utils"
>
  <!-- Match any object of any archetype -->
  <xsl:template match="object">
    <xsl:call-template name="generate_table"/>
  </xsl:template>

</xsl:stylesheet>
