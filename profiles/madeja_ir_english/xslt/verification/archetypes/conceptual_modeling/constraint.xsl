<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : constraint.xsl                                -->
<!-- Content : PROTEUS default XSLT for constraint           -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2024/11/07                                     -->
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
    <!-- ============================================== -->
    <!-- constraint template                            -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'constraint')]">

        <div id="{@id}" data-proteus-id="{@id}" class="constraint">

            <table class="constraint remus_table">
                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="properties/*[@name=':Proteus-code']"/>
                    <xsl:with-param name="class"   select="'constraint'"/>
                </xsl:call-template>

                <!-- Constraint information -->
                <tr>
                    <td colspan="2">
                        <div class="code">
                            <xsl:apply-templates select="." mode="code"/>
                        </div>
                    </td>
                </tr>

                <!-- Comments -->
                <xsl:for-each select="properties/*[@name='comments']">
                    <xsl:call-template name="generate_property_row"/>
                </xsl:for-each>
            </table>
        </div>
    </xsl:template>

    <!-- ============================================== -->
    <!-- constraint template (code mode)                -->
    <!-- ============================================== -->

    <!-- TODO: create a template for modeling object's names -->

    <xsl:template match="object[contains(@classes,'constraint')]" mode="code">

        <!-- constraint declaration -->
        <span class="keyword">
            <xsl:text>constraint </xsl:text>
        </span>
        <span class="class_name">
            <xsl:value-of select="properties/*[@name=':Proteus-name']"/>
        </span>

        <xsl:if test="properties/*[@name='constrained-elements']/trace">
            <span class="keyword">
                <xsl:text> constrains </xsl:text>
            </span>
                <xsl:for-each select="properties/*[@name='constrained-elements']/trace">
                    <xsl:variable name="target_id" select="@target" />
                    <xsl:variable name="target_object" select="//object[@id=$target_id]" />
                    <xsl:variable name="target_name">
                        <xsl:choose>
                            <xsl:when test="contains($target_object/@classes,'association')">
                                <xsl:for-each select="$target_object">
                                    <xsl:call-template name="generate-association-name"/>
                                </xsl:for-each>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$target_object/properties/*[@name=':Proteus-name']"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>

                    <xsl:if test="$target_object">
                        <a href="#{$target_id}" onclick="selectAndNavigate(`{$target_id}`, event)">
                            <xsl:value-of select="$target_name"/>
                        </a>
                        <xsl:if test="not(position()=last())">, </xsl:if>
                    </xsl:if>
                </xsl:for-each>
        </xsl:if>

        <!-- Open bracket -->
        <br></br>
        <xsl:text>{</xsl:text>
        <br></br>

        <!-- constraint description -->
        <xsl:variable name="description" select="properties/*[@name='description']"/>
        <xsl:if test="string-length($description)">
            <ul class="properties">
                <xsl:call-template name="generate_markdown">
                    <xsl:with-param name="content" select="$description"/>
                </xsl:call-template>
            </ul>
        </xsl:if>

        <!-- Close bracket -->
        <xsl:text>}</xsl:text>

    </xsl:template>

</xsl:stylesheet>