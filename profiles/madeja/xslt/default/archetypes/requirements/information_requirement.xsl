<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : information_requirement.xsl                              -->
<!-- Content : PROTEUS default XSLT for information-requirement         -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/09/24                                               -->
<!-- Version : 1.1                                                      -->
<!-- ================================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <!-- ================================================================== -->
  <!-- information-requirement template                                   -->
  <!-- ================================================================== -->

  <!-- Its specific-data children are shown as a compact bulleted list     -->
  <!-- ("name: description" per item) instead of the default nested-card  -->
  <!-- rendering, since each specific datum is just a short name/          -->
  <!-- description pair, not a full object worth a card of its own. The   -->
  <!-- row always comes right after the description: 'description' is    -->
  <!-- rendered manually here (excluded from the automatic property loop) -->
  <!-- so the two stay adjacent regardless of where the rest of the       -->
  <!-- properties end up.                                                 -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' information-requirement ')]"
    name="information_requirement_template"
    priority="1"
  >
    <xsl:variable name="description_and_specific_data_rows">
      <!-- Description -->
      <xsl:for-each select="properties/*[@name='description']">
        <xsl:call-template name="generate_property_row"/>
      </xsl:for-each>

      <!-- Specific data -->
      <xsl:if test="children/*">
        <tr class="children_row">
          <th>
            <xsl:value-of select="proteus-utils:i18n('archetype.class.specific-data')"/>
          </th>
          <td class="children_column">
            <ul class="specific_data_list">
              <xsl:for-each select="children/*">
                <li>
                  <strong>
                    <xsl:value-of select="properties/*[@name=':Proteus-name']"/>
                  </strong>
                  <xsl:text>: </xsl:text>
                  <xsl:call-template name="generate_markdown">
                    <xsl:with-param name="content" select="properties/*[@name='description']"/>
                  </xsl:call-template>
                </li>
              </xsl:for-each>
            </ul>
          </td>
        </tr>
      </xsl:if>
    </xsl:variable>

    <xsl:call-template name="generate_table">
      <xsl:with-param name="excluded_properties" select="',:Proteus-name,:Proteus-code,:Proteus-date,version,authors,sources,description,'"/>
      <xsl:with-param name="extra_rows_before" select="$description_and_specific_data_rows"/>
      <xsl:with-param name="show_children" select="false()"/>
    </xsl:call-template>
  </xsl:template>

</xsl:stylesheet>
