<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : default.xsl                                    -->
<!-- Content : PROTEUS default XSLT template (entry point)    -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/16                                     -->
<!-- Version : 2.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2026/09/16 (Amador Durán & Claude Code)        -->
<!-- i18n redesigned: label dictionaries and per-language     -->
<!-- entry points have been removed. Localized strings are    -->
<!-- now retrieved with the proteus-utils:i18n() extension    -->
<!-- function from the profile i18n YAML files, so this       -->
<!-- template is language-independent and new archetypes can  -->
<!-- provide their own labels without modifying any XSLT      -->
<!-- file. See documentation/i18n_design.md.                  -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <!-- Output -->
  <xsl:output
    method="html"
    doctype-system="about:legacy-compat"
    omit-xml-declaration="yes" encoding="utf-8" indent="yes"
  />

  <!-- Core modules -->
  <xsl:include href="core/utilities.xsl" />
  <xsl:include href="core/generate_table.xsl" />
  <xsl:include href="core/properties.xsl" />
  <xsl:include href="core/cover.xsl" />
  <xsl:include href="core/document.xsl" />

  <!-- General archetype modules -->
  <xsl:include href="archetypes/general/section.xsl" />
  <xsl:include href="archetypes/general/appendix.xsl" />
  <xsl:include href="archetypes/general/paragraph.xsl" />
  <xsl:include href="archetypes/general/comment.xsl" />
  <xsl:include href="archetypes/general/glossary_item.xsl" />
  <xsl:include href="archetypes/general/bibliography_item.xsl" />
  <xsl:include href="archetypes/general/figure.xsl" />
  <xsl:include href="archetypes/general/symbolic_link.xsl" />

  <!-- Advanced archetype modules -->
  <xsl:include href="archetypes/advanced/organization.xsl" />
  <xsl:include href="archetypes/advanced/stakeholder.xsl" />
  <xsl:include href="archetypes/advanced/meeting.xsl" />
  <xsl:include href="archetypes/advanced/traceability_matrix.xsl" />

  <!-- Default archetype module -->
  <xsl:include href="archetypes/any_archetype.xsl" />

  <!-- It matches the XML root (project) and applies templates to the current document -->
  <xsl:template match="project">
    <xsl:variable name="currentDocumentId" select="proteus-utils:current_document()"/>
    <xsl:apply-templates select="documents/object[@id=$currentDocumentId]"/>
  </xsl:template>

</xsl:stylesheet>
