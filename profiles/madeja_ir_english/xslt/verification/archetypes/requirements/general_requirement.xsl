<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : general-requirement.xsl                        -->
<!-- Content : PROTEUS default XSLT for general-requirement   -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/08/02                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/10/10 (Amador Durán)                      -->
<!-- objective -> general-requirement                         -->
<!-- Code simplification.                                     -->
<!-- ======================================================== -->
<!-- Update  : 2024/10/19 (Amador Durán)                      -->
<!-- authors and sources must appear before description.      -->
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
    <!-- ============================================== -->
    <!-- general-requirement template                   -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'general-requirement')]">
        <!-- By wrapping both the list and the current property name with commas, -->
        <!-- we ensure we're matching whole names and not partial strings.        -->
        <!-- This was suggested by Claude AI.                                     -->

        <!-- List of excluded properties (not shown) -->
        <xsl:variable name="excluded_properties">,:Proteus-code,:Proteus-name,:Proteus-date,version,authors,sources,description,dependencies,ai_verification_date,ai_verification_time,ai_verification_output,</xsl:variable>

        <!-- List of mandatory properties (shown even if they are empty)-->
        <xsl:variable name="mandatory_properties">,importance,priority,</xsl:variable>
        

        <div id="{@id}" data-proteus-id="{@id}">
            <table class="general_requirement remus_table">
                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label" select="properties/*[@name=':Proteus-code']"/>
                    <xsl:with-param name="class" select="'general-requirement'"/>
                </xsl:call-template>

                <!-- Version row -->
                <xsl:call-template name="generate_version_row"/>

                <!-- Authors and sources rows -->
                <xsl:for-each select="properties/*[@name='authors' or @name='sources']">
                    <xsl:call-template name="generate_property_row"/>
                </xsl:for-each>

                <!-- Description row -->
                <xsl:for-each select="properties/*[@name='description']">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="mandatory" select="true()"/>
                        <xsl:with-param name="verifiable" select="true()"/>
                    </xsl:call-template>
                </xsl:for-each>

                <!-- Child requirements row -->
                <xsl:call-template name="generate_children_row">
                    <xsl:with-param name="label" select="$proteus:lang_child_requirements"/>
                    <xsl:with-param name="verifiable" select="true()"/>
                </xsl:call-template>

                <!-- Generate rows for all other properties                           -->
                <!-- Each property can be accessed as current() in the called template -->
                <xsl:for-each select="properties/*[not(contains($excluded_properties,concat(',', @name, ',')))]">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="mandatory" select="contains($mandatory_properties,concat(',', current()/@name, ','))"/>
                    </xsl:call-template>
                </xsl:for-each>

                <xsl:call-template name="generate_ai_verification_row"/>
            </table>
        </div>
    </xsl:template>

</xsl:stylesheet>