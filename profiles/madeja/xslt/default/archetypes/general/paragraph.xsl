<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : paragraph.xsl                                            -->
<!-- Content : PROTEUS default XSLT for paragraph                       -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/09/17                                               -->
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
       The paragraph template has priority="1" to avoid being overridden by
       the comment template, which is a subclass of paragraph. Sublasses
       should have their own templates with higher priority, and they
       should call the superclass template by name if they want to reuse it.
  -->
  <!-- ================================================================== -->

  <!-- ================================================================== -->
  <!-- paragraph template                                                 -->
  <!-- ================================================================== -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' paragraph ')]"
    name="paragraph_template"
    priority="1"
  >
    <div id="{@id}" data-proteus-id="{@id}">
      <xsl:variable name="content" select="properties/*[@name='text']"/>
      <xsl:variable name="nonempty_content"
                    select="string-length(normalize-space($content)) > 0"/>
      <p>
        <xsl:choose>
          <xsl:when test="not($nonempty_content)">
            [<span class="tbd">
            <xsl:value-of select="proteus-utils:i18n('xslt.empty_paragraph')"/>
            </span>]
          </xsl:when>
          <xsl:otherwise>
            <xsl:call-template name="generate_markdown">
              <xsl:with-param name="content" select="$content"/>
            </xsl:call-template>
          </xsl:otherwise>
        </xsl:choose>
      </p>
    </div>
  </xsl:template>

</xsl:stylesheet>