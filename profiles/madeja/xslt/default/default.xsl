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

  <!-- Archetype modules, one per archetype, grouped by the same category -->
  <!-- folders used in archetypes/<lang>/objects/. Files with no template -->
  <!-- uncommented are extension points: the object falls back to        -->
  <!-- any_archetype.xsl until someone gives it a custom rendering.       -->

  <!-- 00_general -->
  <xsl:include href="archetypes/general/section.xsl" />
  <xsl:include href="archetypes/general/appendix.xsl" />
  <xsl:include href="archetypes/general/paragraph.xsl" />
  <xsl:include href="archetypes/general/comment.xsl" />
  <xsl:include href="archetypes/general/glossary_item.xsl" />
  <xsl:include href="archetypes/general/bibliography_item.xsl" />
  <xsl:include href="archetypes/general/figure.xsl" />
  <xsl:include href="archetypes/general/symbolic_link.xsl" />
  <xsl:include href="archetypes/general/organization.xsl" />
  <xsl:include href="archetypes/general/stakeholder.xsl" />
  <xsl:include href="archetypes/general/meeting.xsl" />

  <!-- 01_business_analysis -->
  <xsl:include href="archetypes/business_analysis/business_actor.xsl" />
  <xsl:include href="archetypes/business_analysis/business_objective.xsl" />
  <xsl:include href="archetypes/business_analysis/business_process.xsl" />
  <xsl:include href="archetypes/business_analysis/strength.xsl" />
  <xsl:include href="archetypes/business_analysis/weakness.xsl" />
  <xsl:include href="archetypes/business_analysis/user_story.xsl" />

  <!-- 02_requirements -->
  <xsl:include href="archetypes/requirements/business_rule.xsl" />
  <xsl:include href="archetypes/requirements/functional_requirement.xsl" />
  <xsl:include href="archetypes/requirements/general_requirement.xsl" />
  <xsl:include href="archetypes/requirements/information_requirement.xsl" />
  <xsl:include href="archetypes/requirements/nonfunctional_requirement.xsl" />
  <xsl:include href="archetypes/requirements/specific_data.xsl" />
  <xsl:include href="archetypes/requirements/subsystem.xsl" />
  <xsl:include href="archetypes/requirements/system_actor.xsl" />
  <xsl:include href="archetypes/requirements/use_case.xsl" />
  <xsl:include href="archetypes/requirements/use_case_diagram.xsl" />
  <xsl:include href="archetypes/requirements/use_case_step.xsl" />

  <!-- 03_conceptual_modeling -->
  <xsl:include href="archetypes/conceptual_modeling/association.xsl" />
  <xsl:include href="archetypes/conceptual_modeling/attribute.xsl" />
  <xsl:include href="archetypes/conceptual_modeling/constraint.xsl" />
  <xsl:include href="archetypes/conceptual_modeling/entity_class.xsl" />
  <xsl:include href="archetypes/conceptual_modeling/enum_value.xsl" />
  <xsl:include href="archetypes/conceptual_modeling/enumeration.xsl" />
  <xsl:include href="archetypes/conceptual_modeling/mockup.xsl" />
  <xsl:include href="archetypes/conceptual_modeling/parameter.xsl" />
  <xsl:include href="archetypes/conceptual_modeling/role.xsl" />
  <xsl:include href="archetypes/conceptual_modeling/system_operation.xsl" />

  <!-- 04_req_management -->
  <xsl:include href="archetypes/req_management/change_request.xsl" />
  <xsl:include href="archetypes/req_management/conflict.xsl" />
  <xsl:include href="archetypes/req_management/defect.xsl" />
  <xsl:include href="archetypes/req_management/traceability_matrix.xsl" />

  <!-- Default archetype module -->
  <xsl:include href="archetypes/any_archetype.xsl" />

  <!-- It matches the XML root (project) and applies templates to the current document -->
  <xsl:template match="project">
    <xsl:variable name="currentDocumentId" select="proteus-utils:current_document()"/>
    <xsl:apply-templates select="documents/object[@id=$currentDocumentId]"/>
  </xsl:template>

</xsl:stylesheet>
