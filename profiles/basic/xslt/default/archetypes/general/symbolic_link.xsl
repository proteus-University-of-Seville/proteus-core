<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : symbolic_link.xsl                              -->
<!-- Content : PROTEUS default XSLT for symbolic-link         -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/07                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/09 (Amador Durán)                      -->
<!-- match must be object[ends-with(@classes,'symbolic-link')]-->
<!-- To check if an object is of a given class:               -->
<!--    object[contains(@classes,class_name)]                 -->
<!-- To check if an object is of a given final class:         -->
<!--    object[ends-with(@classes,class_name)]                -->
<!-- PROBLEM: XSLT 1.0 does not include ends-with             -->
<!-- archetype-link -> symbolic-link                          -->
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
    <!-- symbolic-link template                        -->
    <!-- ============================================= -->

    <xsl:template match="object[contains(@classes,'symbolic-link')]">
        <div id="{@id}" class="symbolic-link" data-proteus-id="{@id}">
            <!-- Select traceProperty named link -->
            <xsl:variable name="traces" select="properties/*[@name='link']/trace" />

            <!-- Iterate over trace tags -->
            <xsl:for-each select="$traces">
                <!-- Select target object -->
                <xsl:variable name="targetId" select="@target" />
                <xsl:variable name="targetObject" select="//object[@id = $targetId]" />
                
                <!-- If target object exists -->
                <xsl:if test="$targetObject"> 
                    <div class="linked-object" data-tippy-content="{$proteus:lang_symlink_tooltip}">
                        <xsl:apply-templates select="$targetObject" />
                    </div>
                </xsl:if>
            </xsl:for-each>
        </div>

    </xsl:template>

</xsl:stylesheet>
