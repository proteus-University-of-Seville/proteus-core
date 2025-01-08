<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : traceability_matrix.xsl                        -->
<!-- Content : PROTEUS default XSLT for traceability-matrix   -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/09                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/10/19 (Amador Durán)                      -->
<!-- Code review and refactoring.                             -->
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
    <!-- traceability-matrix template                  -->
    <!-- ============================================= -->

    <xsl:template match="object[contains(@classes,'traceability-matrix')]">

        <div id="{@id}" data-proteus-id="{@id}" class="traceability_matrix">

            <!-- Extract row and column classes -->
            <xsl:variable name="col-classes">
                <xsl:apply-templates select="properties/classListProperty[@name='col-classes']/class"/>
            </xsl:variable>

            <xsl:variable name="row-classes">
                <xsl:apply-templates select="properties/classListProperty[@name='row-classes']/class"/>
            </xsl:variable>

            <xsl:choose>
                <xsl:when test="string-length($col-classes) &gt; 1 and string-length($row-classes) &gt; 1">
                    <xsl:call-template name="matrix-from-classes">
                        <xsl:with-param name="col-classes" select="$col-classes"/>
                        <xsl:with-param name="row-classes" select="$row-classes"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="traceability-matrix-warning">
                        <xsl:with-param name="message" select="$proteus:lang_traceability_matrix_missing_class"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Generate matrix caption -->
            <p class="matrix_caption">
                <span class="matrix_caption_label">
                    <xsl:value-of select="$proteus:lang_traceability_matrix"/>
                    <xsl:text> </xsl:text>
                    <!-- from is needed to restart numbering in each document          -->
                    <!-- level is needed to avoid restarting numbering in each section -->
                    <xsl:number
                        from="object[@classes=':Proteus-document']"
                        count="object[contains(@classes,'traceability-matrix')]"
                        level="any"/>:
                    <xsl:text> </xsl:text>
                </span>

                <!-- apply markdown -->
                <xsl:call-template name="generate_markdown">
                    <xsl:with-param name="content" select="properties/*[@name='description']"/>
                </xsl:call-template>
            </p>

        </div>
    </xsl:template>

    <!-- This template helps creating a list of classes separated by spaces.-->
    <!-- Proteus classes cannot contain spaces so this is supposed to be a  -->
    <!-- safe separator.                                                    -->
    <xsl:template match="class">
        <xsl:value-of select="normalize-space(.)"/>
        <xsl:text> </xsl:text>
    </xsl:template>

    <!-- ================================================================== -->
    <!-- matrix-from-classes auxilary template                              -->
    <!-- ================================================================== -->

    <!-- TODO: could this double-check be performed in the main template ?  -->

    <xsl:template name="matrix-from-classes">
        <xsl:param name="col-classes" select="' '"/>
        <xsl:param name="row-classes" select="' '"/>

        <!-- Get column and row items using Python -->
        <xsl:variable name="col-items" select="proteus-utils:traceabilityMatrixHelper.get_objects_from_classes($col-classes)"/>
        <xsl:variable name="row-items" select="proteus-utils:traceabilityMatrixHelper.get_objects_from_classes($row-classes)"/>

        <!-- If there are no col or row classes, warns the user and do not create the matrix -->
        <xsl:choose>
            <xsl:when test="count($col-items) = 0 or count($row-items) = 0">
                <xsl:call-template name="traceability-matrix-warning">
                    <xsl:with-param name="message" select="$proteus:lang_traceability_matrix_missing_item"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="generate-traceability-matrix-table">
                    <xsl:with-param name="col-items" select="$col-items"/>
                    <xsl:with-param name="row-items" select="$row-items"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ================================================================== -->
    <!-- generate-traceability-matrix-table auxilary template               -->
    <!-- ================================================================== -->

    <xsl:template name="generate-traceability-matrix-table">
        <xsl:param name="col-items"/>
        <xsl:param name="row-items"/>

        <table class="traceability_matrix remus_table">
            <thead>
                <xsl:call-template name="generate-traceability-matrix-header">
                    <xsl:with-param name="col-items" select="$col-items"/>
                </xsl:call-template>
            </thead>

            <tbody>
                <xsl:for-each select="$row-items">
                    <tr>
                        <xsl:call-template name="generate-traceability-matrix-row">
                            <xsl:with-param name="col-items" select="$col-items"/>
                        </xsl:call-template>
                    </tr>
                </xsl:for-each>
            </tbody>
        </table>
    </xsl:template>

    <!-- ================================================================== -->
    <!-- generate-traceability-matrix-header auxilary template              -->
    <!-- ================================================================== -->

    <!-- Table header -->
    <xsl:template name="generate-traceability-matrix-header">
        <xsl:param name="col-items"/>
        <th class="matrix_oid">
            <img src="templates:///default/resources/images/traceability-matrix.png"/>
            <xsl:text> </xsl:text>
            <span class="matriz_oid"><xsl:value-of select="properties/*[@name=':Proteus-code']"/></span>
            <br></br>
            <button class="reduce_font">A-</button>
            <button class="increase_font">A+</button>
        </th>

        <xsl:for-each select="$col-items">
            <xsl:variable name="label" select="label"/>

            <th class="matrix_column">
                <a href="#{@id}" onclick="selectAndNavigate(`{@id}`, event)" title="{$label}">
                    <xsl:value-of select="$label"/>
                </a>
            </th>
        </xsl:for-each>
    </xsl:template>

    <!-- ================================================================== -->
    <!-- generate-traceability-matrix-row auxilary template                 -->
    <!-- ================================================================== -->

    <xsl:template name="generate-traceability-matrix-row">
        <xsl:param name="col-items"/>

        <xsl:variable name="label" select="label"/>
        <xsl:variable name="row-item-id" select="@id"/>

        <th>
            <a href="#{@id}" onclick="selectAndNavigate(`{@id}`, event)" title="{$label}">
                <xsl:value-of select="$label"/>
            </a>
        </th>

        <xsl:for-each select="$col-items">
            <td>
                <xsl:variable name="has-dependency" select="proteus-utils:traceabilityMatrixHelper.check_dependency($row-item-id, @id)"/>
                <xsl:choose>
                    <xsl:when test="$has-dependency = 'True'">
                        <xsl:attribute name="class">trace</xsl:attribute>
                        <img class="trace" src="templates:///default/resources/images/trace.png"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>-</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </td>
        </xsl:for-each>
    </xsl:template>

    <!-- ================================================================== -->
    <!-- traceability-matrix-warning auxilary template                      -->
    <!-- ================================================================== -->

    <!-- Warning to be shown were items are not found -->
    <xsl:template name="traceability-matrix-warning">
        <xsl:param name="message"/>

        <table class="traceability_matrix">
            <th>
                <span class="tbd"><xsl:value-of select="$message"/></span>
            </th>
        </table>
    </xsl:template>

</xsl:stylesheet>