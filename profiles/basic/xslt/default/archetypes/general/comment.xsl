<?xml version="1.0" encoding="utf-8"?>

<!-- =================================================================== -->
<!-- File    : comment.xsl                                               -->
<!-- Content : PROTEUS default XSLT for comment (paragraph)              -->
<!-- Author  : Amador Durán Toro                                         -->
<!-- Date    : 2026/09/14                                                -->
<!-- Version : 2.0                                                       -->
<!-- =================================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
>
  <!-- =================================================================== -->
  <!-- NOTE:                                                               -->
  <!-- match expression should be object[ends-with(@classes,'comment')]    -->
  <!-- since comment is a subclass of paragraph, and its classes attribute -->
  <!-- is "traceable-object paragraph comment". That is, to check if an    -->
  <!-- object is of a given class we should use:                           -->
  <!--    object[contains(@classes,class_name)]                            -->
  <!-- And to check if an object is of a given final class:                -->
  <!--    object[ends-with(@classes,class_name)]                           -->
  <!-- The problem is that XSLT 1.0 does not include ends-with.            -->
  <!-- =================================================================== -->

  <!-- =================================================================== -->
  <!-- comment template                                                    -->
  <!-- =================================================================== -->

  <xsl:template match="object[contains(@classes,'comment')]">
    <div id="{@id}" data-proteus-id="{@id}" class="comment">
      <xsl:call-template name="generate_markdown">
        <xsl:with-param name="content" select="properties/*[@name='text']"/>
      </xsl:call-template>
    </div>
  </xsl:template>

</xsl:stylesheet>