<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : appendix.xsl                                   -->
<!-- Content : PROTEUS default XSLT for appendix (section)    -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/14                                     -->
<!-- Version : 2.0                                            -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
>

  <!-- =================================================================== -->
  <!-- NOTE:                                                               -->
  <!-- match expression should be object[ends-with(@classes,'appendix')]   -->
  <!-- since appendix is a subclass of section, and its classes attribute  -->
  <!-- is "section appendix". That is, to check if an object is of a given -->
  <!-- class we should use:                                                -->
  <!--    object[contains(@classes,class_name)]                            -->
  <!-- And to check if an object is of a given final class:                -->
  <!--    object[ends-with(@classes,class_name)]                           -->
  <!-- The problem is that XSLT 1.0 does not include ends-with.            -->
  <!-- =================================================================== -->

  <!-- ============================================= -->
  <!-- appendix template                             -->
  <!-- ============================================= -->

  <xsl:template match="object[contains(@classes,'section appendix')]">
    <!-- Nesting level -->
    <xsl:param name="nesting_level" select="1"/>

    <div id="{@id}" data-proteus-id="{@id}">

      <!-- Calculate appendix index with respect to its parent-->
      <!-- Should use ends-with     -->
      <xsl:variable name="appendix_index">
        <xsl:number count="object[contains(@classes,'appendix')]" level="single" format="A" />
      </xsl:variable>

      <!-- Get appendix title -->
      <xsl:variable name="title" select="properties/stringProperty[@name=':Proteus-name']"/>

      <!-- Generate header element -->
      <xsl:element name="h1">
        <xsl:value-of select="$appendix_index"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="$title"/>
      </xsl:element>

      <!-- Apply templates to all appendix children -->
      <xsl:apply-templates select="children/object">
        <!-- Provide nesting level context to children -->
        <xsl:with-param name="nesting_level" select="$nesting_level + 1"/>
        <xsl:with-param name="previous_index" select="$appendix_index"/>
      </xsl:apply-templates>

    </div>
  </xsl:template>

  <!-- ============================================= -->
  <!-- appendix template in "toc" mode               -->
  <!-- ============================================= -->

  <!-- A <ul> parent element is assumed              -->

  <!-- <xsl:template match="object[ends-with(@classes,'appendix')]" mode="toc"> -->
  <xsl:template match="object[contains(@classes,'section appendix')]" mode="toc">

    <!-- Calculate appendix index with respect to its parent-->
    <!-- Should use ends-with     -->
    <xsl:variable name="appendix_index">
      <xsl:number count="object[contains(@classes,'appendix')]" level="single" format="A" />
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
    <xsl:if test="children/object[contains(@classes,'section')]">
      <ul class="toc_list">
        <xsl:apply-templates select="children/object[contains(@classes,'section')]" mode="toc">
          <xsl:with-param name="previous_index" select="$appendix_index"/>
        </xsl:apply-templates>
      </ul>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>