<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : general_requirement.xsl                                           -->
<!-- Content : PROTEUS default XSLT for requirements archetypes                  -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/09/23                                               -->
<!-- Version : 1.0                                                      -->
<!-- ================================================================== -->

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
       This template has priority="1" to avoid being overridden by
       templates of potential subclasses. Subclasses should have their own
       templates with higher priority, and they should call the superclass
       template by name if they want to reuse it.
  -->
  <!-- ================================================================== -->

  <!--
    Uncomment and modify this template as needed. The default behavior for
    all Proteus objects is generating a table.
  -->

  <!-- ================================================================== -->
  <!-- general-requirement template                                              -->
  <!-- ================================================================== -->

  <!--
  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' general-requirement ')]"
    name="general_requirement_template"
    priority="1"
  >
    <xsl:call-template name="generate_table"/>

  </xsl:template>
  -->

</xsl:stylesheet>
