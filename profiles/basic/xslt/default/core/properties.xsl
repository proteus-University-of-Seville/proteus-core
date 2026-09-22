<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : properties.xsl                                 -->
<!-- Content : PROTEUS default XSLT for properties            -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/22                                     -->
<!-- Version : 2.0                                            -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>

  <!-- ============================================= -->
  <!-- traceProperty                                 -->
  <!-- ============================================= -->

  <!-- List mode -->
  <xsl:template match="traceProperty">
    <ul class="traces">
      <xsl:for-each select="trace">
        <xsl:variable name="target_id" select="@target" />
        <xsl:variable name="target_object" select="//object[@id=$target_id]" />
        <xsl:variable name="target_code" select="$target_object/properties/*[@name=':Proteus-code']" />
        <xsl:variable name="target_name">
          <xsl:if test="$target_code">[<xsl:value-of select="$target_code"/>]</xsl:if>
          <xsl:value-of select="$target_object/properties/*[@name=':Proteus-name']" />
        </xsl:variable>

        <xsl:if test="$target_object">
          <li>
            <a href="#{$target_id}" onclick="selectAndNavigate(`{$target_id}`, event)">
              <xsl:value-of select="$target_name"/>
            </a>
          </li>
        </xsl:if>
      </xsl:for-each>
    </ul>
  </xsl:template>

  <!-- Paragraph mode -->
  <xsl:template match="traceProperty" mode="paragraph">
    <xsl:for-each select="trace">
      <xsl:variable name="target_id" select="@target" />
      <xsl:variable name="target_object" select="//object[@id=$target_id]" />
      <xsl:variable name="target_code" select="$target_object/properties/*[@name=':Proteus-code']" />
      <xsl:variable name="target_name">
        <xsl:if test="$target_code">[<xsl:value-of select="$target_code"/></xsl:if>
        <xsl:value-of select="$target_object/properties/*[@name=':Proteus-name']" />
      </xsl:variable>

      <xsl:if test="$target_object">
        <p>
          <a href="#{$target_id}" onclick="selectAndNavigate(`{$target_id}`, event)">
            <xsl:value-of select="$target_name"/>
          </a>
        </p>
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
    <xsl:variable name="href" select="."/>
    <a href="{$href}">
      <xsl:value-of select="$href"/>
    </a>
  </xsl:template>

  <!-- ============================================= -->
  <!-- enumProperty                                  -->
  <!-- ============================================= -->

  <!-- Enumeration choices are shared with the application GUI -->
  <xsl:template match="enumProperty">
    <xsl:value-of select="proteus-utils:i18n(concat('archetype.enum_choices.', current()/text()))"/>
  </xsl:template>

  <!-- ============================================= -->
  <!-- fileProperty                                  -->
  <!-- ============================================= -->

  <!-- NOTE: it is assumed that it is a graphic file.-->
  <!-- NOTE: it is also assumed that there is a      -->
  <!-- width property in the same object.            -->

  <xsl:template match="fileProperty">
    <!-- Get file name with extension (optional, it could be empty) -->
    <xsl:variable name="image_path" select="."/>

    <!-- Get the image width percentage (if exists)-->
    <xsl:variable name="image_width_percentage">
      <xsl:choose>
        <xsl:when test="../*[@name='width']">
          <xsl:value-of select="../*[@name='width']"/>
        </xsl:when>
        <xsl:otherwise>50</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <!-- Generate <img> element (if any) -->
    <br></br>
    <br></br>
    <div>
      <xsl:choose>
        <xsl:when test="normalize-space($image_path)">
          <img class="figure_image">
            <xsl:attribute name="src">
              <xsl:value-of select="concat('assets:///', $image_path)" disable-output-escaping="no"/>
            </xsl:attribute>
            <xsl:attribute name="style">
              <xsl:value-of select="concat('width:', $image_width_percentage, '%')"/>
            </xsl:attribute>
          </img>
        </xsl:when>
        <xsl:otherwise>
          <span class="tbd">
            <xsl:value-of select="proteus-utils:i18n('xslt.tbd_expanded')"/>
          </span>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

  <!-- ============================================= -->
  <!-- traceTypeListProperty                         -->
  <!-- ============================================= -->

  <xsl:template match="traceTypeListProperty">
    <ul class="traces">
      <xsl:for-each select="type">
        <xsl:if test="current()/text()">
          <li>
            <a>
              <xsl:value-of select="proteus-utils:i18n(concat('xslt.trace_type.', current()/text()))"/>
            </a>
          </li>
        </xsl:if>
      </xsl:for-each>
    </ul>
  </xsl:template>

</xsl:stylesheet>