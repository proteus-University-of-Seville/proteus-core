<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : glossary_item.xsl                              -->
<!-- Content : PROTEUS default XSLT for glossary-item         -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/09                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/07 (Amador Durán)                      -->
<!-- match must be object[ends-with(@classes,'glossary-item')]-->
<!-- since glossary-item is a subclass of                     -->
<!-- general-traceable-object.                                -->
<!-- To check if an object is of a given class:               -->
<!--    object[contains(@classes,class_name)]                 -->
<!-- To check if an object is of a given final class:         -->
<!--    object[ends-with(@classes,class_name)]                -->
<!-- PROBLEM: XSLT 1.0 does not include ends-with             -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/10 (Amador Durán)                      -->
<!-- property "image" added to the archetype                  -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/13 (Amador Durán)                      -->
<!-- Review after integration of trace properties in the list -->
<!-- of properties                                            -->
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
    <!-- glossary-item template                                      -->
    <!-- =========================================================== -->

    <xsl:template match="object[contains(@classes,'glossary-item')]">
        <div id="{@id}" class="glo" data-proteus-id="{@id}">
            <p>
                <!-- Generate glossary item name -->
                <strong>
                    <xsl:value-of select="properties/*[@name=':Proteus-name']"/>
                    <xsl:text>: </xsl:text>
                </strong>

                <!-- Generate glossary item description -->
                <xsl:variable name="description" select="properties/*[@name='description']"/>
                <xsl:variable name="nonempty_content" select="string-length(normalize-space($description)) > 0"/>

                <xsl:choose>
                    <xsl:when test="not($nonempty_content)">
                        <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="generate_markdown">
                            <xsl:with-param name="content" select="$description"/>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>

                <!-- Get file name with extension (optional, it could be empty) -->
                <xsl:variable name="image_path" select="properties/*[@name='image']"/>
                
                <!-- Get the image width percentage -->
                <xsl:variable name="image_width_percentage">
                    <xsl:choose>
                        <xsl:when test="properties/*[@name='width']">
                            <xsl:value-of select="properties/*[@name='width']"/>
                        </xsl:when>
                        <xsl:otherwise>50</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>

                <!-- Generate <img> element (if any) -->
                <xsl:if test="normalize-space($image_path)">
                    <div>
                        <img class="figure_image">
                            <xsl:attribute name="src">
                                <xsl:value-of select="concat('assets:///', $image_path)" disable-output-escaping="no"/>
                            </xsl:attribute>
                            <xsl:attribute name="style">
                                <xsl:value-of select="concat('width:', $image_width_percentage, '%')"/>
                            </xsl:attribute>
                        </img>
                    </div>
                </xsl:if>
            </p>
        </div>
    </xsl:template>

</xsl:stylesheet>