<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : generate_table.xsl                             -->
<!-- Content : PROTEUS default XSLT for generating tables     -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/24                                     -->
<!-- Version : 2.5                                            -->
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
    <xsl:param name="excluded_properties" select="',:Proteus-name,:Proteus-code,:Proteus-date,version,authors,sources,'"/>
    <xsl:param name="included_properties"/>

    <!-- Objects with a :Proteus-code (e.g. madeja's requirements engineering -->
    <!-- archetypes) show it in brackets before the name, instead of as a     -->
    <!-- separate property row, to keep the pill compact.                     -->
    <xsl:param name="code" select="properties/*[@name=':Proteus-code']"/>

    <!-- Extension points for archetypes that need extra rows the generic    -->
    <!-- property loop cannot produce (e.g. a reordered subset of properties -->
    <!-- interleaved with a custom block, or children rendered as something  -->
    <!-- other than nested cards). Both are markup (result tree fragments),  -->
    <!-- built by the caller before calling this template.                  -->
    <!-- - extra_rows_before: inserted right before the automatic property   -->
    <!--   loop, e.g. to show some properties out of their declaration order -->
    <!--   and/or interleaved with a custom block (see madeja's use_case.xsl -->
    <!--   for the "ordinary sequence" step table).                         -->
    <!-- - extra_rows: inserted where the children row normally goes, e.g.   -->
    <!--   to show children in a compact list instead of full nested cards  -->
    <!--   (see madeja's information_requirement.xsl).                     -->
    <!-- - show_children: set to false() when extra_rows already covers the  -->
    <!--   children, so the default nested-card rendering is skipped.       -->
    <xsl:param name="extra_rows_before"/>
    <xsl:param name="extra_rows"/>
    <xsl:param name="show_children" select="true()"/>

    <!-- Image shown in the upper right corner of the object, if any.     -->
    <!-- Organizations use 'logo' and stakeholders use 'photo'. An        -->
    <!-- archetype may pass a different property in this parameter.       -->
    <xsl:param name="image"
      select="properties/fileProperty[@name='logo' or @name='photo'][normalize-space() != '']"
    />

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
                <span class="object_code"><xsl:value-of select="$code"/></span>
              </xsl:if>
              <xsl:value-of select="$name"/>
              <xsl:if test="$postfix">
                <xsl:text></xsl:text>
                <xsl:value-of select="$postfix"/>
              </xsl:if>
            </th>
          </tr>
        </thead>

        <xsl:copy-of select="$extra_rows_before"/>

        <!-- Table body with properties -->
        <!-- By wrapping both the list and the current property name with commas, we    -->
        <!-- ensure we're matching whole names and not partial strings.                 -->
        <!-- This was suggested by Claude AI.                                           -->
        <xsl:for-each select="properties/*[not(contains($all_excluded_properties,concat(',', @name, ',')))]">
          <xsl:call-template name="generate_property_row">
            <xsl:with-param name="included" select="contains($included_properties,concat(',', current()/@name, ','))"/>
            <xsl:with-param name="span" select="$span"/>
          </xsl:call-template>
        </xsl:for-each>

        <xsl:copy-of select="$extra_rows"/>

        <!-- Render the children objects recursively -->
        <xsl:if test="$show_children">
          <xsl:call-template name="renderChildren">
            <xsl:with-param name="children" select="children/*" />
            <xsl:with-param name="span" select="$span" />
          </xsl:call-template>
        </xsl:if>
      </table>
    </div>
  </xsl:template>

  <!-- ============================================= -->
  <!-- renderChildren template                       -->
  <!-- ============================================= -->

  <!-- Children, if any, are shown in a single row: a label cell and, next  -->
  <!-- to it, one nested object card per child, generated by calling        -->
  <!-- generate_table recursively. Since each child card goes through this  -->
  <!-- same template again, children of children are rendered the same way -->
  <!-- with no extra code, however many levels deep they go.                -->

  <xsl:template name="renderChildren">
    <xsl:param name="children" />
    <xsl:param name="span" select="1"/>

    <xsl:if test="$children">
      <tr class="children_row">
        <th>
          <xsl:value-of select="proteus-utils:i18n('xslt.children')"/>
        </th>
        <td colspan="{$span}" class="children_column">
          <xsl:for-each select="$children">
            <xsl:call-template name="generate_table"/>
          </xsl:for-each>
        </td>
      </tr>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>
