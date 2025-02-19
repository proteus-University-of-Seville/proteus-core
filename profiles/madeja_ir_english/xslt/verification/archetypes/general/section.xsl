<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : section.xsl                                    -->
<!-- Content : PROTEUS default XSLT for section               -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/09                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/09 (Amador Durán)                      -->
<!-- match must be object[ends-with(@classes,'section')]      -->
<!-- To check if an object is of a given class:               -->
<!--    object[contains(@classes,class_name)]                 -->
<!-- To check if an object is of a given final class:         -->
<!--    object[ends-with(@classes,class_name)]                -->
<!-- PROBLEM: XSLT 1.0 does not include ends-with             -->
<!-- NOTE: in this case, @classes='section' is kept to avoid  -->
<!-- matching with appendix, whics is a subclass of section   -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/13 (Amador Durán)                      -->
<!-- Review after integration of trace properties in the list -->
<!-- of properties.                                           -->
<!-- No need to apply markdown to the section title, HTML     -->
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
    <!-- section template                              -->
    <!-- ============================================= -->

    <xsl:template match="object[@classes='section']">
        <!-- Nesting level -->
        <xsl:param name="nesting_level" select="1"/>
        <xsl:param name="previous_index" select="''"/>

        <div id="{@id}"  data-proteus-id="{@id}">

            <!-- Calculate the normalized header level -->
            <xsl:variable name="header_level">
                <xsl:choose>
                    <xsl:when test="$nesting_level > 6">6</xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$nesting_level"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <!-- Calculate section index -->
            <xsl:variable name="section_index">
                <xsl:number level="single" count="object[@classes='section']" />
            </xsl:variable>

            <!-- Build the current index -->
            <xsl:variable name="current_index">
                <xsl:value-of select="$previous_index"/>
                
                <xsl:choose>
                    <xsl:when test="$previous_index">
                        <xsl:text>.</xsl:text>                        
                    </xsl:when>
                </xsl:choose>

                <xsl:value-of select="$section_index"/>
            </xsl:variable>
            
            <!-- Get section title -->
            <xsl:variable name="title" select="properties/*[@name=':Proteus-name']"/>

            <!-- Generate header element -->
            <xsl:element name="h{$header_level}">
                <xsl:value-of select="$current_index"/>
                <xsl:text> </xsl:text>
                <xsl:value-of select="$title"/>
            </xsl:element>

            <!-- Apply templates to all section children -->
            <xsl:apply-templates select="children/object">
                <!-- Provide nesting level context to children -->
                <xsl:with-param name="nesting_level" select="$nesting_level + 1"/>
                <xsl:with-param name="previous_index" select="$current_index"/>
            </xsl:apply-templates>
            
        </div>
    </xsl:template>

    <!-- ============================================= -->
    <!-- section template in "toc" mode                -->
    <!-- ============================================= -->

    <!-- A <ul> parent element is assumed              -->

    <xsl:template match="object[@classes='section']" mode="toc">
        <xsl:param name="previous_index" select="''"/>

        <!-- Calculate section index -->
        <xsl:variable name="section_index">
            <xsl:number level="single" count="object[@classes='section']" />
        </xsl:variable>

        <!-- Build the current index -->
        <xsl:variable name="current_index">
            <xsl:value-of select="$previous_index"/>
            
            <xsl:choose>
                <xsl:when test="$previous_index">
                    <xsl:text>.</xsl:text>                        
                </xsl:when>
            </xsl:choose>

            <xsl:value-of select="$section_index"/>
        </xsl:variable>

        <!-- Get section title -->
        <xsl:variable name="title" select="properties/stringProperty[@name=':Proteus-name']"/>

        <!-- Generate TOC item element -->
        <li>
            <xsl:value-of select="$current_index"/>
            <xsl:text> </xsl:text>
            <a href="#{@id}"><xsl:value-of select="$title"/></a>
        </li>

        <!-- Generate TOC items for child sections (if any) -->
        <xsl:if test="children/object[@classes='section']">
            <ul class="toc_list">
                <xsl:apply-templates select="children/object[@classes='section']" mode="toc">
                    <xsl:with-param name="previous_index" select="$current_index"/>
                </xsl:apply-templates>
            </ul>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>