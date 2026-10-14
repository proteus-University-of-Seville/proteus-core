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
    <!-- Wide properties (see generate_property_row) keep their name and their     -->
    <!-- content in the same cell. The alternative that was discarded put the name  -->
    <!-- in a row of its own, and the content in the row below it: in HTML, a th   -->
    <!-- with colspan and then a td with colspan; in LaTeX, two \multicolumn rows,  -->
    <!-- the first one ending with \* so that it is not separated from its content. -->
    <!-- Properties shown at the full width of the table (see generate_property_row) -->
    <xsl:param name="wide_properties" select="',diagram,'"/>
    <xsl:param name="code" select="properties/*[@name=':Proteus-code']"/>
    <xsl:param name="extra_rows_before"/>
    <xsl:param name="extra_rows"/>
    <xsl:param name="show_children" select="true()"/>

    <!-- Children are shown in a row, as nested object cards              -->
    <!-- (children_style 'cards') or as a compact list with the code (if   -->
    <!-- any), the name and the description of each child, nested if the   -->
    <!-- children have children ('list'). children_label_key is the i18n   -->
    <!-- key of the label of the row. The row is at the end of the table   -->
    <!-- (children_position 'end') or, in a list, right after the          -->
    <!-- description row, if there is one ('after_description').           -->
    <xsl:param name="children_style" select="'cards'"/>
    <xsl:param name="children_label_key" select="'xslt.children'"/>
    <xsl:param name="children_position" select="'end'"/>
    <xsl:param name="image"
      select="properties/fileProperty[@name='logo' or @name='photo'][normalize-space() != '']"
    />

    <!-- The corner image is not shown again as a property row. The       -->
    <!-- 'width' property is not shown either when the object has a file  -->
    <!-- property: it only sets the image size (see the fileProperty      -->
    <!-- template in properties.xsl), it is not content of the object.    -->
    <!-- 'dependencies' is never shown, whatever the excluded properties  -->
    <!-- an archetype passes: the traceability matrix is the way of       -->
    <!-- showing them in a document.                                      -->
    <xsl:variable name="all_excluded_properties">
      <xsl:value-of select="$excluded_properties"/>
      <xsl:text>dependencies,</xsl:text>
      <xsl:if test="$image">
        <xsl:value-of select="concat($image[1]/@name, ',')"/>
      </xsl:if>
      <xsl:if test="properties/fileProperty">
        <xsl:text>width,</xsl:text>
      </xsl:if>
    </xsl:variable>

    <!-- True if the list of children is shown right after the description -->
    <xsl:variable name="children_after_description" select="
      $show_children
      and $children_style = 'list'
      and $children_position = 'after_description'
      and boolean(children/object)
      and boolean(properties/*[@name='description'])
      and not(contains($all_excluded_properties, ',description,'))
    "/>

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
        <xsl:with-param name="wide" select="contains($wide_properties,concat(',', current()/@name, ','))"/>
      </xsl:call-template>

      <!-- Children right after the description -->
      <xsl:if test="$children_after_description and @name='description'">
        <xsl:call-template name="renderChildrenListRow">
          <xsl:with-param name="children" select="../../children/object"/>
          <xsl:with-param name="label_key" select="$children_label_key"/>
        </xsl:call-template>
      </xsl:if>
    </xsl:for-each>

    <xsl:value-of select="$extra_rows"/>

    <!-- Children as a compact list, in a row at the end of the table -->
    <xsl:if test="$show_children and $children_style = 'list' and children/object and not($children_after_description)">
      <xsl:call-template name="renderChildrenListRow">
        <xsl:with-param name="children" select="children/object"/>
        <xsl:with-param name="label_key" select="$children_label_key"/>
      </xsl:call-template>
    </xsl:if>

    <xsl:text>\end{xltabular}\ProteusCardEnd&#10;</xsl:text>

    <!-- Render the children objects recursively, below the card, unless -->
    <!-- they are shown as a list inside it                               -->
    <xsl:if test="$show_children and $children_style != 'list'">
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

  <!-- ============================================= -->
  <!-- renderChildrenListRow template                -->
  <!-- ============================================= -->

  <!-- Row of the table with the label and the list of children -->

  <xsl:template name="renderChildrenListRow">
    <xsl:param name="children" />
    <xsl:param name="label_key" select="'xslt.children'"/>

    <xsl:call-template name="label"><xsl:with-param name="key" select="$label_key"/></xsl:call-template>
    <xsl:text> &amp; </xsl:text>
    <xsl:call-template name="renderChildrenItems">
      <xsl:with-param name="children" select="$children"/>
    </xsl:call-template>
    <xsl:text> \\ \hline&#10;</xsl:text>
  </xsl:template>

  <!-- ============================================= -->
  <!-- renderChildrenItems template                  -->
  <!-- ============================================= -->

  <!-- Compact list of objects: "[code] name: description" per item, with -->
  <!-- the code only if the object has one and the description only if it -->
  <!-- is not empty. The children of the objects are shown in nested       -->
  <!-- lists.                                                              -->

  <xsl:template name="renderChildrenItems">
    <xsl:param name="children" />

    <xsl:text>\begin{itemize}&#10;</xsl:text>
    <xsl:for-each select="$children">
      <xsl:variable name="code" select="properties/*[@name=':Proteus-code']"/>
      <xsl:variable name="description" select="properties/*[@name='description']"/>
      <!-- The paragraph must start before the anchor (\phantomsection), -->
      <!-- or it adds an empty line above the item                       -->
      <xsl:text>\item\leavevmode</xsl:text>
      <xsl:call-template name="anchor"/>
      <xsl:if test="$code">
        <xsl:text>\textcolor{proteusaccent}{\texttt{[</xsl:text>
        <xsl:call-template name="tex"><xsl:with-param name="text" select="$code"/></xsl:call-template>
        <xsl:text>]}} </xsl:text>
      </xsl:if>
      <xsl:text>\textbf{</xsl:text>
      <xsl:call-template name="tex">
        <xsl:with-param name="text" select="properties/*[@name=':Proteus-name']"/>
      </xsl:call-template>
      <xsl:text>}</xsl:text>
      <xsl:if test="normalize-space($description) != ''">
        <xsl:text>: </xsl:text>
        <xsl:call-template name="generate_markdown">
          <xsl:with-param name="content" select="$description"/>
        </xsl:call-template>
      </xsl:if>
      <xsl:text>&#10;</xsl:text>
      <xsl:if test="children/object">
        <xsl:call-template name="renderChildrenItems">
          <xsl:with-param name="children" select="children/object"/>
        </xsl:call-template>
      </xsl:if>
    </xsl:for-each>
    <xsl:text>\end{itemize}&#10;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
