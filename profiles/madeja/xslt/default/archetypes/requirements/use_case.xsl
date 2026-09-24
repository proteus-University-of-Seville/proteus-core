<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : use_case.xsl                                             -->
<!-- Content : PROTEUS default XSLT for use-case                        -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/09/24                                               -->
<!-- Version : 1.0                                                      -->
<!-- ================================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <!-- ================================================================== -->
  <!-- use-case template                                                  -->
  <!-- ================================================================== -->

  <!-- Precondition, description, the step-by-step "ordinary sequence" and -->
  <!-- postcondition are shown in that fixed order (not their declaration  -->
  <!-- order in the archetype) and the steps as a Step/Action table, with  -->
  <!-- everything else (importance, urgency, ...) following as usual.      -->
  <!-- The card uses two value sub-columns (span=2) so the step table can  -->
  <!-- show a "Step" and an "Action" column side by side.                  -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' use-case ')]"
    name="use_case_template"
    priority="1"
  >
    <xsl:variable name="use_case_rows">
      <!-- Precondition -->
      <xsl:for-each select="properties/*[@name='precondition']">
        <xsl:call-template name="generate_property_row">
          <xsl:with-param name="span" select="2"/>
        </xsl:call-template>
      </xsl:for-each>

      <!-- Description -->
      <xsl:for-each select="properties/*[@name='description']">
        <xsl:call-template name="generate_property_row">
          <xsl:with-param name="span" select="2"/>
        </xsl:call-template>
      </xsl:for-each>

      <!-- Ordinary sequence: one row per step, "Step" and "Action" columns, -->
      <!-- with the label cell spanning all of them via rowspan.             -->
      <xsl:if test="children/*">
        <tr>
          <th rowspan="{count(children/*) + 1}">
            <xsl:value-of select="proteus-utils:i18n('xslt.ordinary_sequence')"/>
          </th>
          <th class="step_number_column">
            <xsl:value-of select="proteus-utils:i18n('xslt.step')"/>
          </th>
          <th class="step_action_column">
            <xsl:value-of select="proteus-utils:i18n('xslt.action')"/>
          </th>
        </tr>
        <xsl:for-each select="children/*">
          <tr>
            <th class="step_number">
              <xsl:value-of select="position()"/>
            </th>
            <td class="step_action_column">
              <xsl:variable name="step_description" select="properties/*[@name='description']"/>
              <xsl:choose>
                <xsl:when test="not(string-length(normalize-space($step_description)) &gt; 0)">
                  <span class="tbd">
                    <xsl:value-of select="proteus-utils:i18n('xslt.tbd_expanded')"/>
                  </span>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:call-template name="generate_markdown">
                    <xsl:with-param name="content" select="$step_description"/>
                  </xsl:call-template>
                </xsl:otherwise>
              </xsl:choose>
            </td>
          </tr>
        </xsl:for-each>
      </xsl:if>

      <!-- Postcondition -->
      <xsl:for-each select="properties/*[@name='postcondition']">
        <xsl:call-template name="generate_property_row">
          <xsl:with-param name="span" select="2"/>
        </xsl:call-template>
      </xsl:for-each>
    </xsl:variable>

    <xsl:call-template name="generate_table">
      <xsl:with-param name="span" select="2"/>
      <xsl:with-param name="excluded_properties" select="',:Proteus-name,:Proteus-code,:Proteus-date,version,authors,sources,precondition,description,postcondition,'"/>
      <xsl:with-param name="extra_rows_before" select="$use_case_rows"/>
      <xsl:with-param name="show_children" select="false()"/>
    </xsl:call-template>
  </xsl:template>

</xsl:stylesheet>
