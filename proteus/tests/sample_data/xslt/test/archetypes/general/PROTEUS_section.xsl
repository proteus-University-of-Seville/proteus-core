<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_section.xsl                            -->
<!-- Content : PROTEUS XSLT for subjects at US - section      -->
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
    
    <!-- ============================================= -->
    <!-- section template                              -->
    <!-- ============================================= -->

    <xsl:template match="object[@classes='section' and properties/booleanProperty[@name = 'is-appendix' and text() = 'false']]">
        <!-- Nest level -->
        <xsl:param name="nest_level" select="1"/>

        <div id="{@id}"  data-proteus-id="{@id}">

            <!-- Calculate the normalized header level -->
            <xsl:variable name="header_level">
                <xsl:choose>
                    <xsl:when test="$nest_level > 6">6</xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$nest_level"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <!-- Calculate section index -->
            <xsl:variable name="section_index">
                <xsl:number level="multiple" count="object[@classes='section' and properties/booleanProperty[@name = 'is-appendix' and text() = 'false']]" />
            </xsl:variable>
            
            <xsl:element name="h{$header_level}">
                <xsl:value-of select="$section_index"/>
                <xsl:text> </xsl:text>
                <xsl:value-of select="properties/stringProperty[@name=':Proteus-name']"/><xsl:apply-templates select="name"/>
            </xsl:element>

            <!-- Apply templates to all section -->
            <xsl:apply-templates select="children/object">
                <!-- Provide nest level context to children -->
                <xsl:with-param name="nest_level" select="$nest_level + 1"/>
            </xsl:apply-templates>
            
        </div>
    </xsl:template>

    <!-- ============================================= -->
    <!-- appendix template                             -->
    <!-- ============================================= -->

    <xsl:template match="object[@classes='section' and properties/booleanProperty[@name = 'is-appendix' and text() = 'true']]">
        <!-- Nest level -->
        <xsl:param name="nest_level" select="1"/>

        <div id="{@id}"  data-proteus-id="{@id}">

            <!-- Calculate the normalized header level -->
            <xsl:variable name="header_level">
                <xsl:choose>
                    <xsl:when test="$nest_level > 6">6</xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$nest_level"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <!-- Calculate section index -->
            <xsl:variable name="section_index">
                <xsl:number level="multiple" count="object[@classes='section' and properties/booleanProperty[@name = 'is-appendix' and text() = 'true']]" format="A" />
            </xsl:variable>
            
            <xsl:element name="h{$header_level}">
                <xsl:value-of select="$section_index"/>
                <xsl:text> </xsl:text>
                <xsl:value-of select="properties/stringProperty[@name=':Proteus-name']"/><xsl:apply-templates select="name"/>
            </xsl:element>

            <!-- Apply templates to all section -->
            <xsl:apply-templates select="children/object">
                <!-- Provide nest level context to children -->
                <xsl:with-param name="nest_level" select="$nest_level + 1"/>
            </xsl:apply-templates>
            
        </div>
    </xsl:template>

    <!-- ============================================= -->
    <!-- section template in "toc" mode                -->
    <!-- ============================================= -->

    <!-- A <ul> parent element is assumed              -->

    <xsl:template match="object[@classes='section' and properties/booleanProperty[@name = 'is-appendix' and text() = 'false']]" mode="toc">
        <!-- Calculate section index -->
        <xsl:variable name="section_index">
            <xsl:number level="multiple" count="object[@classes='section' and properties/booleanProperty[@name = 'is-appendix' and text() = 'false']]" />
        </xsl:variable>
        <li>
            <xsl:value-of select="$section_index"/>
            <xsl:text> </xsl:text>
            <a href="#{@id}"><xsl:apply-templates select="properties/stringProperty[@name=':Proteus-name']"/></a>
        </li>
        <xsl:if test="children/object[@classes='section']">
            <ul class="toc_list">
                <xsl:apply-templates select="children/object[@classes='section']" mode="toc"/>
            </ul>
        </xsl:if>
    </xsl:template>

    <!-- ============================================= -->
    <!-- appendix template in "toc" mode               -->
    <!-- ============================================= -->

    <!-- A <ul> parent element is assumed              -->

    <xsl:template match="object[@classes='section' and properties/booleanProperty[@name = 'is-appendix' and text() = 'true']]" mode="toc">
        <!-- Calculate section index -->
        <xsl:variable name="section_index">
            <xsl:number level="multiple" count="object[@classes='section' and properties/booleanProperty[@name = 'is-appendix' and text() = 'true']]" format="A" />
        </xsl:variable>
        <li>
            <xsl:value-of select="$section_index"/>
            <xsl:text> </xsl:text>
            <a href="#{@id}"><xsl:apply-templates select="properties/stringProperty[@name=':Proteus-name']"/></a>
        </li>
        <xsl:if test="children/object[@classes='section']">
            <ul class="toc_list">
                <xsl:apply-templates select="children/object[@classes='section']" mode="toc"/>
            </ul>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>