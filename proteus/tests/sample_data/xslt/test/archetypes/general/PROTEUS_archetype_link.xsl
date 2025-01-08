<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_actor.xsl                              -->
<!-- Content : PROTEUS XSLT for subjects at US - actor        -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/07                                     -->
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
    <!-- proteus:actor template                        -->
    <!-- ============================================= -->

    <xsl:template match="object[@classes='archetype-link']">

        <div id="{@id}" class="symbolic-link" data-proteus-id="{@id}">
            <!-- Select traceProperty named link -->
            <xsl:variable name="traces" select="properties/traceProperty[@name='link']/trace" />

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
