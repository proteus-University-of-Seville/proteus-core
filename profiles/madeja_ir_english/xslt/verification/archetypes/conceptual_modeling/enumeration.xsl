<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : enumeration.xsl                                -->
<!-- Content : PROTEUS default XSLT for enumeration           -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2024/11/02                                     -->
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
    <!-- enumeration template                           -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'enumeration')]">

        <div id="{@id}" data-proteus-id="{@id}" class="enumeration">

            <table class="enumeration remus_table">
                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="properties/*[@name=':Proteus-code']"/>
                    <xsl:with-param name="class"   select="'enumeration'"/>
                </xsl:call-template>

                <!-- enumeration information -->
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
    <!-- enumeration template (code mode)               -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'enumeration')]" mode="code">

        <!-- Description -->
        <xsl:variable name="description" select="properties/*[@name='description']"/>
        <xsl:if test="string-length($description)">
            <xsl:call-template name="generate-code-description">
                <xsl:with-param name="multiline-comment" select="true()"/>
            </xsl:call-template>
        </xsl:if>

        <!-- Enumeration declaration -->
        <span class="keyword">
            <xsl:text>enumeration </xsl:text>
        </span>
        <span class="class_name">
            <xsl:value-of select="properties/*[@name=':Proteus-name']"/>
        </span>

        <!-- Open bracket -->
        <br></br>
        <xsl:text>{</xsl:text>

        <!-- Enumeration values -->
        <xsl:if test="children/object[@classes='enum-value']">
            <!--
            <br></br>
            <div class="code_comment code_header"><xsl:value-of select="$proteus:lang_code_attributes"/></div>
            -->
            <ul class="properties">
                <xsl:apply-templates select="children/object[contains(@classes,'enum-value')]" mode="code"/>
            </ul>
        </xsl:if>

        <!-- Close bracket -->
        <xsl:if test="not(children/object[@classes='enum-value'])">
            <br></br>
        </xsl:if>
        <xsl:text>}</xsl:text>

    </xsl:template>

    <!-- ============================================== -->
    <!-- aenum-value template                           -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'enum-value')]" mode="code">

        <li id="{@id}" data-proteus-id="{@id}" class="property">

            <xsl:value-of select="properties/*[@name=':Proteus-name']"/>

            <!-- Description -->
            <xsl:variable name="description" select="properties/*[@name='description']"/>

            <xsl:if test="string-length($description)">
                <span class="code_comment code_description">
                    //
                    <xsl:call-template name="generate_markdown">
                        <xsl:with-param name="content" select="$description"/>
                    </xsl:call-template>
                </span>
            </xsl:if>

        </li>
    </xsl:template>

</xsl:stylesheet>