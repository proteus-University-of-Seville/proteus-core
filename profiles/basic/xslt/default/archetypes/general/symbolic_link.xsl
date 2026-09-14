<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : symbolic_link.xsl                              -->
<!-- Content : PROTEUS default XSLT for symbolic-link         -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/09/14                                     -->
<!-- Version : 2.0                                            -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
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
          <div class="linked-object" title="{$proteus:lang_symlink_tooltip}">
            <xsl:apply-templates select="$targetObject" />
          </div>
        </xsl:if>
      </xsl:for-each>
    </div>

  </xsl:template>

</xsl:stylesheet>
