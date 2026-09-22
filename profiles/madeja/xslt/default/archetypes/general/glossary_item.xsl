<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================================== -->
<!-- File    : glossary_item.xsl                                              -->
<!-- Content : PROTEUS default XSLT for glossary items                        -->
<!-- Author  : Amador Durán Toro                                              -->
<!-- Date    : 2026/09/18                                                     -->
<!-- Version : 2.0                                                            -->
<!-- ======================================================================== -->

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
       The glossary-item template has priority="1" to avoid being overridden 
       by the bibliography-item template, which is a subclass of glossary-item.
       Sublasses should have their own templates with higher priority, and they
       should call the superclass template by name if they want to reuse it.
  -->
  <!-- ================================================================== -->

  <!-- ====================================================================== -->
  <!-- glossary-item template                                                 -->
  <!-- ====================================================================== -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' glossary-item ')]"
    name="glossary_item_template"
    priority="1"
  >
    <div id="{@id}" class="glossary_item" data-proteus-id="{@id}">
      <p>
        <!-- Generate glossary item name -->
        <span class="glossary_item_name">
          <xsl:value-of select="properties/*[@name=':Proteus-name']"/>
          <xsl:text>: </xsl:text>
        </span>

        <!-- Generate glossary item description -->
        <xsl:variable name="description" select="properties/*[@name='description']"/>
        <xsl:variable name="nonempty_content" select="string-length(normalize-space($description)) > 0"/>

        <span class="glossary_item_description">
          <xsl:choose>
            <xsl:when test="not($nonempty_content)">
              <span class="tbd">
                <xsl:value-of select="proteus-utils:i18n('xslt.tbd_expanded')"/>
              </span>
            </xsl:when>
            <xsl:otherwise>
              <xsl:call-template name="generate_markdown">
                <xsl:with-param name="content" select="$description"/>
              </xsl:call-template>
            </xsl:otherwise>
          </xsl:choose>
        </span>

        <!-- Generate synonym list -->
        <xsl:variable name="synonyms" select="properties/*[@name='synonyms']"/>
        <xsl:variable name="nonempty_synonyms" select="string-length(normalize-space($synonyms)) > 0"/>

        <xsl:if test="$nonempty_synonyms">
          <span class="glossary_item_synonyms">
              <xsl:text> </xsl:text>
              <xsl:value-of select="proteus-utils:i18n('archetype.prop_name.synonyms')"/>
              <xsl:text>: </xsl:text>
              <xsl:value-of select="$synonyms"/>
              <xsl:text>.</xsl:text>
          </span>
        </xsl:if>

        <!-- Get file name with extension (optional, it could be empty) -->
        <xsl:variable name="image_path" select="properties/*[@name='image']"/>

        <!-- Get the image width percentage -->
        <xsl:variable name="image_width_percentage">
          <xsl:choose>
            <xsl:when test="properties/*[@name='width']">
              <xsl:value-of select="properties/*[@name='width']"/>
            </xsl:when>
            <xsl:otherwise>50</xsl:otherwise>
          </xsl:choose>
        </xsl:variable>

        <!-- Generate <img> element (if any) -->
        <xsl:if test="normalize-space($image_path)">
          <div>
            <img class="glossary_item_figure">
              <xsl:attribute name="src">
                <xsl:value-of select="concat('assets:///', $image_path)" disable-output-escaping="no"/>
              </xsl:attribute>
              <xsl:attribute name="style">
                <xsl:value-of select="concat('width:', $image_width_percentage, '%')"/>
              </xsl:attribute>
            </img>
          </div>
        </xsl:if>
      </p>
    </div>
  </xsl:template>

</xsl:stylesheet>