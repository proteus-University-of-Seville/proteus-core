<?xml version="1.0" encoding="utf-8"?>
<!-- ================================================================== -->
<!-- File    : meeting.xsl                                              -->
<!-- Content : PROTEUS LaTeX XSLT for meetings                          -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/10/14                                               -->
<!-- Version : 1.0                                                      -->
<!-- ================================================================== -->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <!-- ================================================================ -->
  <!-- meeting template: the default property card, with the results    -->
  <!-- at the full width of the table (see generate_table)              -->
  <!-- ================================================================ -->
  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' meeting ')]"
    name="meeting_template"
    priority="1"
  >
    <xsl:call-template name="generate_table">
      <!-- The results are a text: they take the full width of the table -->
      <xsl:with-param name="wide_properties" select="',diagram,results,'"/>
    </xsl:call-template>
  </xsl:template>
</xsl:stylesheet>
