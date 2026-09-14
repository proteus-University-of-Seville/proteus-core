<?xml version="1.0" encoding="utf-8"?>

<!-- ============================================================================ -->
<!-- File    : bibliography_item.xsl                                              -->
<!-- Content : PROTEUS default XSLT for bibliography items                        -->
<!-- Author  : Amador Durán Toro                                                  -->
<!-- Date    : 2026/09/14                                                         -->
<!-- Version : 2.0                                                                -->
<!-- ============================================================================ -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
>
  <!-- ========================================================================== -->
  <!-- NOTE:                                                                      -->
  <!-- match expression should be object[ends-with(@classes,'bibliography-item')] -->
  <!-- since bibliography-item is a subclass of glossary-item, and its classes    -->
  <!-- attribute is "traceable-object glossary-item bibliography-item". That is,  -->
  <!-- to check if an object is of a given class we should use:                   -->
  <!--    object[contains(@classes,class_name)]                                   -->
  <!-- And to check if an object is of a given final class:                       -->
  <!--    object[ends-with(@classes,class_name)]                                  -->
  <!-- The problem is that XSLT 1.0 does not include ends-with.                   -->
  <!-- ========================================================================== -->

  <!-- ========================================================================== -->
  <!-- bibliography-item template                                                 -->
  <!-- ========================================================================== -->

  <xsl:template match="object[contains(@classes,'bibliography-item')]">
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