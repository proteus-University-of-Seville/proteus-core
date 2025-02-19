<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : change_request.xsl                             -->
<!-- Content : PROTEUS default XSLT for change-request        -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2024/11/22                                     -->
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
    xmlns:exsl="http://exslt.org/common"
    extension-element-prefixes="exsl"
>
    <!-- ============================================= -->
    <!-- change-request template                  -->
    <!-- ============================================= -->

    <xsl:template match="object[contains(@classes,'defect')]">

        <div id="{@id}" data-proteus-id="{@id}">

            <table class="change_request remus_table">
                <!-- Postfix using defect-type -->
                <xsl:variable name="defect-type" select="properties/*[@name='defect-type']"/>
                <xsl:variable name="postfix">
                    <xsl:text>(</xsl:text>
                    <xsl:value-of select="$defect_type_labels/label[@key=$defect-type]"/>
                    <xsl:text>)</xsl:text>
                </xsl:variable>

                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="properties/*[@name=':Proteus-code']"/>
                    <xsl:with-param name="class"   select="'defect'"/>
                    <xsl:with-param name="postfix" select="$postfix"/>
                </xsl:call-template>

                <!-- Version row -->
                <xsl:call-template name="generate_version_row"/>
            
                <!-- By wrapping both the list and the current property name with commas, -->
                <!-- we ensure we're matching whole names and not partial strings.        -->
                <!-- This was suggested by Claude AI.                                     -->

                <!-- List of excluded properties (not shown) -->
                <xsl:variable name="excluded_properties">,:Proteus-code,:Proteus-name,:Proteus-date,version,dependencies,defect-type,</xsl:variable>

                <!-- List of mandatory properties (shown even if they are empty)-->
                <xsl:variable name="mandatory_properties">,description,solution,trace-type,</xsl:variable>

                <!-- Generate rows for all ordinary properties                         -->
                <!-- Each property can be accessed as current() in the called template -->
                <xsl:for-each select="properties/*[not(contains($excluded_properties,concat(',', @name, ',')))]">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="mandatory" select="contains($mandatory_properties,concat(',', current()/@name, ','))"/>
                    </xsl:call-template>
                </xsl:for-each>


                <!-- Indirectly affected objects calculation -->

                <!-- Extract trace types -->
                <xsl:variable name="trace-types">
                    <xsl:for-each  select="properties/*[@name='trace-type']/type">
                        <xsl:value-of select="normalize-space(.)"/>
                        <xsl:text> </xsl:text>
                    </xsl:for-each>
                </xsl:variable>

                <!-- Extract analyzed objects ids (directly affected) -->
                <xsl:variable name="directly-affected-objects">
                    <xsl:for-each select="properties/*[@name='directly-affected-objects']/trace">
                        <xsl:value-of select="@target"/>
                        <xsl:text> </xsl:text>
                    </xsl:for-each>
                </xsl:variable>

                <!-- Extract analyzed objects ids (indirectly affected) -->
                <xsl:variable name="indirectly-affected-objects" select="proteus-utils:impactAnalyzer._calculate_impact($directly-affected-objects,$trace-types)"/>

                <!-- Display indirectly affected objects -->
                <tr>
                    <th colspan="1">
                        <xsl:value-of select="$proteus:lang_indirectly_affected_objects"/>
                    </th>
                    <td>
                        <xsl:if test="not($indirectly-affected-objects)">
                            <span class="tbd"><xsl:value-of select="$proteus:lang_none"/></span>
                        </xsl:if>
                        <ul class="traces">
                        <xsl:for-each select="$indirectly-affected-objects">
                            <li>
                            <xsl:call-template name="generate_object_information">
                                <xsl:with-param name="object_id" select="."/>
                            </xsl:call-template>
                            </li>
                        </xsl:for-each>
                        </ul>
                    </td>
                </tr>

            </table>
        </div>
    </xsl:template>

    <!-- Defect type enumeration dictionary -->
    <!-- Since this is defect archetype exclusive, we store this here to keep main file clean -->
    <xsl:variable name="defect_type_enum_dictionary">
        <label key="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></label>
        <label key="ambiguity"><xsl:value-of select="$proteus:lang_defect_type_ambiguity"/></label>
        <label key="no-necessity"><xsl:value-of select="$proteus:lang_defect_type_no_necessity"/></label>
        <label key="no-understanding"><xsl:value-of select="$proteus:lang_defect_type_no_understanding"/></label>
        <label key="no-verificability"><xsl:value-of select="$proteus:lang_defect_type_no_verificability"/></label>
        <label key="no-consistency"><xsl:value-of select="$proteus:lang_defect_type_no_consistency"/></label>
        <label key="no-achievability"><xsl:value-of select="$proteus:lang_defect_type_no_achievability"/></label>
        <label key="verbosity"><xsl:value-of select="$proteus:lang_defect_type_verbosity"/></label>
        <label key="design-dependence"><xsl:value-of select="$proteus:lang_defect_type_design_dependence"/></label>
        <label key="redundancy"><xsl:value-of select="$proteus:lang_defect_type_redundancy"/></label>
        <label key="imprecision"><xsl:value-of select="$proteus:lang_defect_type_imprecision"/></label>
        <label key="no-completeness"><xsl:value-of select="$proteus:lang_defect_type_no_completeness"/></label>
        <label key="no-priority"><xsl:value-of select="$proteus:lang_defect_type_no_priority"/></label>
        <label key="no-stability"><xsl:value-of select="$proteus:lang_defect_type_no_stability"/></label>
        <label key="wrong-lod"><xsl:value-of select="$proteus:lang_defect_type_wrong_lod"/></label>
        <label key="no-traceability"><xsl:value-of select="$proteus:lang_defect_type_no_traceability"/></label>
        <label key="wrong-org"><xsl:value-of select="$proteus:lang_defect_type_wrong_org"/></label>
        <label key="other"><xsl:value-of select="$proteus:lang_defect_type_other"/></label>
    </xsl:variable>

    <xsl:variable name="defect_type_labels" select="exsl:node-set($defect_type_enum_dictionary)"/>

</xsl:stylesheet>