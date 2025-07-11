<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_meeting.xsl                            -->
<!-- Content : PROTEUS XSLT for subjects at US - meeting      -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/12/08                                     -->
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

    <!-- ============================================= -->
    <!-- proteus:actor template                        -->
    <!-- ============================================= -->

    <xsl:template match="object[@classes='meeting']">

        <div id="{@id}"  data-proteus-id="{@id}">
            <table class="meeting remus_table">

                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="$proteus:lang_meeting"/>
                    <xsl:with-param name="class"   select="'meeting'"/>
                </xsl:call-template>

                <!-- Date -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"   select="$proteus:lang_date"/>
                    <xsl:with-param name="content" select="properties/dateProperty[@name=':Proteus-date']"/>
                </xsl:call-template>

                <!-- Time -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"   select="$proteus:lang_time"/>
                    <xsl:with-param name="content" select="properties/timeProperty[@name='time']"/>
                </xsl:call-template>

                <!-- Place -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"   select="$proteus:lang_place"/>
                    <xsl:with-param name="content" select="properties/stringProperty[@name='place']"/>
                    <xsl:with-param name="mandatory" select="true()"/>
                </xsl:call-template>

                <!-- Attenders -->
                <xsl:call-template name="generate_trace_row">
                    <xsl:with-param name="label"   select="$proteus:lang_attenders"/>
                    <xsl:with-param name="content" select="properties/traceProperty[@name='attenders']"/>
                    <xsl:with-param name="mandatory" select="true()"/>
                </xsl:call-template>

                <!-- Results -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"   select="$proteus:lang_results"/>
                    <xsl:with-param name="content" select="properties/markdownProperty[@name='results']"/>
                    <xsl:with-param name="mandatory" select="true()"/>
                </xsl:call-template>

                <!-- Comments -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"   select="$proteus:lang_comments"/>
                    <xsl:with-param name="content" select="properties/markdownProperty[@name='comments']"/>
                </xsl:call-template>

            </table>
        </div>
    </xsl:template>

</xsl:stylesheet>
