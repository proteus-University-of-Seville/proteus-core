<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : appendix.xsl                                   -->
<!-- Content : PROTEUS default XSLT for appendix (section)    -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/17                                     -->
<!-- Version : 2.0                                            -->
<!-- ======================================================== -->

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
       The appendix template has priority="2" to avoid being overridden by
       the section template, which is its superclass.
  -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!-- appendix template                                                  -->
  <!-- ================================================================== -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' appendix ')]"
    name="appendix_template"
    priority="2"
  >
    <!-- Nesting level -->
    <xsl:param name="nesting_level" select="1"/>

    <div id="{@id}" data-proteus-id="{@id}">

      <!-- Calculate appendix index with respect to its parent-->
      <xsl:variable name="appendix_index">
        <xsl:number
          format="A"
          level="single"
          count="object[contains(concat(' ', normalize-space(@classes), ' '),' appendix ')]"
        />
      </xsl:variable>

      <!-- Get appendix title -->
      <xsl:variable name="title" select="properties/stringProperty[@name=':Proteus-name']"/>

      <!-- Generate header element -->
      <xsl:element name="h1">
        <xsl:value-of select="$appendix_index"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="$title"/>
      </xsl:element>

      <!-- Apply templates to all children -->
      <xsl:apply-templates select="children/object">
        <!-- Provide nesting level context to children -->
        <xsl:with-param name="nesting_level" select="$nesting_level + 1"/>
        <xsl:with-param name="previous_index" select="$appendix_index"/>
      </xsl:apply-templates>

    </div>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- appendix template in "toc" mode                                    -->
  <!-- ================================================================== -->

  <!-- A <ul> parent element is assumed              -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' appendix ')]"
    mode="toc"
    name="appendix_template_toc"
    priority="2"
  >
    <!-- Calculate appendix index with respect to its parent-->
    <!-- Should use ends-with     -->
    <xsl:variable name="appendix_index">
      <xsl:number
        format="A"
        level="single"
        count="object[contains(concat(' ', normalize-space(@classes), ' '),' appendix ')]"  />
    </xsl:variable>

    <!-- Get appendix title -->
    <xsl:variable name="title" select="properties/*[@name=':Proteus-name']"/>

    <!-- Generate TOC item element -->
    <li>
      <xsl:value-of select="$appendix_index"/>
      <xsl:text> </xsl:text>
      <a href="#{@id}">
        <xsl:apply-templates select="$title"/>
      </a>
    </li>

    <!-- Generate TOC items for child sections (if any) -->
    <xsl:variable
      name="children"
      select="children/object[contains(concat(' ', normalize-space(@classes), ' '), ' section ')]"
    />

    <xsl:if test="$children">
      <ul class="toc_list">
        <xsl:apply-templates select="$children" mode="toc">
          <xsl:with-param name="previous_index" select="$current_index"/>
        </xsl:apply-templates>
      </ul>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>