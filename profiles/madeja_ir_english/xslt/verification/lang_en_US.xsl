<?xml version="1.0" encoding="ISO-8859-1"?>

<!-- ========================================================= -->
<!-- File    : template_en_US.xsl                              -->
<!-- Content : PROTEUS default XSLT English (main file)        -->
<!-- Author  : Amador Durán Toro                               -->
<!--           José María Delgado Sánchez                      -->
<!-- Date    : 2023/06/29                                      -->
<!-- Version : 1.0                                             -->
<!-- ========================================================= -->
<!-- Update  : 2024/09/13 (Amador Durán)                       -->
<!-- Variable declaration moved to i18n document.              -->
<!-- ========================================================= -->

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
<!-- Import default localized strings                         -->
<!-- ======================================================== -->

<xsl:import href="i18n_English.xsl"/>

<!-- ======================================================== -->
<!-- Include main XSLT file                                   -->
<!-- ======================================================== -->

<xsl:include href="main.xsl"/>

</xsl:stylesheet>
