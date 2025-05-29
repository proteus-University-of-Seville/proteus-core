<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:proteus="http://proteus.us.es"
    xmlns:proteus-utils="http://proteus.us.es/utils"
    exclude-result-prefixes="proteus proteus-utils"
    xmlns:exsl="http://exslt.org/common"
    extension-element-prefixes="exsl"
>
    <!-- Output -->
    <xsl:output method="html"
        omit-xml-declaration="yes"
        encoding="utf-8"
        indent="yes"
    />

    <xsl:include href="document.xsl"/>
    <xsl:include href="section.xsl"/>
    <xsl:include href="paragraph.xsl"/>
    <xsl:include href="figure.xsl"/>


    <xsl:template match="project">
        <xsl:variable name="currentDocumentId" select="proteus-utils:current_document()"/>
        <xsl:apply-templates select="documents/object[@id=$currentDocumentId]"/>
    </xsl:template>

</xsl:stylesheet>