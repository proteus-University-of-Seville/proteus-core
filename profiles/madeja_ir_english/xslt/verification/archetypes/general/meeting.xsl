<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : meeting.xsl                                    -->
<!-- Content : PROTEUS default XSLT for meeting               -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/12/08                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/09 (Amador Durán)                      -->
<!-- match must be object[ends-with(@classes,'meeting')]      -->
<!-- To check if an object is of a given class:               -->
<!--    object[contains(@classes,class_name)]                 -->
<!-- To check if an object is of a given final class:         -->
<!--    object[ends-with(@classes,class_name)]                -->
<!-- PROBLEM: XSLT 1.0 does not include ends-with             -->
<!-- archetype-link -> symbolic-link                          -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/14 (Amador Durán)                      -->
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
>
    <!-- ============================================= -->
    <!-- meeting template                              -->
    <!-- ============================================= -->

    <xsl:template match="object[contains(@classes,'meeting')]">

        <div id="{@id}" data-proteus-id="{@id}">
            <table class="meeting remus_table">
                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="$proteus:lang_meeting"/>
                    <xsl:with-param name="class"   select="'meeting'"/>
                </xsl:call-template>

                <!-- By wrapping both the list and the current property name with commas, -->
                <!-- we ensure we're matching whole names and not partial strings.        -->
                <!-- This was suggested by Claude AI (https://claude.ai/).                -->

                <!-- List of excluded properties (not shown or shown as a special case) -->
                <xsl:variable name="excluded_properties">,:Proteus-name,version,authors,</xsl:variable>

                <!-- List of mandatory properties (shown even if they are empty)-->
                <xsl:variable name="mandatory_properties">,:Proteus-date,date,time,place,attenders,results,</xsl:variable>

                <!-- Generate rows for all ordinary properties                         -->
                <!-- Each property can be accessed as current() in the called template -->
                <xsl:for-each select="properties/*[not(contains($excluded_properties,concat(',', @name, ',')))]">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="mandatory" select="contains($mandatory_properties,concat(',', current()/@name, ','))"/>
                    </xsl:call-template>
                </xsl:for-each>

            </table>
        </div>
    </xsl:template>

</xsl:stylesheet>
