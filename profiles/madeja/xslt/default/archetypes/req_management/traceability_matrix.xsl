<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : traceability_matrix.xsl                                  -->
<!-- Content : PROTEUS default XSLT for traceability matrix             -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/09/24                                               -->
<!-- Version : 2.2                                                      -->
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
  <!-- traceability-matrix template                                       -->
  <!-- ================================================================== -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' traceability-matrix ')]"
    name="traceability_matrix_template"
    priority="1"
  >
    <div id="{@id}" data-proteus-id="{@id}" class="proteus_object traceability_matrix">

      <!-- Extract row and column classes -->
      <xsl:variable name="col-classes">
        <xsl:apply-templates select="properties/classListProperty[@name='col-classes']/class"/>
      </xsl:variable>

      <xsl:variable name="row-classes">
        <xsl:apply-templates select="properties/classListProperty[@name='row-classes']/class"/>
      </xsl:variable>

      <!-- Trace types to consider, :Proteus-dependency if none were selected -->
      <xsl:variable name="trace-types">
        <xsl:choose>
          <xsl:when test="properties/traceTypeListProperty[@name='trace-types']/type">
            <xsl:apply-templates select="properties/traceTypeListProperty[@name='trace-types']/type" mode="matrix-trace-type"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>:Proteus-dependency </xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>

      <xsl:choose>
        <xsl:when test="string-length($col-classes) &gt; 1 and string-length($row-classes) &gt; 1">
          <xsl:call-template name="matrix-from-classes">
            <xsl:with-param name="col-classes" select="$col-classes"/>
            <xsl:with-param name="row-classes" select="$row-classes"/>
            <xsl:with-param name="trace-types" select="$trace-types"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="traceability-matrix-warning">
            <xsl:with-param name="message" select="proteus-utils:i18n('xslt.traceability_matrix_missing_class')"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>

      <!-- Generate matrix caption -->
      <p class="matrix_caption">
        <span class="matrix_caption_label">
          <xsl:value-of select="proteus-utils:i18n('xslt.traceability_matrix')"/>
          <xsl:text> </xsl:text>
          <!-- from is needed to restart numbering in each document          -->
          <!-- level is needed to avoid restarting numbering in each section -->
          <xsl:number
            from="object[@classes=':Proteus-document']"
            count="object[contains(concat(' ', normalize-space(@classes), ' '),' traceability-matrix ')]"
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

  <!-- This template helps creating a list of classes separated by spaces. -->
  <!-- Proteus classes cannot contain spaces so this is supposed to be a   -->
  <!-- safe separator.                                                     -->
  <xsl:template match="class">
    <xsl:value-of select="normalize-space(.)"/>
    <xsl:text> </xsl:text>
  </xsl:template>

  <!-- Same idea for trace type names. A dedicated mode is used because    -->
  <!-- <type> is not exclusive to this property: matching it unmoded would -->
  <!-- apply this template to any other <type> element in the document.    -->
  <xsl:template match="type" mode="matrix-trace-type">
    <xsl:value-of select="normalize-space(.)"/>
    <xsl:text> </xsl:text>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- matrix-from-classes auxiliary template                             -->
  <!-- ================================================================== -->

  <!-- TODO: could this double-check be performed in the main template ? -->

  <xsl:template name="matrix-from-classes">
    <xsl:param name="col-classes" select="' '"/>
    <xsl:param name="row-classes" select="' '"/>
    <xsl:param name="trace-types" select="':Proteus-dependency '"/>

    <!-- Get column and row items using Python -->
    <xsl:variable name="col-items" select="proteus-utils:traceabilityMatrixHelper.get_objects_from_classes($col-classes)"/>
    <xsl:variable name="row-items" select="proteus-utils:traceabilityMatrixHelper.get_objects_from_classes($row-classes)"/>

    <!-- If there are no col or row classes, warn the user and do not create the matrix -->
    <xsl:choose>
      <xsl:when test="count($col-items) = 0 or count($row-items) = 0">
        <xsl:call-template name="traceability-matrix-warning">
          <xsl:with-param name="message" select="proteus-utils:i18n('xslt.traceability_matrix_missing_item')"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="generate-traceability-matrix-table">
          <xsl:with-param name="col-items" select="$col-items"/>
          <xsl:with-param name="row-items" select="$row-items"/>
          <xsl:with-param name="trace-types" select="$trace-types"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- generate-traceability-matrix-table auxiliary template              -->
  <!-- ================================================================== -->

  <xsl:template name="generate-traceability-matrix-table">
    <xsl:param name="col-items"/>
    <xsl:param name="row-items"/>
    <xsl:param name="trace-types"/>

    <table class="proteus_table traceability_matrix">
      <thead>
        <xsl:call-template name="generate-traceability-matrix-header">
          <xsl:with-param name="col-items" select="$col-items"/>
        </xsl:call-template>
      </thead>

      <tbody>
        <xsl:for-each select="$row-items">
          <tr>
            <xsl:call-template name="generate-traceability-matrix-row">
              <xsl:with-param name="col-items" select="$col-items"/>
              <xsl:with-param name="trace-types" select="$trace-types"/>
            </xsl:call-template>
          </tr>
        </xsl:for-each>
      </tbody>
    </table>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- generate-traceability-matrix-header auxiliary template             -->
  <!-- ================================================================== -->

  <!-- Table header: same name_column/value_column shape as every other -->
  <!-- object's card (icon pill, code badge, name), plus a second row    -->
  <!-- for the column items. The font-size buttons still ride along,    -->
  <!-- just repositioned into the corner of the card instead of sharing -->
  <!-- a cell with the code.                                            -->
  <xsl:template name="generate-traceability-matrix-header">
    <xsl:param name="col-items"/>

    <xsl:variable name="code" select="properties/*[@name=':Proteus-code']"/>
    <xsl:variable name="name" select="properties/*[@name=':Proteus-name']"/>

    <tr class="header_row traceability_matrix">
      <th class="name_column">
        <span class="class_pill">
          <img src="{concat($base_url_icons, 'traceability-matrix.png')}"/>
          <xsl:value-of select="proteus-utils:i18n('archetype.class.traceability-matrix')"/>
        </span>
      </th>
      <th class="value_column" colspan="{count($col-items)}">
        <div class="matrix_font_buttons">
          <button class="reduce_font">A-</button>
          <button class="increase_font">A+</button>
        </div>
        <xsl:if test="$code">
          <span class="object_code"><xsl:value-of select="$code"/></span>
        </xsl:if>
        <xsl:value-of select="$name"/>
      </th>
    </tr>

    <tr>
      <th class="matrix_corner"></th>
      <xsl:for-each select="$col-items">
        <xsl:variable name="label" select="label"/>

        <th class="matrix_column">
          <a href="#{@id}" onclick="selectAndNavigate(`{@id}`, event)" title="{$label}">
            <xsl:value-of select="$label"/>
          </a>
        </th>
      </xsl:for-each>
    </tr>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- generate-traceability-matrix-row auxiliary template                -->
  <!-- ================================================================== -->

  <xsl:template name="generate-traceability-matrix-row">
    <xsl:param name="col-items"/>
    <xsl:param name="trace-types"/>

    <xsl:variable name="label" select="label"/>
    <xsl:variable name="row-item-id" select="@id"/>

    <th>
      <a href="#{@id}" onclick="selectAndNavigate(`{@id}`, event)" title="{$label}">
        <xsl:value-of select="$label"/>
      </a>
    </th>

    <xsl:for-each select="$col-items">
      <td>
        <xsl:variable name="has-dependency" select="proteus-utils:traceabilityMatrixHelper.check_trace($row-item-id, @id, $trace-types)"/>
        <xsl:choose>
          <xsl:when test="$has-dependency = 'True'">
            <xsl:attribute name="class">trace</xsl:attribute>
            <span class="trace_mark">&#10003;</span>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>-</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </td>
    </xsl:for-each>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- traceability-matrix-warning auxiliary template                     -->
  <!-- ================================================================== -->

  <!-- Warning to be shown when rows or columns are missing -->
  <xsl:template name="traceability-matrix-warning">
    <xsl:param name="message"/>

    <table class="traceability_matrix">
      <tbody>
        <tr>
          <th>
            <span class="tbd"><xsl:value-of select="$message"/></span>
          </th>
        </tr>
      </tbody>
    </table>
  </xsl:template>

</xsl:stylesheet>
