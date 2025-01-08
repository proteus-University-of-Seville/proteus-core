<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_user_story.xsl                         -->
<!-- Content : PROTEUS XSLT for subjects at US - user story   -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2024/05/28                                     -->
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
    <!-- proteus:user-story template                   -->
    <!-- ============================================= -->

    <xsl:template match="object[@classes='madeja user-story']">

        <div id="{@id}"  data-proteus-id="{@id}">
            <table class="madeja_object remus_table">

                <!-- Header, version, authors and sources -->
                <xsl:call-template name="generate_software_requirement_expanded_header">
                    <xsl:with-param name="label"   select="properties/codeProperty[@name=':Proteus-code']"/>
                    <xsl:with-param name="class"   select="'madejaUserStory'"/>
                </xsl:call-template>

                <!-- Description -->
                <tr>
                    <th>
                        <xsl:value-of select="$proteus:lang_description" />
                    </th>
                    <td>
                        <strong><xsl:value-of select="$proteus:lang_hu_as_a" /></strong>
                        <xsl:text> </xsl:text>
                        <xsl:choose>
                            <xsl:when test="properties/stringProperty[@name='as-role']">
                                <xsl:value-of select="properties/stringProperty[@name='as-role']"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                            </xsl:otherwise>
                        </xsl:choose>
                        <br/>

                        <strong><xsl:value-of select="$proteus:lang_hu_i_want_to" /></strong>
                        <xsl:text> </xsl:text>
                        <xsl:choose>
                            <xsl:when test="properties/markdownProperty[@name='i-want-to']">
                                <xsl:value-of select="properties/markdownProperty[@name='i-want-to']"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                            </xsl:otherwise>
                        </xsl:choose>
                        <br/>

                        <strong><xsl:value-of select="$proteus:lang_hu_so_that" /></strong>
                        <xsl:text> </xsl:text>
                        <xsl:choose>
                            <xsl:when test="properties/markdownProperty[@name='so-that']">
                                <xsl:value-of select="properties/markdownProperty[@name='so-that']"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                            </xsl:otherwise>
                        </xsl:choose>
                    </td>
                </tr>

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
