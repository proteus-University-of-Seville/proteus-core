<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : system-actor.xsl                               -->
<!-- Content : PROTEUS default XSLT for system-actor          -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/07                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/10/11 (Amador Durán)                      -->
<!-- match must be object[ends-with(@classes,'actor')]        -->
<!-- To check if an object is of a given class:               -->
<!--    object[contains(@classes,class_name)]                 -->
<!-- To check if an object is of a given final class:         -->
<!--    object[ends-with(@classes,class_name)]                -->
<!-- PROBLEM: XSLT 1.0 does not include ends-with.            -->
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
    <!-- system-actor template                         -->
    <!-- ============================================= -->

    <xsl:template match="object[contains(@classes,'system-actor')]">
        <div id="{@id}" data-proteus-id="{@id}">
            <table class="system_actor remus_table">
                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="properties/*[@name=':Proteus-code']"/>
                    <xsl:with-param name="class"   select="'system-actor'"/>
                </xsl:call-template>

                <!-- Version row -->
                <xsl:call-template name="generate_version_row"/>

                <!-- By wrapping both the list and the current property name with commas, -->
                <!-- we ensure we're matching whole names and not partial strings.        -->
                <!-- This was suggested by Claude AI.                                     -->

                <!-- List of excluded properties (not shown) -->
                <xsl:variable name="excluded_properties">,:Proteus-code,:Proteus-name,:Proteus-date,version,dependencies,ai_verification_date,ai_verification_time,ai_verification_output,</xsl:variable>

                <!-- List of mandatory properties (shown even if they are empty)-->
                <xsl:variable name="mandatory_properties">,description,</xsl:variable>

                <!-- List of properties that will be marked as verifiable -->
                <xsl:variable name="verifiable_properties">,description,</xsl:variable>

                <!-- Generate rows for all ordinary properties                         -->
                <!-- Each property can be accessed as current() in the called template -->
                <xsl:for-each select="properties/*[not(contains($excluded_properties,concat(',', @name, ',')))]">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="mandatory" select="contains($mandatory_properties,concat(',', current()/@name, ','))"/>
                        <xsl:with-param name="verifiable" select="contains($verifiable_properties,concat(',', current()/@name, ','))"/>
                    </xsl:call-template>
                </xsl:for-each>

                <xsl:call-template name="generate_ai_verification_row"/>
            </table>
        </div>
    </xsl:template>

</xsl:stylesheet>
