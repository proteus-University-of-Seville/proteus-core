<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_main.xsl                               -->
<!-- Content : PROTEUS XSLT for subjects at US - main file    -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/09                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->

<!-- ======================================================== -->
<!-- exclude-result-prefixes="proteus" must be set in all     -->
<!-- files to avoid xmlsn:proteus="." to appear in HTML tags. -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:proteus="http://proteus.us.es"
    xmlns:proteus-utils="http://proteus.us.es/utils"
    exclude-result-prefixes="proteus proteus-utils"
>

    <!-- Output -->
    <xsl:output method="html"
        doctype-public="XSLT-compat"
        omit-xml-declaration="yes"
        encoding="iso-8859-1"
        indent="yes"
    />

    <!-- Template includes -->
    <xsl:include href="PROTEUS_utilities.xsl" />
    <xsl:include href="PROTEUS_properties.xsl" />
    <xsl:include href="PROTEUS_cover.xsl" />
    <xsl:include href="PROTEUS_document.xsl" />

    <xsl:include href="archetypes/general/PROTEUS_section.xsl" />
    <xsl:include href="archetypes/general/PROTEUS_paragraph.xsl" />
    <xsl:include href="archetypes/general/PROTEUS_glossary_item.xsl" />
    <xsl:include href="archetypes/software/PROTEUS_actor.xsl" />
    <xsl:include href="archetypes/general/PROTEUS_graphic_file.xsl" />
    <xsl:include href="archetypes/general/PROTEUS_external_resource.xsl" />
    <xsl:include href="archetypes/PROTEUS_default.xsl" />
    <xsl:include href="archetypes/software/PROTEUS_information_requirement.xsl" />
    <xsl:include href="archetypes/software/PROTEUS_objective.xsl" />
    <xsl:include href="archetypes/software/PROTEUS_use_case.xsl" />
    <xsl:include href="archetypes/software/PROTEUS_constraint.xsl" />
    <xsl:include href="archetypes/software/PROTEUS_functional_requirement.xsl" />
    <xsl:include href="archetypes/software/PROTEUS_nonfunctional_requirement.xsl" />
    <xsl:include href="archetypes/general/PROTEUS_organization.xsl" />
    <xsl:include href="archetypes/general/PROTEUS_stakeholder.xsl" />
    <xsl:include href="archetypes/general/PROTEUS_meeting.xsl" />
    <xsl:include href="archetypes/general/PROTEUS_archetype_link.xsl" />
    <xsl:include href="archetypes/software/PROTEUS_object_type.xsl" />
    <xsl:include href="archetypes/software/PROTEUS_association_type.xsl" />
    <xsl:include href="archetypes/madeja/PROTEUS_business_actor.xsl" />
    <xsl:include href="archetypes/madeja/PROTEUS_business_process.xsl" />
    <xsl:include href="archetypes/madeja/PROTEUS_strength.xsl" />
    <xsl:include href="archetypes/madeja/PROTEUS_weakness.xsl" />
    <xsl:include href="archetypes/madeja/PROTEUS_user_story.xsl" />

    <xsl:template match="project">
        <xsl:variable name="currentDocumentId" select="proteus-utils:current_document()"/>
        <xsl:for-each select="documents">
            <xsl:if test="object[@id=$currentDocumentId]">
                <xsl:apply-templates select="object[@id=$currentDocumentId]"/>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>

</xsl:stylesheet>