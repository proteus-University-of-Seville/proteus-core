<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:proteus="http://proteus.us.es"
    xmlns:proteus-utils="http://proteus.us.es/utils"
    exclude-result-prefixes="proteus proteus-utils"
>
    <!-- =========================================================== -->
    <!-- paragraph template                                          -->
    <!-- =========================================================== -->

    <xsl:template match="object[contains(@classes,'paragraph')]">
        <xsl:value-of select="properties/*[@name='text']"/>
    </xsl:template>

</xsl:stylesheet>