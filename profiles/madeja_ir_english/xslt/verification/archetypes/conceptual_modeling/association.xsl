<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : association.xsl                                -->
<!-- Content : PROTEUS defualt XSLT for association           -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/08/02                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/10/20 (Amador Durán)                      -->
<!-- Code review and refactoring.                             -->
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
    <!-- association template                           -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'association')]">

        <div id="{@id}" data-proteus-id="{@id}" class="association">

            <table class="association remus_table">

                <xsl:variable name="name">
                    <xsl:call-template name="generate-association-name"/>
                </xsl:variable>

                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label" select="properties/*[@name=':Proteus-code']"/>
                    <xsl:with-param name="class" select="'association'"/>
                    <xsl:with-param name="name"  select="$name" />
                </xsl:call-template>

                <!-- Association information -->
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
    <!-- association template (code mode)               -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'association')]" mode="code">

        <!-- Description -->
        <xsl:variable name="description" select="properties/*[@name='description']"/>
        <xsl:if test="string-length($description)">
            <xsl:call-template name="generate-code-description">
                <xsl:with-param name="multiline-comment" select="true()"/>
            </xsl:call-template>
        </xsl:if>

        <!-- Association declaration -->
        <xsl:variable name="name">
            <xsl:call-template name="generate-association-name"/>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="properties/*[@name='is-composition'] = 'true'">
                <span class="keyword">composition </span>
            </xsl:when>
            <xsl:otherwise>
                <span class="keyword">association </span>
            </xsl:otherwise>
        </xsl:choose>
        <span class="class_name"><xsl:value-of select="$name"/></span>

        <!-- Open bracket -->
        <br></br>
        <xsl:text>{</xsl:text>

        <!-- Roles -->
        <xsl:if test="children/object[@classes='role']">
            <br></br>
            <!-- <div class="code_comment code_header"><xsl:value-of select="$proteus:lang_code_roles"/></div> -->
            <ul class="properties">
                <xsl:apply-templates select="children/object[@classes='role']" mode="code"/>
            </ul>
        </xsl:if>

        <!-- Attributes -->
        <xsl:if test="children/object[@classes='attribute']">
            <br></br>
            <!-- <div class="code_comment code_header"><xsl:value-of select="$proteus:lang_code_attributes"/></div> -->
            <ul class="properties">
                <xsl:apply-templates select="children/object[@classes='attribute']" mode="code"/>
            </ul>
        </xsl:if>

        <!-- Close bracket -->
        <xsl:if test="not(children/object[@classes='attribute' or @classes='role'])">
            <br></br>
        </xsl:if>
        <xsl:text>}</xsl:text>
    </xsl:template>

    <!-- ============================================== -->
    <!-- role template                                  -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'role')]" mode="code">

        <li id="{@id}" data-proteus-id="{@id}" class="property">

            <!-- role name -->
            <xsl:value-of select="properties/*[@name=':Proteus-name']"/>
            <xsl:text>: </xsl:text>

            <!-- role type -->
            <xsl:variable name="target_id" select="properties/traceProperty[@name='type']/trace/@target"/>
            <xsl:choose>
                <xsl:when test="$target_id">
                    <xsl:variable name="target_object" select="//object[@id=$target_id]" />
                    <xsl:value-of select="$target_object/properties/*[@name=':Proteus-name']" />
                </xsl:when>
                <xsl:otherwise>
                    <span class="tbd">?</span>
                </xsl:otherwise>
            </xsl:choose>

            <!-- role multiplicity -->
            <xsl:variable name="lower-bound" select="properties/*[@name='multiplicity-lower-bound']"/>
            <xsl:variable name="upper-bound" select="properties/*[@name='multiplicity-upper-bound']"/>

            <xsl:if test="string-length($lower-bound) or string-length($upper-bound)">
                <xsl:text> [</xsl:text>

                <!-- lower bound -->
                <xsl:if test="string-length($lower-bound)">
                    <xsl:value-of select="$lower-bound"/>
                    <xsl:text>..</xsl:text>
                </xsl:if>

                <!-- upper bound -->
                <xsl:choose>
                    <xsl:when test="string-length($upper-bound)">
                        <xsl:value-of select="$upper-bound"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <span class="tbd">?</span>
                    </xsl:otherwise>
                </xsl:choose>

                <xsl:text>]</xsl:text>
            </xsl:if>

            <!-- role ordered -->
            <xsl:if test="properties/*[@name='ordered'] = 'true'">
                {<xsl:value-of select="$proteus:lang_ordered"/>}
            </xsl:if>

            <!-- role description -->
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

    <!-- ============================================== -->
    <!-- Helper templates                               -->
    <!-- ============================================== -->

    <!-- association name -->
    <xsl:template name="generate-association-name">
        <!-- Name -->
        <xsl:value-of select="properties/*[@name = ':Proteus-name']"/>

        <xsl:text>( </xsl:text>

        <!-- Get association roles -->
        <xsl:variable name="roles" select="children/object[@classes='role']"/>

        <!-- Include roles -->
        <xsl:for-each select="$roles">
            <xsl:variable name="target_id" select="properties/traceProperty[@name='type']/trace/@target"/>
            <xsl:choose>
                <xsl:when test="$target_id">
                    <xsl:variable name="target_object" select="//object[@id=$target_id]" />
                    <xsl:value-of select="$target_object/properties/*[@name=':Proteus-name']" />
                </xsl:when>
                <xsl:otherwise>
                    <span class="tbd">?</span>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>

        <xsl:choose>
            <xsl:when test="not($roles)">?, ?</xsl:when>
            <xsl:when test="count($roles) = 1">, ?</xsl:when>
        </xsl:choose>

        <xsl:text> )</xsl:text>

    </xsl:template>

</xsl:stylesheet>