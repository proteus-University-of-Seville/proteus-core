<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : figure.xsl                                     -->
<!-- Content : PROTEUS default XSLT for figure                -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/09                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/08 (Amador Durán)                      -->
<!-- match must be object[ends-with(@classes,'figure')]       -->
<!-- To check if an object is of a given class:               -->
<!--    object[contains(@classes,class_name)]                 -->
<!-- To check if an object is of a given final class:         -->
<!--    object[ends-with(@classes,class_name)]                -->
<!-- PROBLEM: XSLT 1.0 does not include ends-with             -->
<!-- graphic-file -> figure                                   -->
<!-- external-resource -> figure                              -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/13 (Amador Durán)                      -->
<!-- Review after integration of trace properties in the list -->
<!-- of properties.                                           -->
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
<!-- figure template                                          -->
<!-- ======================================================== -->

<xsl:template match="object[contains(@classes,'figure')]"> 

    <div id="{@id}" data-proteus-id="{@id}">

        <div class="figure">
            <!-- Get file name with extension -->
            <xsl:variable name="figure_path" select="properties/*[@name='file']"/>

            <!-- Get file link -->
            <xsl:variable name="figure_url" select="properties/*[@name='url']"/>

            <!-- Get the image width percentage -->
            <xsl:variable name="image_width_percentage">
                <xsl:choose>
                    <xsl:when test="properties/*[@name='width']">
                        <xsl:value-of select="properties/*[@name='width']"/>
                    </xsl:when>
                    <xsl:otherwise>50</xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <!-- Generate <img> element -->
            <img class="figure_image">
                <xsl:attribute name="src">
                    <xsl:choose>
                        <xsl:when test="normalize-space($figure_path)">
                            <xsl:value-of select="concat('assets:///', $figure_path)" disable-output-escaping="no"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$figure_url" disable-output-escaping="yes"/>                        
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>

                <xsl:attribute name="style">
                    <xsl:value-of select="concat('width:', $image_width_percentage, '%')"/>
                </xsl:attribute>
            </img>

            <!-- Generate figure caption -->
            <p class="figure_caption">
                <span class="figure_caption_label">
                    <xsl:value-of select="$proteus:lang_figure"/>
                    <xsl:text> </xsl:text>
                    <!-- from is needed to restart numbering in each document          -->
                    <!-- level is needed to avoid restarting numbering in each section -->
                    <xsl:number
                        from="object[@classes=':Proteus-document']"
                        count="object[contains(@classes,'figure')]"
                        level="any"/>:
                    <xsl:text> </xsl:text>
                </span>
                
                <!-- apply markdown -->
                <xsl:call-template name="generate_markdown">
                    <xsl:with-param name="content" select="properties/*[@name='description']"/>
                </xsl:call-template>
            </p>

        </div>
    </div>

</xsl:template>

</xsl:stylesheet>