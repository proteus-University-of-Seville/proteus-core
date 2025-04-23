<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : use_case.xsl                                   -->
<!-- Content : PROTEUS default XSLT for use-case              -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/08/10                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/10/19 (Amador Durán)                      -->
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
    <!-- use-case template                              -->
    <!-- ============================================== -->
    <!-- Note the use of two class names in match due   -->
    <!-- to the lack of ends-with function in XSLT 1.0. -->

    <xsl:template match="object[contains(@classes,'software-requirement use-case')]">
        <!-- By wrapping both the list and the current property name with commas, -->
        <!-- we ensure we're matching whole names and not partial strings.        -->
        <!-- This was suggested by Claude AI.                                     -->

        <!-- List of excluded properties (not shown) -->
        <xsl:variable name="excluded_properties">,:Proteus-code,:Proteus-name,:Proteus-date,version,authors,sources,precondition,description,postcondition,dependencies,ai_verification_date,ai_verification_time,ai_verification_output,</xsl:variable>

        <!-- List of mandatory properties (shown even if they are empty)-->
        <xsl:variable name="mandatory_properties"></xsl:variable>

        <!-- Note the use of colspan=2 -->
        <xsl:variable name="span" select="2" />

        <div id="{@id}" data-proteus-id="{@id}">
            <table class="use_case remus_table">
                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="properties/*[@name=':Proteus-code']"/>
                    <xsl:with-param name="class"   select="'use-case'"/>
                    <xsl:with-param name="span" select="$span" />
                </xsl:call-template>

                <!-- Version row -->
                <xsl:call-template name="generate_version_row">
                    <xsl:with-param name="span" select="$span" />
                </xsl:call-template>

                <!-- Authors and sources rows -->
                <xsl:for-each select="properties/*[@name='authors' or @name='sources']">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="span" select="$span" />
                    </xsl:call-template>
                </xsl:for-each>

                <!-- Precondition row -->
                <xsl:for-each select="properties/*[@name='precondition']">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="mandatory" select="true()"/>
                        <xsl:with-param name="span" select="$span" />
                        <xsl:with-param name="verifiable" select="true()"/>
                    </xsl:call-template>
                </xsl:for-each>

                <!-- Description row -->
                <xsl:for-each select="properties/*[@name='description']">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="mandatory" select="true()"/>
                        <xsl:with-param name="span" select="$span" />
                        <xsl:with-param name="verifiable" select="true()"/>
                    </xsl:call-template>
                </xsl:for-each>

                <!-- use case steps -->
                <!-- check if there are children otherwise do nothing -->
                <xsl:if test="children/object">
                    <!-- count the number of use case step in total -->
                    <xsl:variable name="number_of_steps" select="count(children/object)" />

                    <tr>
                        <th rowspan="{$number_of_steps + 1}">
                            <xsl:value-of select="$proteus:lang_ordinary_sequence" />
                        </th>
                        <th class="step_number_column">
                            <xsl:value-of select="$proteus:lang_step" />
                        </th>
                        <th class="step_action_column">
                            <xsl:value-of select="$proteus:lang_action" />
                        </th>
                    </tr>

                    <xsl:apply-templates select="children/object" />

                </xsl:if>

                <!-- Postcondition row -->
                <xsl:for-each select="properties/*[@name='postcondition']">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="mandatory" select="true()"/>
                        <xsl:with-param name="span" select="$span" />
                        <xsl:with-param name="verifiable" select="true()"/>
                    </xsl:call-template>
                </xsl:for-each>

                <!-- Generate rows for all other properties                           -->
                <!-- Each property can be accessed as current() in the called template -->
                <xsl:for-each select="properties/*[not(contains($excluded_properties,concat(',', @name, ',')))]">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="mandatory" select="contains($mandatory_properties,concat(',', current()/@name, ','))"/>
                        <xsl:with-param name="span" select="$span" />
                    </xsl:call-template>
                </xsl:for-each>

                <xsl:call-template name="generate_ai_verification_row"/>
            </table>
        </div>
    </xsl:template>

    <!-- ============================================== -->
    <!-- Use case step template                         -->
    <!-- ============================================== -->

    <xsl:template match="object[contains(@classes,'use-case-step')]">
        <xsl:variable name="label_number">
            <xsl:number
                from="object[contains(@classes,'software-requirement use-case')]"
                count="object[contains(@classes,'use-case-step')]"
                level="any"
                format="1"
            />
        </xsl:variable>

        <xsl:variable name="description" select="properties/*[@name='description']"/>

        <tr id="{@id}" data-proteus-id="{@id}">
            <th class="step_number">
                <xsl:value-of select="$label_number"/>
            </th>
            <td colspan="1" class="verifiable-property">
                <xsl:choose>
                    <xsl:when test="not(string-length(normalize-space($description)) > 0)">
                        <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates select="$description"/>
                    </xsl:otherwise>
                </xsl:choose>
            </td>
        </tr>
    </xsl:template>

</xsl:stylesheet>