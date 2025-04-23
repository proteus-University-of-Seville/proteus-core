<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : cover.xsl                                      -->
<!-- Content : PROTEUS XSLT for subjects at US - cover        -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/09                                     -->
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
    <xsl:template name="document_cover">
        <div id="{@id}"  data-proteus-id="{@id}">
            <div id="document_cover">


                <div id="project_name">
                    <xsl:value-of select="$proteus:lang_project"/>
                    <xsl:text> </xsl:text>
                    <xsl:value-of select="parent::*/parent::*/properties/stringProperty[@name=':Proteus-name']"/>
                </div>

                <div id="document_logo">
                    <img alt="Universidad de Sevilla" src="templates:///verification/resources/images/logo_us.gif"/>
                </div>

                <div id="document_name">
                    <xsl:apply-templates select="properties/stringProperty[@name=':Proteus-name']"/>
                </div>

                <div id="document_version">
                    <xsl:value-of select="$proteus:lang_version"/>
                    <xsl:text> </xsl:text>
                    <xsl:value-of select="properties/stringProperty[@name='version']"/>
                </div>

                <div id="document_date">
                    <xsl:value-of select="$proteus:lang_date"/>
                    <xsl:text> </xsl:text>
                    <xsl:value-of select="properties/dateProperty[@name=':Proteus-date']"/>
                </div>

                <div id="document_prepared_for">
                    <xsl:value-of select="$proteus:lang_prepared_for"/>
                    <xsl:text> </xsl:text>

                    <xsl:choose>
                        <xsl:when test="not(properties/traceProperty[@name='prepared-for']/trace)">
                            <p class="tbd">?</p>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select="properties/traceProperty[@name='prepared-for']" mode="paragraph"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </div>

                <div id="document_prepared_by">
                    <xsl:value-of select="$proteus:lang_prepared_by"/>
                    <xsl:text> </xsl:text>

                    <xsl:choose>
                        <xsl:when test="not(properties/traceProperty[@name='prepared-by']/trace)">
                            <p class="tbd">?</p>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select="properties/traceProperty[@name='prepared-by']" mode="paragraph"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </div>
            </div>
        </div>
    </xsl:template>
</xsl:stylesheet>