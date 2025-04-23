<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : document.xsl                                   -->
<!-- Content : PROTEUS default XSLT for document              -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/09                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/07 (Amador Durán)                      -->
<!-- match for TOC must be object[contains(@classes,'section')]-->
<!-- since appendix is a subclass of section.                 -->
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
    exclude-result-prefixes="proteus"
>
    <!-- Match the root object of the document -->
    <xsl:template match="object[@classes=':Proteus-document']">

        <!-- <!doctype html> -->
        <html>
            <head>
                <meta charset="utf-8"/>
                <meta name="generatedBy" content="PROTEUS"/>

                <!-- Remus stylesheets -->
                <link rel="stylesheet" href="templates:///verification/resources/css/remus.css"/>

                <!-- Custom stylesheets -->
                <link rel="stylesheet" href="templates:///verification/resources/css/codehilite.css"/>

                <title>
                    <xsl:value-of select="$proteus:lang_project"/>
                    <xsl:text> </xsl:text>
                    <xsl:value-of select="parent::*/parent::*/properties/stringProperty[@name=':Proteus-name']"/>
                </title>

            </head>
            <body>
                <!-- Cover -->
                <xsl:call-template name="document_cover"/>

                <xsl:call-template name="pagebreak"/>

                <!-- Table of contents -->
                <nav id="toc" role="navigation">
                    <h1><xsl:value-of select="$proteus:lang_TOC"/></h1>
                    <ul class="toc_list toc_list_level_1">
                        <xsl:apply-templates select="children/object[contains(@classes,'section')]" mode="toc"/>
                    </ul>
                </nav>

                <xsl:call-template name="pagebreak"/>

                <!-- Document body -->
                <xsl:apply-templates select="children/object"/>

                <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
                <script src="templates:///verification/resources/javascript/proteus.js"></script>
                <script src="templates:///verification/resources/javascript/verification.js"></script>

            </body>
        </html>
    </xsl:template>

</xsl:stylesheet>