<?xml version="1.0" encoding="utf-8"?>

<!-- =================================================================== -->
<!-- File    : comment.xsl                                               -->
<!-- Content : PROTEUS default XSLT for comment (paragraph)              -->
<!-- Author  : Amador Durán Toro                                         -->
<!-- Date    : 2026/09/18                                                -->
<!-- Version : 2.0                                                       -->
<!-- =================================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <!-- ================================================================ -->
  <!-- NOTE #1
       match expression gets rid of leading and trailing spaces in the
       @classes attribute, and adds a space at the beginning and end of
       the class name to avoid matching substrings. This way, we can
       check if a class name is present in the @classes attribute by
       using contains().

       NOTE #2
       The comment template has priority="2" to avoid being overridden by
       the paragraph template, which is its superclass.
  -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!-- comment template                                                   -->
  <!-- ================================================================== -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' comment ')]"
    name="comment_template"
    priority="2"
  >
    <div id="{@id}" data-proteus-id="{@id}" class="comment">
      <xsl:call-template name="generate_markdown">
        <xsl:with-param name="content" select="properties/*[@name='text']"/>
      </xsl:call-template>
    </div>
  </xsl:template>

</xsl:stylesheet>