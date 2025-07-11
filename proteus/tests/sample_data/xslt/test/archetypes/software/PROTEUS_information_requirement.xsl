<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_information_requirement.xsl            -->
<!-- Content : PROTEUS XSLT for subjects at US - information  -->
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

    <!-- ============================================== -->
    <!-- Information Requirement template            -->
    <!-- ============================================== -->
    <!-- Note the use of colspan=2                      -->

    <xsl:template match="object[@classes='software-requirement information-requirement']">
        <xsl:variable name="span" select="2"/>

        <div id="{@id}"  data-proteus-id="{@id}">
            <table class="information_requirement remus_table">

                <!-- Header, version, authors and sources -->
                <xsl:call-template name="generate_software_requirement_expanded_header">
                    <xsl:with-param name="label"   select="properties/codeProperty[@name=':Proteus-code']"/>
                    <xsl:with-param name="class" select="'informationRequirement'" />
                    <xsl:with-param name="span" select="$span" />
                </xsl:call-template>

                <!-- Description -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"     select="$proteus:lang_description"/>
                    <xsl:with-param name="content"   select="properties/markdownProperty[@name='description']"/>
                    <xsl:with-param name="mandatory" select="true()"/>
                    <xsl:with-param name="span" select="$span" />
                </xsl:call-template>

                <!-- specific data -->
                <!-- check if there are children otherwise do nothing -->
                <xsl:if test="children/object">
                    <tr>
                        <th>
                            <xsl:value-of select="$proteus:lang_specific_data" />
                        </th>
                        <td colspan="{$span}">
                            <ul class="specific_data">
                                <xsl:for-each select="children/object">
                                    <xsl:call-template name="generate_specificdata"/>
                                </xsl:for-each>
                            </ul>
                        </td>
                    </tr>
                </xsl:if>

                <!-- Priority rows -->
                <xsl:call-template name="generate_priority_rows">
                    <xsl:with-param name="span" select="$span" />
                </xsl:call-template>

                <!-- Comments -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"   select="$proteus:lang_comments"/>
                    <xsl:with-param name="content" select="properties/markdownProperty[@name='comments']"/>
                    <xsl:with-param name="span" select="$span" />
                </xsl:call-template>

            </table>
        </div>
    </xsl:template>

    <!-- ============================================== -->
    <!-- Specific data template                         -->
    <!-- ============================================== -->

    <xsl:template name="generate_specificdata">
        <div id="{@id}"  data-proteus-id="{@id}">
            <xsl:variable name="description" select="properties/markdownProperty[@name='description']" />

            <li>
                <xsl:choose>
                    <xsl:when test="not(string-length(normalize-space($description)) > 0)">
                        <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$description" />
                    </xsl:otherwise>
                </xsl:choose>
            </li>
        </div>
    </xsl:template>

</xsl:stylesheet>
