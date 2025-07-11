<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_stakeholder.xsl                        -->
<!-- Content : PROTEUS XSLT for subjects at US - stakeholder  -->
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
    <!-- proteus:stakeholder template                  -->
    <!-- ============================================= -->

    <xsl:template match="object[@classes='stakeholder']">

        <div id="{@id}"  data-proteus-id="{@id}">
            <table class="stakeholder remus_table">

                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="$proteus:lang_stakeholder"/>
                    <xsl:with-param name="class"   select="'stakeholder'"/>
                </xsl:call-template>

                <!-- Organization -->
                <xsl:variable name="organization_content" select="properties/traceProperty[@name='works-for']" />
                <xsl:choose>
                    <xsl:when test="$organization_content/trace">
                        <xsl:call-template name="generate_trace_row">
                            <xsl:with-param name="label"   select="$proteus:lang_organization"/>
                            <xsl:with-param name="content" select="$organization_content"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <tr>
                            <th><xsl:value-of select="$proteus:lang_organization"/></th>
                            <td>
                                <span><xsl:value-of select="$proteus:lang_freelance"/></span>
                            </td>
                        </tr>
                    </xsl:otherwise>
                </xsl:choose>

                <!-- Role -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"     select="$proteus:lang_role"/>
                    <xsl:with-param name="content"   select="properties/stringProperty[@name='role']"/>
                    <xsl:with-param name="mandatory" select="true()"/>
                </xsl:call-template>

                <!-- Category -->
                <xsl:if test="properties/enumProperty[@name='category'] != 'nd'">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="label"   select="$proteus:lang_category"/>
                        <xsl:with-param name="content" select="properties/enumProperty[@name='category']"/>
                    </xsl:call-template>
                </xsl:if>

                <!-- Comments -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"   select="$proteus:lang_comments"/>
                    <xsl:with-param name="content" select="properties/markdownProperty[@name='comments']"/>
                </xsl:call-template>

            </table>
        </div>
    </xsl:template>

</xsl:stylesheet>
