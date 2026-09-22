<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================ -->
<!-- File    : any_archetype.xsl                                      -->
<!-- Content : PROTEUS default XSLT for any archetype                 -->
<!-- Author  : Amador Durán Toro                                      -->
<!-- Date    : 2026/09/20                                             -->
<!-- Version : 2.0                                                    -->
<!-- ================================================================ -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <!-- ================================================================ -->
  <!-- NOTE
       This is the default template for any archetype. It matches any
       object of any archetype with the lowest priority, i.e., it will
       be overridden by any other template that matches a specific
       archetype.
  -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!-- any archetype template                                             -->
  <!-- ================================================================== -->

  <xsl:template
    match="object"
    priority="-1"
    name="any_archetype_template"
  >
    <xsl:call-template name="generate_table"/>
  </xsl:template>

</xsl:stylesheet>
