<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_organization.xsl                       -->
<!-- Content : PROTEUS XSLT for subjects at US - organization -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/12/07                                     -->
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
    <!-- proteus:organization template                 -->
    <!-- ============================================= -->
<!--  -->
    <xsl:template match="object[@classes='organization']">

        <div id="{@id}"  data-proteus-id="{@id}">
            <table class="organization remus_table">

                <!-- Header-->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="$proteus:lang_organization"/>
                    <xsl:with-param name="class"   select="'organization'"/>
                </xsl:call-template>

                <!-- Address -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"     select="$proteus:lang_address"/>
                    <xsl:with-param name="content"   select="properties/stringProperty[@name='address']"/>
                    <xsl:with-param name="mandatory" select="true()"/>
                </xsl:call-template>

                <!-- phone-number -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"     select="$proteus:lang_telephone"/>
                    <xsl:with-param name="content"   select="properties/stringProperty[@name='phone-number']"/>
                </xsl:call-template>

                <!-- fax -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"     select="$proteus:lang_fax"/>
                    <xsl:with-param name="content"   select="properties/stringProperty[@name='fax']"/>
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
