<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : generate_table.xsl                             -->
<!-- Content : PROTEUS default XSLT for generating tables     -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/20                                     -->
<!-- Version : 2.0                                            -->
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
  xmlns:str="http://exslt.org/strings"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
  exclude-result-prefixes="str proteus proteus-utils"
>
  <xsl:template name="generate_table">
    <xsl:param name="class" select="str:tokenize(@classes, ' ')[last()]"/>
    <xsl:param name="name" select="properties/*[@name=':Proteus-name']"/>
    <xsl:param name="icon" select="concat($class,'.png')"/>
    <xsl:param name="postfix"/>
    <xsl:param name="span" select="1"/>
    <xsl:param name="excluded_properties" select="',:Proteus-name,:Proteus-date,:Proteus-code,version,authors,sources,'"/>
    <xsl:param name="included_properties"/>

    <!-- Image shown in the upper right corner of the object, if any.     -->
    <!-- Organizations use 'logo' and stakeholders use 'photo'. An        -->
    <!-- archetype may pass a different property in this parameter.       -->
    <xsl:param name="image"
      select="properties/fileProperty[@name='logo' or @name='photo'][normalize-space() != '']"
    />

    <!-- Objects with a code (e.g. requirements, model elements) show it   -->
    <!-- next to the name in the header instead of as a property row.     -->
    <xsl:variable name="code" select="properties/codeProperty[@name=':Proteus-code']"/>

    <!-- The corner image is not shown again as a property row -->
    <xsl:variable name="all_excluded_properties">
      <xsl:value-of select="$excluded_properties"/>
      <xsl:if test="$image">
        <xsl:value-of select="concat($image[1]/@name, ',')"/>
      </xsl:if>
    </xsl:variable>

    <!-- All objects are displayed inside a div with their IDs -->
    <div id="{@id}" data-proteus-id="{@id}" class="{$class}">
      <xsl:attribute name="class">
        <xsl:text>proteus_object</xsl:text>
        <xsl:if test="$image"> with_image</xsl:if>
      </xsl:attribute>

      <!-- Properties are displayed in a table -->
      <table class="{concat('proteus_table ', $class)}">

        <!-- Table header with icon, class, name and suffix-->
        <thead>
          <tr class="{concat('header_row ', $class)}">
            <th class="name_column">
              <!-- the span allows the icon and the class name to be shaped as a pill -->
              <span class="class_pill">
                <img src="{concat($base_url_icons,$icon)}"/>
                <xsl:value-of select="proteus-utils:i18n(concat('archetype.class.', $class))"/>
              </span>
            </th>
            <th class="value_column" colspan="{$span}">
              <!-- The image is placed here so that it inherits the archetype  -->
              <!-- colours; CSS positions it over the upper right corner of    -->
              <!-- the object. Without CSS it simply shows in the header.      -->
              <xsl:if test="$image">
                <img class="object_image"
                  src="{concat('assets:///', normalize-space($image[1]))}"
                  alt="{$name}"
                />
              </xsl:if>
              <xsl:if test="$code">
                <span class="code_pill">
                  <xsl:value-of select="$code"/>
                </span>
                <xsl:text> </xsl:text>
              </xsl:if>
              <xsl:value-of select="$name"/>
              <xsl:if test="$postfix">
                <xsl:text></xsl:text>
                <xsl:value-of select="$postfix"/>
              </xsl:if>
            </th>
          </tr>
        </thead>

        <!-- Table body with properties -->
        <!-- By wrapping both the list and the current property name with commas, we    -->
        <!-- ensure we're matching whole names and not partial strings.                 -->
        <!-- This was suggested by Claude AI.                                           -->
        <xsl:for-each select="properties/*[not(contains($all_excluded_properties,concat(',', @name, ',')))]">
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
  <!-- TODO: review this template and simplify it if possible -->
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
            <xsl:for-each select="properties/*">
              <tr>
                <td style="width: 17.5%;">
                  <strong>
                    <xsl:value-of select="@name"/>
                  </strong>
                </td>
                <td style="width: 82.5%;">
                  <xsl:value-of select="."/>
                </td>
              </tr>
            </xsl:for-each>
          </table>
        </td>
      </tr>
    </xsl:for-each>
  </xsl:template>

</xsl:stylesheet>
