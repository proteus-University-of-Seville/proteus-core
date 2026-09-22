<?xml version="1.0" encoding="utf-8"?>

  <!-- ================================================================ -->
<!-- File    : symbolic_link.xsl                                        -->
<!-- Content : PROTEUS default XSLT for symbolic links                  -->
<!-- Author  : Amador Durán Toro                                        -->
<!-- Date    : 2026/09/14                                               -->
<!-- Version : 2.0                                                      -->
  <!-- ================================================================ -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
>
  <!-- ================================================================ -->
  <!-- NOTE #1
       match expression gets rid of leading and trailing spaces in the
       @classes attribute, and adds a space at the beginning and end of
       the class name to avoid matching substrings. This way, we can
       check if a class name is present in the @classes attribute by
       using contains().

       NOTE #2
       This template has priority="1" to avoid being overridden by
       templates of potential subclasses. Subclasses should have their own
       templates with higher priority, and they should call the superclass
       template by name if they want to reuse it.
  -->
  <!-- ================================================================== -->

  <!-- ================================================================ -->
  <!-- symbolic-link template                                           -->
  <!-- ================================================================ -->

  <xsl:template
    match="object[contains(concat(' ', normalize-space(@classes), ' '),' symbolic-link ')]"
    name="symbolic_link_template"
    priority="1"
  >
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
          <div class="linked-object" title="{proteus-utils:i18n('xslt.symlink_tooltip')}">
            <xsl:apply-templates select="$targetObject" />
          </div>
        </xsl:if>
      </xsl:for-each>
    </div>

  </xsl:template>

</xsl:stylesheet>
