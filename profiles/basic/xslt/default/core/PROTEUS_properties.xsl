<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_properties.xsl                         -->
<!-- Content : PROTEUS default XSLT for properties            -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/12/08                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/11 (Amador Durán)                      -->
<!-- New template for urlProperty                             -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/14 (Amador Durán)                      -->
<!-- Improvements in template for urlProperty.                -->
<!-- New template for enum property.                          -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/18 (Amador Durán)                      -->
<!-- New template for file property, assuming it is a graphic -->
<!-- file to be displayed in an <img> element.                -->
<!-- traceProperty enhanced to include :Proteus-code when     -->
<!-- present.                                                 -->
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
    <!-- traceProperty                                 -->
    <!-- ============================================= -->

    <!-- List mode -->
    <xsl:template match="traceProperty">
        <ul class="traces">
            <xsl:for-each select="trace">
                <xsl:variable name="target_id" select="@target" />
                <xsl:variable name="target_object" select="//object[@id=$target_id]" />
                <xsl:variable name="target_code" select="$target_object/properties/*[@name=':Proteus-code']" />
                <xsl:variable name="target_name">
                    <xsl:if test="$target_code">
                        [<xsl:value-of select="$target_code"/>]
                    </xsl:if>
                    <xsl:value-of select="$target_object/properties/*[@name=':Proteus-name']" />
                </xsl:variable>

                <xsl:if test="$target_object">
                    <li>
                        <a href="#{$target_id}" onclick="selectAndNavigate(`{$target_id}`, event)">
                            <xsl:value-of select="$target_name"/>
                        </a>
                    </li>
                </xsl:if>
            </xsl:for-each>
        </ul>
    </xsl:template>

    <!-- Paragraph mode -->
    <xsl:template match="traceProperty" mode="paragraph">
        <xsl:for-each select="trace">
            <xsl:variable name="target_id" select="@target" />
            <xsl:variable name="target_object" select="//object[@id=$target_id]" />
            <xsl:variable name="target_code" select="$target_object/properties/*[@name=':Proteus-code']" />
            <xsl:variable name="target_name">
                <xsl:if test="$target_code">
                    [<xsl:value-of select="$target_code"/>]
                </xsl:if>
                <xsl:value-of select="$target_object/properties/*[@name=':Proteus-name']" />
            </xsl:variable>

            <xsl:if test="$target_object">
                <p>
                    <a href="#{$target_id}" onclick="selectAndNavigate(`{$target_id}`, event)">
                        <xsl:value-of select="$target_name"/>
                    </a>
                </p>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <!-- ============================================= -->
    <!-- markdownProperty                              -->
    <!-- ============================================= -->

    <xsl:template match="markdownProperty">
        <xsl:call-template name="generate_markdown">
            <xsl:with-param name="content" select="."/>
        </xsl:call-template>
    </xsl:template>

    <!-- ============================================= -->
    <!-- urlProperty                                   -->
    <!-- ============================================= -->

    <xsl:template match="urlProperty">
        <xsl:variable name="href" select="."/>
        <a href="{$href}"><xsl:value-of select="$href"/></a>
    </xsl:template>

    <!-- ============================================= -->
    <!-- enumProperty                                  -->
    <!-- ============================================= -->

    <xsl:template match="enumProperty">
        <xsl:value-of select="$enum_labels/label[@key=current()/text()]"/>
    </xsl:template>

    <!-- ============================================= -->
    <!-- fileProperty                                  -->
    <!-- ============================================= -->

    <!-- NOTE: it is assumed that it is a graphic file.-->
    <!-- NOTE: it is also assumed that there is a      -->
    <!-- width property in the same object.            -->

    <xsl:template match="fileProperty">
        <!-- Get file name with extension (optional, it could be empty) -->
        <xsl:variable name="image_path" select="."/>

        <!-- Get the image width percentage (if exists)-->
        <xsl:variable name="image_width_percentage">
            <xsl:choose>
                <xsl:when test="../*[@name='width']">
                    <xsl:value-of select="../*[@name='width']"/>
                </xsl:when>
                <xsl:otherwise>50</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <!-- Generate <img> element (if any) -->
        <br></br>
        <br></br>
        <div>
            <xsl:choose>
                <xsl:when test="normalize-space($image_path)">
                    <img class="figure_image">
                        <xsl:attribute name="src">
                            <xsl:value-of select="concat('assets:///', $image_path)" disable-output-escaping="no"/>
                        </xsl:attribute>
                        <xsl:attribute name="style">
                            <xsl:value-of select="concat('width:', $image_width_percentage, '%')"/>
                        </xsl:attribute>
                    </img>
                </xsl:when>
                <xsl:otherwise>
                    <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                </xsl:otherwise>
            </xsl:choose>
        </div>
    </xsl:template>

    <!-- ============================================= -->
    <!-- traceTypeListProperty                         -->
    <!-- ============================================= -->

    <xsl:template match="traceTypeListProperty">
        <ul class="traces">
            <xsl:for-each select="type">
                <xsl:if test="current()/text()">
                    <li>
                        <a>
                        <xsl:variable name="trace_type_label" select="$trace_types/label[@key=current()/text()]" />
                        <xsl:choose>
                            <xsl:when test="normalize-space($trace_type_label)">
                                <xsl:value-of select="$trace_type_label"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="current()/text()"/>
                            </xsl:otherwise>
                        </xsl:choose>
                        </a>
                    </li>
                </xsl:if>
            </xsl:for-each>
        </ul>
    </xsl:template>

</xsl:stylesheet>