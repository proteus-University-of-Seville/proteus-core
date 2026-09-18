<?xml version="1.0" encoding="utf-8"?>

<!-- ============================================================================ -->
<!-- File    : bibliography_item.xsl                                              -->
<!-- Content : PROTEUS default XSLT for bibliography items                        -->
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
       The bibliography-item template has priority="2" to avoid being 
       overridden by the glossary-item template, which is its superclass.
  -->
  <!-- ================================================================== -->

  <!-- ========================================================================== -->
  <!-- bibliography-item template                                                 -->
  <!-- ========================================================================== -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' bibliography-item ')]"
    name="bibliography_item_template"
    priority="2"
  >
    <div id="{@id}" class="bibliography_item" data-proteus-id="{@id}">
      <p>
        <!-- Generate bibliography item name -->
        <span class="bibliography_item_name">
          <xsl:value-of select="properties/*[@name=':Proteus-name']"/>
          <xsl:text>: </xsl:text>
        </span>

        <!-- Generate bibliography item description -->
        <xsl:variable name="description" select="properties/*[@name='description']"/>
        <xsl:variable name="nonempty_content" select="string-length(normalize-space($description)) > 0"/>

        <span class="bibliography_item_description">
          <xsl:call-template name="generate_markdown">
            <xsl:with-param name="content" select="$description"/>
          </xsl:call-template>
        </span>
      </p>
    </div>
  </xsl:template>

</xsl:stylesheet>