<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : appendix.xsl                                             -->
<!-- Content : PROTEUS LaTeX XSLT for appendix                          -->
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
       The appendix template has priority="2" to avoid being overridden by
       the section template, which is its superclass. \appendix is written
       before the first appendix of the document, so LaTeX numbers
       appendices with letters. Appendices can only be placed directly in
       a document; sections after an appendix would also be lettered.
  -->
  <!-- ================================================================ -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' appendix ')]"
    name="appendix_template"
    priority="2"
  >
    <xsl:param name="nesting_level" select="1"/>

    <xsl:if test="not(preceding-sibling::object[contains(concat(' ', normalize-space(@classes), ' '),' appendix ')])">
      <xsl:text>&#10;\appendix&#10;</xsl:text>
    </xsl:if>

    <xsl:call-template name="section_template">
      <xsl:with-param name="nesting_level" select="$nesting_level"/>
    </xsl:call-template>
  </xsl:template>

</xsl:stylesheet>
