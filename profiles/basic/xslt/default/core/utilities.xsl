<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : utilities.xsl                                  -->
<!-- Content : PROTEUS default XSLT utilities                 -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/22                                     -->
<!-- Version : 2.0                                            -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <!-- Base URL for icons -->
  <xsl:variable name="base_url_icons">templates:///default/resources/images/</xsl:variable>

  <!-- ============================================= -->
  <!-- pagebreak template                            -->
  <!-- ============================================= -->

  <xsl:template name="pagebreak">
    <div class="page-break"></div>
  </xsl:template>

  <!-- ============================================= -->
  <!-- generate_markdown template                    -->
  <!-- ============================================= -->

  <xsl:template name="generate_markdown">
    <xsl:param name="content" select="string(.)"/>
    <xsl:param name="glossary-items-highlight" select="true()"/>

    <xsl:choose>
      <xsl:when test="$glossary-items-highlight">
        <xsl:value-of select="proteus-utils:glossary_highlight(proteus-utils:generate_markdown($content))" disable-output-escaping="yes"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="proteus-utils:generate_markdown($content)" disable-output-escaping="yes"/>
      </xsl:otherwise>
    </xsl:choose>

  </xsl:template>

  <!-- ============================================= -->
  <!-- generate_property_row template                -->
  <!-- ============================================= -->

  <!-- current() is the property element being processed.    -->
  <!-- 'tbd' is considered as having no content, it is shown -->
  <!-- only if it included.                                 -->

  <xsl:template name="generate_property_row">
    <xsl:param name="label" select="proteus-utils:i18n(concat('archetype.prop_name.', current()/@name))"/>
    <xsl:param name="included" select="false()"/>
    <xsl:param name="alternative"/>
    <xsl:param name="span" select="1"/>
    <xsl:param name="diagram" select="@name='diagram'"/>

    <xsl:variable name="hasContent" select="(string-length(current()//text()) > 0) and (normalize-space(current()) != 'tbd')"/>
    <xsl:variable name="hasChildren" select="boolean(current()/*)"/>

    <xsl:if test="$hasContent or $hasChildren or $included">
      <tr>
        <xsl:choose>
          <xsl:when test="$diagram">
            <th colspan="{$span + 1}">
              <xsl:value-of select="$label"/>
              <xsl:apply-templates select="current()"/>
            </th>
          </xsl:when>
          <xsl:otherwise>
            <th>
              <xsl:value-of select="$label"/>
            </th>
            <td colspan="{$span}">
              <xsl:choose>
                <xsl:when test="(not($hasContent) and not($hasChildren)) or normalize-space(current()) = 'tbd'">
                  <span class="tbd">
                    <xsl:value-of select="proteus-utils:i18n('xslt.tbd_expanded')"/>
                  </span>
                </xsl:when>
                <xsl:when test="$alternative">
                  <span class="alternative">
                    <xsl:value-of select="$alternative"/>
                  </span>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:apply-templates select="current()"/>
                </xsl:otherwise>
              </xsl:choose>
            </td>
          </xsl:otherwise>
        </xsl:choose>
      </tr>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>
