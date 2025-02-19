<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_default.xsl                            -->
<!-- Content : PROTEUS XSLT for subjects at US - default      -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/09                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->

<!-- ======================================================== -->
<!-- exclude-result-prefixes="proteus" must be set in all     -->
<!-- files to avoid xmlsn:proteus="." to appear in HTML tags. -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:proteus="http://proteus.lsi.us.es">
    <!-- Match any object -->
    <xsl:template match="object">

        <div id="{@id}" data-proteus-id="{@id}">
            <!-- Display properties in a table -->
            <table class="remus_table">
                <tr style="background-color: powderblue;">
                    <th style="width: 17.5%;">Property Name</th>
                    <th style="width: 82.5%;">Text Value</th>
                </tr>
                <!-- Call the named template to handle properties -->
                <xsl:call-template name="renderProperties">
                    <xsl:with-param name="properties" select="properties/*" />
                </xsl:call-template>

                <!-- Render the children objects recursively -->
                <xsl:call-template name="renderChildren">
                    <xsl:with-param name="children" select="children/*" />
                </xsl:call-template>
            </table>
        </div>
    </xsl:template>

    <!-- Named template to render properties -->
    <xsl:template name="renderProperties">
        <xsl:param name="properties" />
        <xsl:for-each select="$properties">
            <tr>
                <td style="width: 17.5%;"><strong><xsl:value-of select="@name"/></strong></td>
                <td style="width: 82.5%;"><xsl:value-of select="."/></td>
            </tr>
        </xsl:for-each>
    </xsl:template>

    <!-- Named template to render children -->
    <xsl:template name="renderChildren">
        <xsl:param name="children" />

        <xsl:for-each select="$children">
            <!-- Child name -->
            <tr>
                <td style="background-color: lightgray;">
                    <strong>
                        <xsl:value-of select="properties/stringProperty[@name=':Proteus-name']"/>
                    </strong>
                </td>

                <td >
                    <table  id="{@id}"
                            style="margin: 0; margin-bottom: 0; width: 100%;"
                            data-proteus-id="{@id}"
                        >
                        <xsl:call-template name="renderProperties">
                            <xsl:with-param name="properties" select="properties/*" />
                        </xsl:call-template>
                    </table>
                </td>
            </tr>
        </xsl:for-each>
    </xsl:template>
</xsl:stylesheet>
