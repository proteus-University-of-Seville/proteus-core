<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_document.xsl                           -->
<!-- Content : PROTEUS XSLT for subjects at US - document     -->
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
                <link rel="stylesheet" href="templates:///remus/resources/css/remus.css"/>

                <!-- Custom stylesheets -->
                <link rel="stylesheet" href="templates:///remus/resources/css/codehilite.css"/>

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
                        <xsl:apply-templates select="children/object[@classes='section']" mode="toc"/>
                    </ul>
                </nav>

                <xsl:call-template name="pagebreak"/>

                <!-- Document body -->
                <xsl:apply-templates select="children/object"/>

                <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
                <script src="templates:///remus/resources/javascript/proteus.js"></script> 

            </body>
        </html>
    </xsl:template>

</xsl:stylesheet>