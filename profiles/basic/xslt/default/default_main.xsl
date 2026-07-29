<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : default_main.xsl                               -->
<!-- Content : PROTEUS default XSLT main file                 -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/09                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/08 (Amador Durán)                      -->
<!-- encoding="iso-8859-1" -> enconding="utf-8"               -->
<!-- graphic_file -> local_resource                           -->
<!-- external_resource -> remote_resource                     -->
<!-- archetype_link -> symbolic_link                          -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/13 (Amador Durán)                      -->
<!-- Document loop simplified.                                -->
<!-- Added dictionaries and keys for property and enum labels -->
<!-- Use of EXSLT node-set function to overcome some XLST 1.0 -->
<!-- limitations.                                             -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/14 (Amador Durán)                      -->
<!-- key() does not work on variables in lxml.                -->
<!-- ======================================================== -->
<!-- Update  : 2026/07/29 (Amador Durán)                      -->
<!-- Renamed and refactored.                                  -->
<!-- ======================================================== -->

<!-- ======================================================== -->
<!-- exclude-result-prefixes="proteus" must be set in all     -->
<!-- files to avoid xmlsn:proteus="." to appear in HTML tags. -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
  exclude-result-prefixes="proteus proteus-utils"
  extension-element-prefixes="exsl"
>
  <!-- Output -->
  <xsl:output method="html"
      doctype-public="XSLT-compat"
      omit-xml-declaration="yes"
      encoding="utf-8"
      indent="yes"
  />

  <!-- Language-independent dictionaries -->
  <xsl:include href="labels/property_labels.xsl"/>
  <xsl:include href="labels/enumeration_labels.xsl"/>
  <xsl:include href="labels/trace_type_labels.xsl"/>

  <!-- XSLT core modules -->
  <xsl:include href="core/utilities.xsl" />
  <xsl:include href="core/properties.xsl" />
  <xsl:include href="core/cover.xsl" />
  <xsl:include href="core/document.xsl" />

  <!-- XSLT archetype modules -->
  <xsl:include href="archetypes/general/section.xsl" />
  <xsl:include href="archetypes/general/appendix.xsl" />
  <xsl:include href="archetypes/general/paragraph.xsl" />
  <xsl:include href="archetypes/general/glossary_item.xsl" />
  <xsl:include href="archetypes/general/figure.xsl" />
  <xsl:include href="archetypes/general/organization.xsl" />
  <xsl:include href="archetypes/general/stakeholder.xsl" />
  <xsl:include href="archetypes/general/symbolic_link.xsl" />

  <xsl:include href="archetypes/default.xsl" />

  <xsl:template match="project">
      <xsl:variable name="currentDocumentId" select="proteus-utils:current_document()"/>
      <xsl:apply-templates select="documents/object[@id=$currentDocumentId]"/>
  </xsl:template>

</xsl:stylesheet>