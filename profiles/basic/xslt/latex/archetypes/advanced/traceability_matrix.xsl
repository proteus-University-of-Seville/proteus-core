<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : traceability_matrix.xsl                                  -->
<!-- Content : PROTEUS LaTeX XSLT for traceability matrix               -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/10/07                                               -->
<!-- Version : 1.0                                                      -->
<!-- ================================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
  exclude-result-prefixes="proteus proteus-utils"
>
  <!-- ================================================================ -->
  <!-- NOTE
       Rows and columns are computed with the traceabilityMatrixHelper
       methods of the basic plugin, as in the default template. The matrix
       is a non-floating table with rotated column headers, scaled down
       if it is wider than the text. Its caption uses the "traceability
       matrix" label and LaTeX numbering.
  -->
  <!-- ================================================================ -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' traceability-matrix ')]"
    name="traceability_matrix_template"
    priority="1"
  >
    <!-- Row and column classes, space-separated -->
    <xsl:variable name="col-classes">
      <xsl:for-each select="properties/classListProperty[@name='col-classes']/class">
        <xsl:value-of select="normalize-space(.)"/>
        <xsl:text> </xsl:text>
      </xsl:for-each>
    </xsl:variable>

    <xsl:variable name="row-classes">
      <xsl:for-each select="properties/classListProperty[@name='row-classes']/class">
        <xsl:value-of select="normalize-space(.)"/>
        <xsl:text> </xsl:text>
      </xsl:for-each>
    </xsl:variable>

    <!-- Trace types to consider, :Proteus-dependency if none were selected -->
    <xsl:variable name="trace-types">
      <xsl:choose>
        <xsl:when test="properties/traceTypeListProperty[@name='trace-types']/type">
          <xsl:for-each select="properties/traceTypeListProperty[@name='trace-types']/type">
            <xsl:value-of select="normalize-space(.)"/>
            <xsl:text> </xsl:text>
          </xsl:for-each>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>:Proteus-dependency </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <xsl:text>&#10;\begin{table}[H]&#10;\centering\ProteusUseAccent{traceability-matrix}&#10;</xsl:text>

    <xsl:choose>
      <xsl:when test="string-length($col-classes) &gt; 1 and string-length($row-classes) &gt; 1">
        <xsl:call-template name="matrix-from-classes">
          <xsl:with-param name="col-classes" select="$col-classes"/>
          <xsl:with-param name="row-classes" select="$row-classes"/>
          <xsl:with-param name="trace-types" select="$trace-types"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="tbd">
          <xsl:with-param name="key" select="'xslt.traceability_matrix_missing_class'"/>
        </xsl:call-template>
        <xsl:text>&#10;</xsl:text>
      </xsl:otherwise>
    </xsl:choose>

    <!-- Caption -->
    <xsl:text>\renewcommand{\tablename}{</xsl:text>
    <xsl:call-template name="label">
      <xsl:with-param name="key" select="'xslt.traceability_matrix'"/>
    </xsl:call-template>
    <xsl:text>}\caption{</xsl:text>
    <xsl:call-template name="generate_markdown">
      <xsl:with-param name="content" select="properties/*[@name='description']"/>
    </xsl:call-template>
    <xsl:text>}\ProteusLabel{</xsl:text>
    <xsl:value-of select="@id"/>
    <xsl:text>}&#10;\end{table}&#10;</xsl:text>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- matrix-from-classes auxiliary template                             -->
  <!-- ================================================================== -->

  <xsl:template name="matrix-from-classes">
    <xsl:param name="col-classes"/>
    <xsl:param name="row-classes"/>
    <xsl:param name="trace-types"/>

    <!-- Get column and row items using Python -->
    <xsl:variable name="col-items" select="proteus-utils:traceabilityMatrixHelper.get_objects_from_classes($col-classes)"/>
    <xsl:variable name="row-items" select="proteus-utils:traceabilityMatrixHelper.get_objects_from_classes($row-classes)"/>

    <xsl:choose>
      <xsl:when test="count($col-items) = 0 or count($row-items) = 0">
        <xsl:call-template name="tbd">
          <xsl:with-param name="key" select="'xslt.traceability_matrix_missing_item'"/>
        </xsl:call-template>
        <xsl:text>&#10;</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <!-- Column specification: one centred column per column item -->
        <xsl:text>\begin{adjustbox}{max width=\ProteusTableWidth}\small&#10;\begin{tabular}{|l|</xsl:text>
        <xsl:for-each select="$col-items">c|</xsl:for-each>
        <xsl:text>}&#10;\hline&#10;\rowcolor{proteusaccent!12}</xsl:text>

        <!-- Header: rotated column labels -->
        <xsl:for-each select="$col-items">
          <xsl:text> &amp; \rotatebox{90}{</xsl:text>
          <xsl:call-template name="matrix-item"/>
          <xsl:text>}</xsl:text>
        </xsl:for-each>
        <xsl:text> \\ \hline&#10;</xsl:text>

        <!-- One row per row item -->
        <xsl:for-each select="$row-items">
          <xsl:variable name="row-item-id" select="@id"/>
          <xsl:call-template name="matrix-item"/>
          <xsl:for-each select="$col-items">
            <xsl:text> &amp; </xsl:text>
            <xsl:choose>
              <xsl:when test="proteus-utils:traceabilityMatrixHelper.check_trace($row-item-id, @id, $trace-types) = 'True'">
                <xsl:text>\cellcolor{proteusaccent!25}\checkmark</xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>--</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:for-each>
          <xsl:text> \\ \hline&#10;</xsl:text>
        </xsl:for-each>

        <xsl:text>\end{tabular}&#10;\end{adjustbox}&#10;</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ================================================================== -->
  <!-- matrix-item auxiliary template: link to a row or column item       -->
  <!-- ================================================================== -->

  <!-- current() is an <object id="..."><label>...</label></object> node -->
  <!-- returned by traceabilityMatrixHelper.get_objects_from_classes     -->
  <xsl:template name="matrix-item">
    <xsl:text>\hyperref[</xsl:text>
    <xsl:value-of select="@id"/>
    <xsl:text>]{</xsl:text>
    <xsl:call-template name="tex">
      <xsl:with-param name="text" select="label"/>
    </xsl:call-template>
    <xsl:text>}</xsl:text>
  </xsl:template>

</xsl:stylesheet>
