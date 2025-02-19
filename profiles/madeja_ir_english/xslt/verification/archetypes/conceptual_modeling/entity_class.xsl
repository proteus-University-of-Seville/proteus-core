<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : entity_class.xsl                               -->
<!-- Content : PROTEUS default XSLT for entity-class          -->
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
    <!-- entity-class template                          -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'entity-class')]">

        <div id="{@id}" data-proteus-id="{@id}" class="entity_class">

            <table class="entity_class remus_table">
                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="properties/*[@name=':Proteus-code']"/>
                    <xsl:with-param name="class"   select="'entity-class'"/>
                </xsl:call-template>

                <!-- Entity information -->
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
    <!-- entity-class template (code mode)              -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'entity-class')]" mode="code">

        <!-- Description -->
        <xsl:variable name="description" select="properties/*[@name='description']"/>
        <xsl:if test="string-length($description)">
            <xsl:call-template name="generate-code-description">
                <xsl:with-param name="multiline-comment" select="true()"/>
            </xsl:call-template>
        </xsl:if>

        <!-- Class declaration -->
        <xsl:variable name="is_abstract">
            <xsl:if test="properties/*[@name='is-abstract'] = 'true'">abstract </xsl:if>
        </xsl:variable>

        <span class="keyword">
            <xsl:value-of select="$is_abstract"/>
            <xsl:text>class </xsl:text>
        </span>
        <span class="class_name {$is_abstract}">
            <xsl:value-of select="properties/*[@name=':Proteus-name']"/>
        </span>

        <!-- superclass -->
        <xsl:variable name="superclass-trace" select="properties/*[@name='superclass']/trace"/>

        <xsl:if test="$superclass-trace">
            <span class="keyword"> specializes </span>
            <span class="class_name">
            <xsl:for-each select="$superclass-trace">
                <xsl:variable name="target_id" select="@target" />
                <xsl:variable name="target_object" select="//object[@id = $target_id]" />

                <a href="#{$target_id}">
                    <xsl:value-of select="$target_object/properties/*[@name=':Proteus-name']" />
                </a>
            </xsl:for-each>
            </span>
        </xsl:if>

        <!-- Open bracket -->
        <br></br>
        <xsl:text>{</xsl:text>

        <!-- Attributes -->
        <xsl:if test="children/object[contains(@classes,'attribute')]">
            <!--
            <br></br>
            <div class="code_comment code_header"><xsl:value-of select="$proteus:lang_code_attributes"/></div>
            -->
            <ul class="properties">
                <xsl:apply-templates select="children/object[contains(@classes,'attribute')]" mode="code"/>
            </ul>
        </xsl:if>

        <!-- Close bracket -->
        <xsl:if test="not(children/object[contains(@classes,'attribute')])">
            <br></br>
        </xsl:if>
        <xsl:text>}</xsl:text>

    </xsl:template>

    <!-- ============================================== -->
    <!-- attribute template                             -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'attribute')]" mode="code">

        <li id="{@id}" data-proteus-id="{@id}" class="property">

            <xsl:value-of select="properties/*[@name=':Proteus-name']"/>
            <xsl:text>: </xsl:text>
            <xsl:value-of select="properties/*[@name='type']"/>

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

    <!-- ============================================== -->
    <!-- Helper templates                               -->
    <!-- ============================================== -->

    <!-- description -->
    <xsl:template name="generate-code-description">
        <xsl:param name="multiline-comment" select="false()"/>
        <xsl:param name="content" select="properties/markdownProperty[@name='description']"/>

        <xsl:choose>
            <xsl:when test="string-length($content)">
                <div>
                <span class="code_comment">/**</span>
                <xsl:if test="$multiline-comment">
                    <br></br>
                </xsl:if>
                <ul class="properties">
                    <span class="code_comment code_description">
                        <xsl:call-template name="generate_markdown">
                            <xsl:with-param name="content" select="$content"/>
                        </xsl:call-template>
                    </span>
                </ul>
                <span class="code_comment">*/</span>
            </div>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>