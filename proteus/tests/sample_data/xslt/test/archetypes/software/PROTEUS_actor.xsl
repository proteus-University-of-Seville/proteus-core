<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_actor.xsl                              -->
<!-- Content : PROTEUS XSLT for subjects at US - actor        -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/07                                     -->
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

    <xsl:template match="object[@classes='software-requirement actor']">

        <div id="{@id}"  data-proteus-id="{@id}">
            <table class="actor remus_table">

                <!-- Header, version, authors and sources -->
                <xsl:call-template name="generate_software_requirement_expanded_header">
                    <xsl:with-param name="label"   select="properties/codeProperty[@name=':Proteus-code']"/>
                    <xsl:with-param name="class"   select="'actor'"/>
                </xsl:call-template>

                <!-- Description -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"     select="$proteus:lang_description"/>
                    <xsl:with-param name="content"   select="properties/markdownProperty[@name='description']"/>
                    <xsl:with-param name="mandatory" select="true()"/>
                </xsl:call-template>

                <!-- Priority rows -->
                <xsl:call-template name="generate_priority_rows"/>

                <!-- Comments -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"   select="$proteus:lang_comments"/>
                    <xsl:with-param name="content" select="properties/markdownProperty[@name='comments']"/>
                </xsl:call-template>
            </table>
        </div>
    </xsl:template>

</xsl:stylesheet>
