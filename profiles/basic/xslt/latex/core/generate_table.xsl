<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : generate_table.xsl                             -->
<!-- Content : PROTEUS LaTeX XSLT for generating tables       -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/10/07                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->

<!-- ________________________________________________________ -->
<!-- | icon label    | [code] name (suffix)          image  | -->
<!-- |______________________________________________________| -->
<!-- | property name | property value                       | -->
<!-- | ...           | ...                                  | -->
<!-- |______________________________________________________| -->
<!--     children (indented cards)                            -->

<!-- Same parameters as generate_table in the default         -->
<!-- template, so that archetype modules can be ported        -->
<!-- easily. The card is an xltabular (a long table that can  -->
<!-- break across pages); its header row is repeated on every -->
<!-- page. Long tables cannot be nested in table cells, so    -->
<!-- children are rendered below the card, indented, instead  -->
<!-- of in a "children" row.                                  -->
<!--                                                          -->
<!-- extra_rows_before and extra_rows are LaTeX text: rows    -->
<!-- written as 'label & value \\ \hline'.                    -->

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
    <xsl:param name="postfix"/>
    <xsl:param name="excluded_properties" select="',:Proteus-name,:Proteus-code,:Proteus-date,version,authors,sources,'"/>
    <xsl:param name="included_properties"/>
    <xsl:param name="code" select="properties/*[@name=':Proteus-code']"/>
    <xsl:param name="extra_rows_before"/>
    <xsl:param name="extra_rows"/>
    <xsl:param name="show_children" select="true()"/>
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

    <!-- Accent colour of the archetype (see proteus.sty) and anchor -->
    <xsl:text>&#10;\ProteusUseAccent{</xsl:text>
    <xsl:value-of select="$class"/>
    <xsl:text>}</xsl:text>
    <xsl:call-template name="anchor"/>
    <xsl:text>&#10;\begin{xltabular}{\ProteusTableWidth}{|L|Q|}&#10;\hline&#10;</xsl:text>

    <!-- Header row: class icon and label, code, name and image -->
    <xsl:text>\ProteusHeaderRow{</xsl:text>
    <xsl:value-of select="$class"/>
    <xsl:text>}{</xsl:text>
    <xsl:call-template name="label"><xsl:with-param name="key" select="concat('archetype.class.', $class)"/></xsl:call-template>
    <xsl:text>}{</xsl:text>
    <xsl:call-template name="tex"><xsl:with-param name="text" select="$code"/></xsl:call-template>
    <xsl:text>}{</xsl:text>
    <xsl:call-template name="tex"><xsl:with-param name="text" select="$name"/></xsl:call-template>
    <xsl:call-template name="tex"><xsl:with-param name="text" select="$postfix"/></xsl:call-template>
    <xsl:if test="$image">
      <xsl:text>\ProteusObjectImage{assets/</xsl:text>
      <xsl:value-of select="normalize-space($image[1])"/>
      <xsl:text>}</xsl:text>
    </xsl:if>
    <xsl:text>}&#10;\endhead&#10;</xsl:text>

    <xsl:value-of select="$extra_rows_before"/>

    <!-- Property rows. By wrapping both the list and the current property -->
    <!-- name with commas, we ensure we're matching whole names.           -->
    <xsl:for-each select="properties/*[not(contains($all_excluded_properties,concat(',', @name, ',')))]">
      <xsl:call-template name="generate_property_row">
        <xsl:with-param name="included" select="contains($included_properties,concat(',', current()/@name, ','))"/>
      </xsl:call-template>
    </xsl:for-each>

    <xsl:value-of select="$extra_rows"/>

    <xsl:text>\end{xltabular}\ProteusCardEnd&#10;</xsl:text>

    <!-- Render the children objects recursively, below the card -->
    <xsl:if test="$show_children">
      <xsl:call-template name="renderChildren">
        <xsl:with-param name="children" select="children/object" />
      </xsl:call-template>
    </xsl:if>
  </xsl:template>

  <!-- ============================================= -->
  <!-- renderChildren template                       -->
  <!-- ============================================= -->

  <xsl:template name="renderChildren">
    <xsl:param name="children" />

    <xsl:if test="$children">
      <xsl:text>\begin{adjustwidth}{1.5em}{0pt}&#10;\ProteusChildren{</xsl:text>
      <xsl:call-template name="label"><xsl:with-param name="key" select="'xslt.children'"/></xsl:call-template>
      <xsl:text>}&#10;</xsl:text>
      <xsl:for-each select="$children">
        <xsl:call-template name="generate_table"/>
      </xsl:for-each>
      <xsl:text>\end{adjustwidth}&#10;</xsl:text>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>
