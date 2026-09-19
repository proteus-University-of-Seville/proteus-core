<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : figure.xsl                                               -->
<!-- Content : PROTEUS default XSLT for figure                          -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/09/19                                               -->
<!-- Version : 2.0                                                      -->
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

  <!-- ================================================================== -->
  <!-- figure template                                                    -->
  <!-- ================================================================== -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' figure ')]"
    name="figure_template"
    priority="1"
  >
    <div id="{@id}" data-proteus-id="{@id}" class="figure">

      <!-- Get file name with extension -->
      <xsl:variable name="figure_path" select="properties/*[@name='file']"/>

      <!-- Get file link -->
      <xsl:variable name="figure_url" select="properties/*[@name='url']"/>

      <!-- Get the image width percentage -->
      <xsl:variable name="image_width_percentage">
        <xsl:choose>
          <xsl:when test="properties/*[@name='width']">
            <xsl:value-of select="properties/*[@name='width']"/>
          </xsl:when>
          <xsl:otherwise>50</xsl:otherwise>
        </xsl:choose>
      </xsl:variable>

      <!-- Generate <img> element -->
      <img class="figure_image">
        <xsl:attribute name="src">
          <xsl:choose>
            <xsl:when test="normalize-space($figure_path)">
              <xsl:value-of select="concat('assets:///', $figure_path)" disable-output-escaping="no"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="$figure_url" disable-output-escaping="yes"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:attribute>

        <xsl:attribute name="style">
          <xsl:value-of select="concat('width:', $image_width_percentage, '%')"/>
        </xsl:attribute>
      </img>

      <!-- Generate figure caption -->
      <p class="figure_caption">
        <span class="figure_caption_label">
          <xsl:value-of select="proteus-utils:i18n('xslt.figure')"/>
          <xsl:text> </xsl:text>
          <!-- from is needed to restart numbering in each document          -->
          <!-- level is needed to avoid restarting numbering in each section -->
          <xsl:number from="object[@classes=':Proteus-document']"
                      count="object[contains(concat(' ', normalize-space(@classes), ' '),' figure ')]"
                      level="any"/>:
          <xsl:text> </xsl:text>
        </span>

        <!-- apply markdown -->
        <xsl:call-template name="generate_markdown">
          <xsl:with-param name="content" select="properties/*[@name='description']"/>
        </xsl:call-template>
      </p>

    </div>

  </xsl:template>

</xsl:stylesheet>