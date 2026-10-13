<?xml version="1.0" encoding="utf-8"?>
<!-- Minimal text-output (LaTeX) template used by test_render_service.py -->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <xsl:output method="text" encoding="utf-8"/>

  <xsl:template match="/">
    <xsl:text>\section{</xsl:text>
    <xsl:value-of select="proteus-utils:latex_escape(string(/project/properties/*[@name=':Proteus-name']))"/>
    <xsl:text>}&#10;</xsl:text>
    <xsl:value-of select="proteus-utils:markdown_to_latex('Price: **50%** &amp; more', false())"/>
  </xsl:template>
</xsl:stylesheet>
