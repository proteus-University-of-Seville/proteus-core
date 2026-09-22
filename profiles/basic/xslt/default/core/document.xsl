<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : document.xsl                                   -->
<!-- Content : PROTEUS default XSLT for documents             -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/22                                     -->
<!-- Version : 2.0                                            -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:proteus="http://proteus.us.es"
    xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <!-- Match the root object of the document -->
  <xsl:template match="object[@classes=':Proteus-document']">

    <!-- <!doctype html> -->
    <html>
      <head>
        <meta charset="utf-8"/>
        <meta name="generatedBy" content="PROTEUS"/>

        <!-- Proteus stylesheets -->
        <link rel="stylesheet" href="templates:///default/resources/css/default.css"/>

        <!-- Custom stylesheets -->
        <link rel="stylesheet" href="templates:///default/resources/css/codehilite.css"/>

        <title>
          <xsl:value-of select="proteus-utils:i18n('xslt.project')"/>
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
          <h1><xsl:value-of select="proteus-utils:i18n('xslt.toc')"/></h1>

          <ul class="toc_list toc_list_level_1">
            <xsl:apply-templates
              mode="toc"
              select="children/object[contains(@classes,'section')]"
            />
          </ul>
        </nav>

        <xsl:call-template name="pagebreak"/>

        <!-- Document body -->
        <xsl:apply-templates select="children/object"/>

        <!-- JavaScript for connecting HTML with application -->
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script src="templates:///default/resources/javascript/proteus.js"></script>

      </body>
    </html>
  </xsl:template>

</xsl:stylesheet>