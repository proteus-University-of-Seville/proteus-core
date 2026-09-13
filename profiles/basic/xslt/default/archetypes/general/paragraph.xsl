<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : paragraph.xsl                                  -->
<!-- Content : PROTEUS default XSLT for paragraph             -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/14                                     -->
<!-- Version : 2.0                                            -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
>

  <!-- =========================================================== -->
  <!-- paragraph template                                          -->
  <!-- =========================================================== -->

  <xsl:template match="object[contains(@classes,'paragraph')]">
    <div id="{@id}" data-proteus-id="{@id}">
      <xsl:variable name="content" select="properties/*[@name='text']"/>
      <xsl:variable name="nonempty_content"
                    select="string-length(normalize-space($content)) > 0"/>
      <p>
        <xsl:choose>
          <xsl:when test="not($nonempty_content)">
            [<span class="tbd">
            <xsl:value-of select="$proteus:lang_empty_paragraph"/>
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