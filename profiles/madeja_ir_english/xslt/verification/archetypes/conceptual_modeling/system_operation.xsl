<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : system_operation.xsl                           -->
<!-- Content : PROTEUS default XSLT for system-operation      -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2024/11/05                                     -->
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
    <!-- system-operation template                      -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'system-operation')]">

        <div id="{@id}" data-proteus-id="{@id}" class="system_operation">

            <table class="system_operation remus_table">
                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="properties/*[@name=':Proteus-code']"/>
                    <xsl:with-param name="class"   select="'system-operation'"/>
                </xsl:call-template>

                <!-- System operation information -->
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
    <!-- system-operation template (code mode)          -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'system-operation')]" mode="code">

        <!-- Description -->
        <xsl:variable name="description" select="properties/*[@name='description']"/>
        <xsl:if test="string-length($description)">
            <xsl:call-template name="generate-code-description">
                <xsl:with-param name="multiline-comment" select="true()"/>
            </xsl:call-template>
        </xsl:if>

        <!-- System operation declaration -->
        <span class="keyword">
            <xsl:text>sysop </xsl:text>
        </span>
        <span class="class_name">
            <xsl:value-of select="properties/*[@name=':Proteus-name']"/>
        </span>
        <xsl:variable name="result_type" select="properties/*[@name='result-type']"/>
        <xsl:if test="string-length($result_type)">
            <xsl:text> : </xsl:text>
            <xsl:value-of select="$result_type"/>
        </xsl:if>

        <!-- Open parenthesis -->
        <xsl:text>(</xsl:text>

        <!-- Parameters -->
        <xsl:if test="children/object[contains(@classes,'parameter')]">
            <ul class="properties">
                <xsl:apply-templates select="children/object[contains(@classes,'parameter')]" mode="code"/>
            </ul>
        </xsl:if>

        <!-- Close parenthesis -->
        <xsl:text>)</xsl:text>

        <!-- Open bracket -->
        <br></br>
        <xsl:text>{</xsl:text>

        <!-- Precondition -->
        <xsl:variable name="precondition" select="properties/*[@name='precondition']"/>
        <xsl:if test="string-length($precondition)">
            <br></br>
            <div class="code_header">
                <span class="keyword">precondition:</span>
            </div>
            <ul class="properties">
                <span class="code_description">
                    <xsl:call-template name="generate_markdown">
                        <xsl:with-param name="content" select="$precondition"/>
                    </xsl:call-template>
                </span>
            </ul>
        </xsl:if>

        <!-- Postconditions -->
        <xsl:variable name="postcondition" select="properties/*[@name='postcondition']"/>
        <xsl:if test="string-length($postcondition)">
            <br></br>
            <div class="code_header">
                <span class="keyword">postcondition:</span>
            </div>
            <ul class="properties">
                <span class="code_description">
                    <xsl:call-template name="generate_markdown">
                        <xsl:with-param name="content" select="$postcondition"/>
                    </xsl:call-template>
                </span>
            </ul>
        </xsl:if>

        <!-- Exceptions -->

        <!-- Close bracket -->
        <xsl:text>}</xsl:text>

    </xsl:template>

    <!-- ============================================== -->
    <!-- parameter template                             -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'parameter')]" mode="code">

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

</xsl:stylesheet>