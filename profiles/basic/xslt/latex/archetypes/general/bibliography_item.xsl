<?xml version="1.0" encoding="utf-8"?>

<!-- ================================================================== -->
<!-- File    : bibliography_item.xsl                                    -->
<!-- Content : PROTEUS LaTeX XSLT for bibliography item                 -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/10/07                                               -->
<!-- Version : 1.1                                                      -->
<!-- ================================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <!-- ================================================================ -->
  <!-- NOTE #1
       The bibliography-item template has priority="2" to avoid being
       overridden by the glossary-item template, which is its superclass.

       NOTE #2
       Bibliography items are LaTeX bibliography entries:
       \ProteusBibItem[<name>]{<id>} (a \bibitem, see proteus.sty) inside a
       proteusbibliography list. The label is the item name, as in the HTML
       view, and \cite{<id>} prints it in brackets. Citations are generated
       by the links to bibliography items of the document: glossary
       highlighting of their names in Markdown texts and traces (see
       generate_markdown and trace_target).

       Consecutive bibliography items share one list: the first one opens
       it and the last one closes it. A bibliography item rendered alone
       (standalone, e.g. by a symbolic link) opens and closes its own list.
  -->
  <!-- ================================================================ -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' bibliography-item ')]"
    name="bibliography_item_template"
    priority="2"
  >
    <xsl:param name="standalone" select="false()"/>

    <xsl:variable name="first"
      select="$standalone or not(preceding-sibling::object[1][contains(concat(' ', normalize-space(@classes), ' '),' bibliography-item ')])"/>
    <xsl:variable name="last"
      select="$standalone or not(following-sibling::object[1][contains(concat(' ', normalize-space(@classes), ' '),' bibliography-item ')])"/>

    <xsl:if test="$first">
      <xsl:text>&#10;\begin{proteusbibliography}</xsl:text>
    </xsl:if>

    <!-- \ProteusBibItem[name]{id} authors. details. -->
    <xsl:text>&#10;\ProteusBibItem[</xsl:text>
    <xsl:call-template name="tex">
      <xsl:with-param name="text" select="properties/*[@name=':Proteus-name']"/>
    </xsl:call-template>
    <xsl:text>]{</xsl:text>
    <xsl:value-of select="@id"/>
    <xsl:text>}</xsl:text>
    <xsl:call-template name="anchor"/>
    <xsl:text> </xsl:text>
    <xsl:call-template name="tex">
      <xsl:with-param name="text" select="properties/*[@name='publication_authors']"/>
    </xsl:call-template>
    <xsl:text>. </xsl:text>
    <xsl:call-template name="generate_markdown">
      <xsl:with-param name="content" select="properties/*[@name='publication_details']"/>
    </xsl:call-template>
    <xsl:text>&#10;</xsl:text>

    <xsl:if test="$last">
      <xsl:text>\end{proteusbibliography}&#10;</xsl:text>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>
