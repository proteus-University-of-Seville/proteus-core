<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : user_story.xsl                                 -->
<!-- Content : PROTEUS default XSLT for user-story            -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2024/05/28                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/19 (Amador Durán)                      -->
<!-- Code simplification.                                     -->
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
    <!-- user-story template                           -->
    <!-- ============================================= -->

    <xsl:template match="object[contains(@classes,'user-story')]">
        <xsl:variable name="as_role"   select="properties/*[@name='as-role']" />
        <xsl:variable name="i_want_to" select="properties/*[@name='i-want-to']" />
        <xsl:variable name="so_that"   select="properties/*[@name='so-that']" />

        <div id="{@id}" data-proteus-id="{@id}">
            <table class="user_story remus_table">

                <!-- Header -->
                <xsl:call-template name="generate_header">
                    <xsl:with-param name="label"   select="properties/*[@name=':Proteus-code']"/>
                    <xsl:with-param name="class"   select="'user-story'"/>
                </xsl:call-template>

                <!-- Version row -->
                <xsl:call-template name="generate_version_row"/>

                <!-- Description -->
                <tr>
                    <th>
                        <xsl:value-of select="$proteus:lang_description" />
                    </th>

                    <td>

                        <!-- As a... (mandatory) -->
                        <strong><xsl:value-of select="$proteus:lang_as_a" /></strong>
                        <xsl:text> </xsl:text>
                        <xsl:choose>
                            <xsl:when test="normalize-space($as_role)">
                                <xsl:value-of select="$as_role"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                            </xsl:otherwise>
                        </xsl:choose>
                        <br/>

                        <!-- I want to... (mandatory) -->
                        <strong><xsl:value-of select="$proteus:lang_i_want_to" /></strong>
                        <xsl:text> </xsl:text>
                        <xsl:choose>
                            <xsl:when test="normalize-space($i_want_to)">
                                <xsl:value-of select="$i_want_to"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                            </xsl:otherwise>
                        </xsl:choose>
                        <br/>

                        <!-- So that... (optional) -->
                        <xsl:if test="normalize-space($so_that)">
                            <strong><xsl:value-of select="$proteus:lang_so_that" /></strong>
                            <xsl:text> </xsl:text>
                            <xsl:value-of select="$so_that"/>
                        </xsl:if>
                    </td>
                </tr>

                <!-- By wrapping both the list and the current property name with commas, -->
                <!-- we ensure we're matching whole names and not partial strings.        -->
                <!-- This was suggested by Claude AI.                                     -->

                <!-- List of excluded properties (not shown) -->
                <xsl:variable name="excluded_properties">,:Proteus-code,:Proteus-name,:Proteus-date,version,as-role,i-want-to,so-that,dependencies,</xsl:variable>

                <!-- List of mandatory properties (shown even if they are empty)-->
                <xsl:variable name="mandatory_properties">,importance,urgency,</xsl:variable>

                <!-- Generate rows for all ordinary properties                         -->
                <!-- Each property can be accessed as current() in the called template -->
                <xsl:for-each select="properties/*[not(contains($excluded_properties,concat(',', @name, ',')))]">
                    <xsl:call-template name="generate_property_row">
                        <xsl:with-param name="mandatory" select="contains($mandatory_properties,concat(',', current()/@name, ','))"/>
                    </xsl:call-template>
                </xsl:for-each>
            </table>
        </div>
    </xsl:template>

</xsl:stylesheet>
