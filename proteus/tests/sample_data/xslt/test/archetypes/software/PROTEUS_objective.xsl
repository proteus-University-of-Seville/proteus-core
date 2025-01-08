<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_objective.xsl                          -->
<!-- Content : PROTEUS XSLT for subjects at US - objective    -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/08/02                                     -->
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
    <!-- Objective template                             -->
    <!-- ============================================== -->
    <!-- Note the use of colspan=2                      -->

    <xsl:template match="object[@classes='software-requirement objective']">
        <xsl:variable name="span" select="2" />

        <div id="{@id}"  data-proteus-id="{@id}">
            <table class="objective remus_table">

                <!-- Header, version, authors and sources -->
                <xsl:call-template name="generate_software_requirement_expanded_header">
                    <xsl:with-param name="label"   select="properties/codeProperty[@name=':Proteus-code']"/>
                    <xsl:with-param name="class" select="'objective'" />
                    <xsl:with-param name="span" select="$span" />
                </xsl:call-template>

                <!-- Description -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"     select="$proteus:lang_description"/>
                    <xsl:with-param name="content"   select="properties/markdownProperty[@name='description']"/>
                    <xsl:with-param name="mandatory" select="true()"/>
                    <xsl:with-param name="span" select="$span" />
                </xsl:call-template>

                <!-- Subobjectives -->
                <!-- check if there are children otherwise do nothing -->
                <xsl:if test="children/object">
                    <tr>
                        <th>
                            <xsl:value-of select="$proteus:lang_subobjectives" />
                        </th>
                        <td colspan="{$span}">
                            <ul class="subobjectives">
                                <xsl:for-each select="children/object">
                                    <xsl:call-template name="generate_subobjective"/>
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
    <!-- Subobjective template                          -->
    <!-- ============================================== -->

    <xsl:template name="generate_subobjective">
        <!-- Label number -->
        <xsl:variable name="label_number">
            <xsl:value-of select="properties/codeProperty[@name = ':Proteus-code']/prefix" />
            <xsl:value-of select="properties/codeProperty[@name = ':Proteus-code']/number" />
            <xsl:value-of select="properties/codeProperty[@name = ':Proteus-code']/suffix" />
        </xsl:variable>

        <div id="{@id}"  data-proteus-id="{@id}">
            <!-- Current objective -->
            <xsl:variable name="description" select="properties/markdownProperty[@name='description']" />

            <li>
                <strong>
                    <xsl:value-of select="concat('[',$label_number,']')" />
                    <xsl:text> </xsl:text>
                    <xsl:value-of select="properties/stringProperty[@name=':Proteus-name']" />
                </strong>
                <xsl:text> : </xsl:text>
                
                <xsl:choose>
                    <xsl:when test="not(string-length(normalize-space($description)) > 0)">
                        <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$description" />
                    </xsl:otherwise>
                </xsl:choose>
            </li>

            <!-- Nested objectives -->
            <xsl:if test="children/object">
                <ul class="subobjectives">
                    <xsl:for-each select="children/object">
                        <xsl:call-template name="generate_subobjective"/>
                    </xsl:for-each>
                </ul>
            </xsl:if>
        </div>
    </xsl:template>

</xsl:stylesheet>