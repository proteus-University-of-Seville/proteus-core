<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_external_resource                      -->
<!-- Content : PROTEUS XSLT for subjects at US - ext resource -->
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

<!-- ======================================================== -->
<!-- External resource template                               -->
<!-- ======================================================== -->

<xsl:template match="object[@classes='external-resource']">

    <div id="{@id}"  data-proteus-id="{@id}">
        <div class="figure">
            <!-- Get file link -->
            <xsl:variable name="file-link" select="properties/urlProperty[@name='url']"/>

            <!-- Get the image width percentage -->
            <xsl:variable name="image_width_percentage">
                <xsl:choose>
                    <xsl:when test="properties/integerProperty[@name='width']">
                        <xsl:value-of select="properties/integerProperty[@name='width']"/>
                    </xsl:when>
                    <xsl:otherwise>50</xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <img class="figure_image">
                <xsl:attribute name="src">
                    <xsl:value-of select="$file-link" disable-output-escaping="yes"/>
                </xsl:attribute>

                <xsl:attribute name="style">
                    <xsl:value-of select="concat('width:', $image_width_percentage, '%')"/>
                </xsl:attribute>
            </img>

            <p class="figure_caption">
                <span class="figure_caption_label">
                    <xsl:value-of select="$proteus:lang_figure"/>
                    <xsl:text> </xsl:text>
                    <!-- from is needed to restart numbering in each document          -->
                    <!-- level is needed to avoid restarting numbering in each section -->
                    <xsl:number
                        from="object[@classes=':Proteus-document']"
                        count="object[@classes='external-resource'] | object[@classes='graphic-file']"
                        level="any"/>:
                    <xsl:text> </xsl:text>
                </span>
                
                <!-- applying markdown -->
                <xsl:call-template name="generate_markdown">
                    <xsl:with-param name="content" select="properties/markdownProperty[@name='description']"/>
                </xsl:call-template>
            </p>
        </div>
    </div>

</xsl:template>

</xsl:stylesheet>