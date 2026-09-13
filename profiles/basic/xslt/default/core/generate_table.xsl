<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : generate_table.xsl                             -->
<!-- Content : PROTEUS default XSLT for generating tables     -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/13                                     -->
<!-- Version : 2.0                                            -->
<!-- ======================================================== -->

<!-- ======================================================== -->
<!-- exclude-result-prefixes="proteus" must be set in all     -->
<!-- files to avoid xmlsn:proteus="." to appear in HTML tags. -->
<!-- ======================================================== -->

<!-- ________________________________________________________ -->
<!-- | icon label    | name (suffix)                        | -->
<!-- |______________________________________________________| -->
<!-- | property name | property value                       | -->
<!-- | property name | property value                       | -->
<!-- | ...           | ...                                  | -->
<!-- | property name | property value                       | -->
<!-- |______________________________________________________| -->

<!-- Excluded properties, usually shown in the header, are    -->
<!-- not displayed in the table. Empty properties are not     -->
<!-- displayed either, except they are in the included        -->
<!-- properties list.                                         -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
  exclude-result-prefixes="proteus proteus-utils"
  xmlns:str="http://exslt.org/strings"
  extension-element-prefixes="str"
>
  <xsl:template name="generate_table">
    <xsl:param name="class" select="str:tokenize(@classes, ' ')[last()]"/>
    <xsl:param name="name"  select="properties/*[@name=':Proteus-name']"/>
    <xsl:param name="icon"  select="concat($class,'.png')"/>
    <xsl:param name="postfix"/>
    <xsl:param name="span" select="1"/>
    <xsl:param name="excluded_properties" select="',:Proteus-name,:Proteus-date,version,authors,sources,'"/>
    <xsl:param name="included_properties"/>

    <!-- All objects are displayed inside a div with their IDs -->
    <div id="{@id}" data-proteus-id="{@id}">

      <!-- Properties are displayed in a table -->
      <table class="{concat('proteus_table ', $class)}">

        <!-- Table header with icon, class, name and suffix-->
        <thead>
          <tr class="{concat('header_row ', $class)}">
            <th class="name_column">
              <img src="{concat($base_url_icons,$icon)}"/>
              <xsl:text> </xsl:text>
              <xsl:value-of select="$class_labels/label[@key=$class]"/>
            </th>
            <th class="value_column" colspan="{$span}">
              <xsl:value-of select="$name"/>
              <xsl:if test="$postfix">
                <xsl:text> </xsl:text>
                <xsl:value-of select="$postfix"/>
              </xsl:if>
            </th>
          </tr>
        </thead>

        <!-- Table body with properties -->
        <!-- By wrapping both the list and the current property name with commas, we    -->
        <!-- ensure we're matching whole names and not partial strings.                 -->
        <!-- This was suggested by Claude AI.                                           -->
        <xsl:for-each select="properties/*[not(contains($excluded_properties,concat(',', @name, ',')))]">
            <xsl:call-template name="generate_property_row">
                <xsl:with-param name="included" select="contains($included_properties,concat(',', current()/@name, ','))"/>
            </xsl:call-template>
        </xsl:for-each>

        <!-- Render the children objects recursively -->
        <xsl:call-template name="renderChildren">
          <xsl:with-param name="children" select="children/*" />
        </xsl:call-template>
      </table>
    </div>
  </xsl:template>

  <!-- Named template to render children -->
  <xsl:template name="renderChildren">
    <xsl:param name="children" />

    <xsl:for-each select="$children">
      <!-- Child name -->
      <tr>
        <td style="background-color: lightgray;">
          <strong>
            <xsl:value-of select="properties/stringProperty[@name=':Proteus-name']"/>
          </strong>
        </td>

        <td >
          <table id="{@id}" style="margin: 0; margin-bottom: 0; width: 100%;" data-proteus-id="{@id}">
            <xsl:call-template name="renderProperties">
              <xsl:with-param name="properties" select="properties/*" />
            </xsl:call-template>
          </table>
        </td>
      </tr>
    </xsl:for-each>
  </xsl:template>

</xsl:stylesheet>
