<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : stakeholder.xsl                                -->
<!-- Content : PROTEUS default XSLT for stakeholder           -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/07                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/09 (Amador Durán)                      -->
<!-- match must be object[ends-with(@classes,'stakeholder')]  -->
<!-- To check if an object is of a given class:               -->
<!--    object[contains(@classes,class_name)]                 -->
<!-- To check if an object is of a given final class:         -->
<!--    object[ends-with(@classes,class_name)]                -->
<!-- PROBLEM: XSLT 1.0 does not include ends-with             -->
<!-- archetype-link -> symbolic-link                          -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/13 (Amador Durán)                      -->
<!-- Review after integration of trace properties in the list -->
<!-- of properties.                                           -->
<!-- Simplification using excluded and mandatory property     -->
<!-- list and property and enum dictionaries using key().     -->
<!-- Use of EXSLT node-set function to overcome some XLST 1.0 -->
<!-- limitations.                                             -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/14 (Amador Durán)                      -->
<!-- key() does not work on variables in lxml.                -->
<!-- Code simplification.                                     -->
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
    <!-- stakeholder template                          -->
    <!-- ============================================= -->

    <xsl:template match="object[contains(@classes,'stakeholder')]">
        <div id="{@id}" data-proteus-id="{@id}">
            <table class="stakeholder remus_table">

                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label" select="$proteus:lang_stakeholder"/>
                    <xsl:with-param name="class" select="'stakeholder'"/>
                </xsl:call-template>

                <!-- By wrapping both the list and the current property name with commas, -->
                <!-- we ensure we're matching whole names and not partial strings.        -->
                <!-- This was suggested by Claude AI (https://claude.ai/).                -->

                <!-- List of excluded properties (not shown or shown as a special case) -->
                <xsl:variable name="excluded_properties">,:Proteus-name,:Proteus-date,version,works-for,authors,sources</xsl:variable>

                <!-- List of mandatory properties (shown even if they are empty)-->
                <xsl:variable name="mandatory_properties">,works-for,category,role,</xsl:variable>

                <!-- Generate row for organization (works-for)                           -->
                <!-- This trace property must show 'freelance' when empty (special case) -->
                <xsl:variable name="organization_property" select="exsl:node-set(properties/*[@name='works-for'])" />
                <xsl:variable name="is_freelance" select="not($organization_property/trace)"/>

                <xsl:for-each select="properties/traceProperty[@name='works-for']">
                    <xsl:choose>
                        <xsl:when test="$is_freelance">
                            <xsl:call-template name="generate_property_row">
                                <xsl:with-param name="alternative" select="$proteus:lang_freelance"/>
                                <xsl:with-param name="mandatory" select="contains($mandatory_properties,concat(',', current()/@name, ','))"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="generate_property_row">
                                <xsl:with-param name="mandatory" select="contains($mandatory_properties,concat(',', current()/@name, ','))"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>

                <!-- Generate rows for all other properties -->
                <xsl:for-each select="properties/*[not(contains($excluded_properties,concat(',', @name, ',')))]">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="mandatory" select="contains($mandatory_properties,concat(',', current()/@name, ','))"/>
                    </xsl:call-template>
                </xsl:for-each>

            </table>
        </div>
    </xsl:template>

</xsl:stylesheet>
