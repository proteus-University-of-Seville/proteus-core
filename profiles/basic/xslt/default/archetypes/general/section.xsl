<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : section.xsl                                    -->
<!-- Content : PROTEUS default XSLT for section               -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/14                                     -->
<!-- Version : 2.0                                            -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
>
  <!-- ================================================================== -->
  <!-- NOTE:                                                              -->
  <!-- match expression should be object[ends-with(@classes,'section')]   -->
  <!-- That is, to check if an object is of a given class we should use:  -->
  <!--    object[contains(@classes,class_name)]                           -->
  <!-- And to check if an object is of a given final class:               -->
  <!--    object[ends-with(@classes,class_name)]                          -->
  <!-- The problem is that XSLT 1.0 does not include ends-with.           -->
  <!-- In this case, object[@classes='section'] is kept to avoid matching -->
  <!-- with appendix objects, which is a subclass of section.             -->
  <!-- ================================================================== -->

  <!-- ============================================= -->
  <!-- section template                              -->
  <!-- ============================================= -->

  <xsl:template match="object[@classes='section']">
    <!-- Nesting level -->
    <xsl:param name="nesting_level" select="1"/>
    <xsl:param name="previous_index" select="''"/>

    <div id="{@id}" data-proteus-id="{@id}">

      <!-- Calculate the normalized header level for <h> tags -->
      <xsl:variable name="header_level">
        <xsl:choose>
          <xsl:when test="$nesting_level > 6">6</xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="$nesting_level"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>

      <!-- Calculate section index with respect to its parent -->
      <xsl:variable name="section_index">
        <xsl:number level="single" count="object[@classes='section']" />
      </xsl:variable>

      <!-- Build the current index -->
      <xsl:variable name="current_index">
        <xsl:value-of select="$previous_index"/>

        <xsl:choose>
          <xsl:when test="$previous_index">
            <xsl:text>.</xsl:text>
          </xsl:when>
        </xsl:choose>

        <xsl:value-of select="$section_index"/>
      </xsl:variable>

      <!-- Get section title -->
      <xsl:variable name="title" select="properties/*[@name=':Proteus-name']"/>

      <!-- Generate header element -->
      <xsl:element name="h{$header_level}">
        <xsl:value-of select="$current_index"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="$title"/>
      </xsl:element>

      <!-- Apply templates to all section children -->
      <xsl:apply-templates select="children/object">
        <!-- Provide nesting level context to children -->
        <xsl:with-param name="nesting_level" select="$nesting_level + 1"/>
        <xsl:with-param name="previous_index" select="$current_index"/>
      </xsl:apply-templates>

    </div>
  </xsl:template>

  <!-- ============================================= -->
  <!-- section template in "toc" mode                -->
  <!-- ============================================= -->

  <!-- A <ul> parent element is assumed              -->

  <xsl:template match="object[@classes='section']" mode="toc">
    <xsl:param name="previous_index" select="''"/>

    <!-- Calculate section index with respect to its parent -->
    <xsl:variable name="section_index">
      <xsl:number level="single" count="object[@classes='section']" />
    </xsl:variable>

    <!-- Build the current index -->
    <xsl:variable name="current_index">
      <xsl:value-of select="$previous_index"/>

      <xsl:choose>
        <xsl:when test="$previous_index">
          <xsl:text>.</xsl:text>
        </xsl:when>
      </xsl:choose>

      <xsl:value-of select="$section_index"/>
    </xsl:variable>

    <!-- Get section title -->
    <xsl:variable name="title" select="properties/stringProperty[@name=':Proteus-name']"/>

    <!-- Generate TOC item element -->
    <li>
      <xsl:value-of select="$current_index"/>
      <xsl:text> </xsl:text>
      <a href="#{@id}">
        <xsl:value-of select="$title"/>
      </a>
    </li>

    <!-- Generate TOC items for child sections (if any) -->
    <xsl:if test="children/object[@classes='section']">
      <ul class="toc_list">
        <xsl:apply-templates select="children/object[@classes='section']" mode="toc">
          <xsl:with-param name="previous_index" select="$current_index"/>
        </xsl:apply-templates>
      </ul>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>