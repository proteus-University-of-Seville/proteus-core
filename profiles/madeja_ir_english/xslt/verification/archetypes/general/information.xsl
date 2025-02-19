<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : information.xsl                                -->
<!-- Content : PROTEUS default XSLT for information (paragraph)-->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2024/10/05                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/07 (Amador Durán)                      -->
<!-- match must be object[ends-with(@classes,'paragraph')]    -->
<!-- since paragraph is a subclass of                         -->
<!-- general-traceable-object.                                -->
<!-- To check if an object is of a given class:               -->
<!--    object[contains(@classes,class_name)]                 -->
<!-- To check if an object is of a given final class:         -->
<!--    object[ends-with(@classes,class_name)]                -->
<!-- PROBLEM: XSLT 1.0 does not include ends-with             -->
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
    <!-- =========================================================== -->
    <!-- information template                                        -->
    <!-- =========================================================== -->

    <xsl:template match="object[contains(@classes,'information')]">
        <div id="{@id}" data-proteus-id="{@id}" class="info">
            <xsl:variable name="content" select="properties/*[@name='text']"/>

            <xsl:call-template name="generate_markdown">
                <xsl:with-param name="content" select="$content"/>
            </xsl:call-template>
        </div>
    </xsl:template>

</xsl:stylesheet>