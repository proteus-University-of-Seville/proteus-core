<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : appendix.xsl                                   -->
<!-- Content : PROTEUS default XSLT for appendix              -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2024/07/29                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/07 (Amador Durán)                      -->
<!-- match must be object[ends-with(@classes,'appendix')]     -->
<!-- since appendix is a subclass of section, and its classes -->
<!-- attribute is "section appendix".                         -->
<!-- To check if an object is of a given class:               -->
<!--    object[contains(@classes,class_name)]                 -->
<!-- To check if an object is of a given final class:         -->
<!--    object[ends-with(@classes,class_name)]                -->
<!-- PROBLEM: XSLT 1.0 does not include ends-with             -->
<!-- nest_level -> nesting_level                              -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/13 (Amador Durán)                      -->
<!-- Review after integration of trace properties in the list -->
<!-- of properties.                                           -->
<!-- No need to apply markdown to the appendix title, HTML    -->
<!-- headers ignore formatting.                               -->
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
    <!-- ============================================= -->
    <!-- appendix template                             -->
    <!-- ============================================= -->

    <!-- <xsl:template match="object[ends-with(@classes,'appendix')]"> -->
    <xsl:template match="object[contains(@classes,'appendix')]">
        <!-- Nesting level -->
        <xsl:param name="nesting_level" select="1"/>

        <div id="{@id}" data-proteus-id="{@id}">

            <!-- Calculate appendix index -->
            <!-- Should use ends-with     -->
            <xsl:variable name="appendix_index">
                <xsl:number  
                    count="object[contains(@classes,'appendix')]"
                    level="single" 
                    format="A" />
            </xsl:variable>
 
            <!-- Get appendix title -->
            <xsl:variable name="title" select="properties/stringProperty[@name=':Proteus-name']"/>

            <!-- Generate header element -->
            <xsl:element name="h1">
                <xsl:value-of select="$appendix_index"/>
                <xsl:text> </xsl:text>
                <xsl:value-of select="$title"/>
            </xsl:element>

            <!-- Apply templates to all appendix children -->
            <xsl:apply-templates select="children/object">
                <!-- Provide nesting level context to children -->
                <xsl:with-param name="nesting_level" select="$nesting_level + 1"/>
                <xsl:with-param name="previous_index" select="$appendix_index"/>
            </xsl:apply-templates>
            
        </div>
    </xsl:template>

    <!-- ============================================= -->
    <!-- appendix template in "toc" mode               -->
    <!-- ============================================= -->

    <!-- A <ul> parent element is assumed              -->

    <!-- <xsl:template match="object[ends-with(@classes,'appendix')]" mode="toc"> -->
    <xsl:template match="object[contains(@classes,'appendix')]" mode="toc">

            <!-- Calculate appendix index -->
            <!-- Should use ends-with     -->
            <xsl:variable name="appendix_index">
                <xsl:number  
                    count="object[contains(@classes,'appendix')]"
                    level="single" 
                    format="A" />
            </xsl:variable>

        <!-- Get appendix title -->
        <xsl:variable name="title" select="properties/*[@name=':Proteus-name']"/>

        <!-- Generate TOC item element -->
        <li>
            <xsl:value-of select="$appendix_index"/>
            <xsl:text> </xsl:text>
            <a href="#{@id}"><xsl:apply-templates select="$title"/></a>
        </li>

        <!-- Generate TOC items for child sections (if any) -->
        <xsl:if test="children/object[contains(@classes,'section')]">
            <ul class="toc_list">
                <xsl:apply-templates select="children/object[contains(@classes,'section')]" mode="toc">
                    <xsl:with-param name="previous_index" select="$appendix_index"/>
                </xsl:apply-templates>
            </ul>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>