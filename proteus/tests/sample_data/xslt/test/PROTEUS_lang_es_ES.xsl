<?xml version="1.0" encoding="ISO-8859-1"?>

<!-- ========================================================= -->
<!-- File    : template_es_ES.xsl                              -->
<!-- Content : PROTEUS XSLT for subjects at US - English main  -->
<!--           file                                            -->
<!-- Author  : Amador Durán Toro                               -->
<!--           José María Delgado Sánchez                      -->
<!-- Date    : 2023/06/29                                      -->
<!-- Version : 1.0                                             -->
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

<xsl:import href="PROTEUS_i18n_Spanish.xsl"/>

<!-- ======================================================== -->
<!-- Localized PROTEUS-specific strings                       -->
<!-- ======================================================== -->

<xsl:variable name="proteus:lang">es</xsl:variable>
<xsl:variable name="proteus:lang_part">Parte</xsl:variable>
<xsl:variable name="proteus:lang_warnings">Avisos</xsl:variable>
<xsl:variable name="proteus:lang_abstract">abstracto</xsl:variable>
<xsl:variable name="proteus:lang_TBD_expanded">Por determinar</xsl:variable>

<!-- ======================================================== -->
<!-- Include main XSLT file                                   -->
<!-- ======================================================== -->

<xsl:include href="PROTEUS_main.xsl"/>

</xsl:stylesheet>