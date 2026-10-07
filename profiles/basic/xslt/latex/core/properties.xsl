<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : properties.xsl                                 -->
<!-- Content : PROTEUS LaTeX XSLT for properties              -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/10/07                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
  exclude-result-prefixes="proteus proteus-utils"
>

  <!-- ============================================= -->
  <!-- Any other property: escaped text              -->
  <!-- ============================================= -->

  <!-- Unlike HTML, the built-in text template cannot be used  -->
  <!-- because text must be escaped. Negative priority so that -->
  <!-- the property-type templates below (priority 0) win.     -->
  <xsl:template match="properties/*" priority="-0.5">
    <xsl:call-template name="tex"/>
  </xsl:template>

  <!-- ============================================= -->
  <!-- trace_target template: [code] name            -->
  <!-- ============================================= -->

  <!-- Only targets in the rendered document have a label to -->
  <!-- link to; the others are shown as plain text.          -->
  <!-- Bibliography items of the document are cited.         -->
  <xsl:template name="trace_target">
    <xsl:param name="target_object"/>

    <xsl:variable name="target_code" select="$target_object/properties/*[@name=':Proteus-code']" />
    <xsl:variable name="in_document"
      select="$target_object/ancestor::object[@classes=':Proteus-document']/@id = proteus-utils:current_document()"/>
    <xsl:variable name="citable">
      <xsl:call-template name="is_citable">
        <xsl:with-param name="object" select="$target_object"/>
      </xsl:call-template>
    </xsl:variable>

    <xsl:choose>
      <xsl:when test="$citable = 'true'">
        <xsl:text>\cite{</xsl:text>
        <xsl:value-of select="$target_object/@id"/>
        <xsl:text>}</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="trace_target_link">
          <xsl:with-param name="target_object" select="$target_object"/>
          <xsl:with-param name="target_code" select="$target_code"/>
          <xsl:with-param name="in_document" select="$in_document"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- [code] name, linked if the target is in the rendered document -->
  <xsl:template name="trace_target_link">
    <xsl:param name="target_object"/>
    <xsl:param name="target_code"/>
    <xsl:param name="in_document"/>

    <xsl:if test="$in_document">
      <xsl:text>\hyperref[</xsl:text>
      <xsl:value-of select="$target_object/@id"/>
      <xsl:text>]</xsl:text>
    </xsl:if>
    <xsl:text>{</xsl:text>
    <xsl:if test="$target_code">
      <xsl:text>[</xsl:text>
      <xsl:call-template name="tex"><xsl:with-param name="text" select="$target_code"/></xsl:call-template>
      <xsl:text>]\nobreakspace{}</xsl:text>
    </xsl:if>
    <xsl:call-template name="tex">
      <xsl:with-param name="text" select="$target_object/properties/*[@name=':Proteus-name']"/>
    </xsl:call-template>
    <xsl:text>}</xsl:text>
  </xsl:template>

  <!-- ============================================= -->
  <!-- traceProperty                                 -->
  <!-- ============================================= -->

  <!-- List mode -->
  <xsl:template match="traceProperty">
    <xsl:if test="//object[@id = current()/trace/@target]">
      <xsl:text>\begin{itemize}[topsep=0pt]&#10;</xsl:text>
      <xsl:for-each select="trace">
        <xsl:variable name="target_object" select="//object[@id=current()/@target]" />
        <xsl:if test="$target_object">
          <xsl:text>\item </xsl:text>
          <xsl:call-template name="trace_target">
            <xsl:with-param name="target_object" select="$target_object"/>
          </xsl:call-template>
          <xsl:text>&#10;</xsl:text>
        </xsl:if>
      </xsl:for-each>
      <xsl:text>\end{itemize}</xsl:text>
    </xsl:if>
  </xsl:template>

  <!-- Paragraph mode -->
  <xsl:template match="traceProperty" mode="paragraph">
    <xsl:for-each select="trace">
      <xsl:variable name="target_object" select="//object[@id=current()/@target]" />
      <xsl:if test="$target_object">
        <xsl:call-template name="trace_target">
          <xsl:with-param name="target_object" select="$target_object"/>
        </xsl:call-template>
        <xsl:text>\par&#10;</xsl:text>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

  <!-- ============================================= -->
  <!-- markdownProperty                              -->
  <!-- ============================================= -->

  <xsl:template match="markdownProperty">
    <xsl:call-template name="generate_markdown">
      <xsl:with-param name="content" select="."/>
    </xsl:call-template>
  </xsl:template>

  <!-- ============================================= -->
  <!-- urlProperty                                   -->
  <!-- ============================================= -->

  <xsl:template match="urlProperty">
    <xsl:value-of select="proteus-utils:latex_url(string(.))"/>
  </xsl:template>

  <!-- ============================================= -->
  <!-- enumProperty                                  -->
  <!-- ============================================= -->

  <!-- Enumeration choices are shared with the application GUI -->
  <xsl:template match="enumProperty">
    <xsl:call-template name="label">
      <xsl:with-param name="key" select="concat('archetype.enum_choices.', current()/text())"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ============================================= -->
  <!-- booleanProperty                               -->
  <!-- ============================================= -->

  <xsl:template match="booleanProperty">
    <xsl:choose>
      <xsl:when test="normalize-space(.) = 'true'">\checkmark</xsl:when>
      <xsl:otherwise>--</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ============================================= -->
  <!-- fileProperty                                  -->
  <!-- ============================================= -->

  <!-- NOTE: it is assumed that it is a graphic file.  -->
  <!-- NOTE: it is also assumed that there may be a    -->
  <!-- width property in the same object. Assets are   -->
  <!-- referenced as {assets/<file>}: the export       -->
  <!-- strategies copy them (converting the formats    -->
  <!-- LaTeX cannot include) by looking for this text. -->

  <xsl:template match="fileProperty">
    <xsl:text>\includegraphics[width=</xsl:text>
    <xsl:call-template name="image_width">
      <xsl:with-param name="width" select="../*[@name='width']"/>
    </xsl:call-template>
    <xsl:text>\linewidth]{assets/</xsl:text>
    <xsl:value-of select="normalize-space(.)"/>
    <xsl:text>}</xsl:text>
  </xsl:template>

  <!-- ============================================= -->
  <!-- traceTypeListProperty                         -->
  <!-- ============================================= -->

  <xsl:template match="traceTypeListProperty">
    <xsl:for-each select="type[normalize-space()]">
      <xsl:if test="position() > 1">, </xsl:if>
      <xsl:call-template name="label">
        <xsl:with-param name="key" select="concat('xslt.trace_type.', current()/text())"/>
      </xsl:call-template>
    </xsl:for-each>
  </xsl:template>

  <!-- ============================================= -->
  <!-- classListProperty                             -->
  <!-- ============================================= -->

  <xsl:template match="classListProperty">
    <xsl:for-each select="class[normalize-space()]">
      <xsl:if test="position() > 1">, </xsl:if>
      <xsl:call-template name="label">
        <xsl:with-param name="key" select="concat('archetype.class.', normalize-space(.))"/>
      </xsl:call-template>
    </xsl:for-each>
  </xsl:template>

</xsl:stylesheet>
