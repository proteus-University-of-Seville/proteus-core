<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : utilities.xsl                                  -->
<!-- Content : PROTEUS default XSLT - utilities               -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/06/09                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/10 (Amador Durán)                      -->
<!-- Use of EXSLT node-set function to overcome some XLST 1.0 -->
<!-- limitations.                                             -->
<!-- ======================================================== -->
<!-- Update  : 2024/09/16 (Amador Durán)                      -->
<!-- generate_software_requirement_expanded_header ->         -->
<!-- generate_expanded_header and simplified.                 -->
<!-- generate_version_row simplified.                         -->
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
                xmlns:exsl="http://exslt.org/common"
                extension-element-prefixes="exsl"
    >
    <!-- Base URL for icons -->
    <xsl:variable name="base_url_icons">templates:///verification/resources/images/</xsl:variable>
    
    <!-- ============================================= -->
    <!-- pagebreak template                            -->
    <!-- ============================================= -->
    
    <xsl:template name="pagebreak">
        <div class="page-break"></div>
    </xsl:template>
    
    <!-- ============================================= -->
    <!-- generate_markdown template                    -->
    <!-- ============================================= -->
    
    <xsl:template name="generate_markdown">
        <xsl:param name="content" select="string(.)"/>
        <xsl:param name="glossary-items-highlight" select="true()"/>
        
        <xsl:choose>
            <xsl:when test="$glossary-items-highlight">
                <xsl:value-of select="proteus-utils:glossary_highlight(proteus-utils:generate_markdown($content))" disable-output-escaping="yes"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="proteus-utils:generate_markdown($content)" disable-output-escaping="yes"/>
            </xsl:otherwise>
        </xsl:choose>
        
    </xsl:template>
    
    <!-- ============================================= -->
    <!-- generate_property_row template                -->
    <!-- ============================================= -->
    
    <!-- current() is the property element being processed. -->
    <!-- 'tbd' is considered as having no content, it shown -->
    <!-- only if it mandatory.                              -->
    
    <xsl:template name="generate_property_row">
        <xsl:param name="label" select="$property_labels/label[@key=current()/@name]"/>
        <!-- <xsl:param name="content" select="current()//text()"/> -->
        <xsl:param name="mandatory" select="false()"/>
        <xsl:param name="verifiable" select="false()"/>
        <xsl:param name="alternative"/>
        <xsl:param name="span" select="1"/>
        <xsl:param name="diagram" select="@name='diagram'"/>
        
        <xsl:variable name="hasContent"  select="(string-length(current()//text()) > 0) and (normalize-space(current()) != 'tbd')"/>
        <xsl:variable name="hasChildren" select="boolean(current()/*)"/>
        
        <xsl:variable name="verifiableClass">
            <xsl:choose>
                <xsl:when test="$verifiable">verifiable-property</xsl:when>
                <xsl:otherwise></xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        
        <xsl:if test="$hasContent or $hasChildren or $mandatory">
            <tr>
                <xsl:choose>
                    <xsl:when test="$diagram">
                        <th colspan="{$span + 1}">
                            <xsl:value-of select="$label"/>
                            <xsl:apply-templates select="current()"/>
                        </th>
                    </xsl:when>
                    <xsl:otherwise>
                        <th>
                            <xsl:value-of select="$label"/>
                        </th>
                        <td colspan="{$span}" class="{$verifiableClass}">
                            <xsl:choose>
                                <xsl:when test="(not($hasContent) and not($hasChildren)) or normalize-space(current()) = 'tbd'">
                                    <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                                </xsl:when>
                                <xsl:when test="$alternative">
                                    <span class="alternative"><xsl:value-of select="$alternative"/></span>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:apply-templates select="current()"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </td>
                    </xsl:otherwise>
                </xsl:choose>
            </tr>
        </xsl:if>
    </xsl:template>
    
    <!-- ============================================== -->
    <!-- generate_children_row                          -->
    <!-- ============================================== -->
    
    <!-- current() is the object element being processed -->
    <!-- TODO: check CSS class names                     -->
    
    <xsl:template name="generate_children_row">
        <xsl:param name="label"/>
        <xsl:param name="span" select="1"/>
        <xsl:param name="verifiable" select="false()"/>
        
        <xsl:variable name="verifiableClass">
            <xsl:choose>
                <xsl:when test="$verifiable">verifiable-property</xsl:when>
                <xsl:otherwise></xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        
        <xsl:variable name="hasChildren" select="children/object"/>
        
        <xsl:if test="$hasChildren">
            <tr>
                <th>
                    <xsl:value-of select="$label"/>
                </th>
                <td colspan="{$span}" class="{$verifiableClass}">
                    <ul class="children">
                        <!-- for each children -->
                        <xsl:for-each select="children/object">
                            <li>
                                <xsl:call-template name="generate_object_basic_information"/>
                            </li>
                        </xsl:for-each>
                    </ul>
                </td>
            </tr>
        </xsl:if>
    </xsl:template>
    
    <!-- ============================================== -->
    <!-- generate_object_basic_information              -->
    <!-- ============================================== -->
    
    <!-- current() is the object element being processed -->
    <!-- TODO: check CSS class names                     -->
    
    <xsl:template name="generate_object_basic_information">
        <xsl:variable name="code"        select="properties/*[@name=':Proteus-code']" />
        <xsl:variable name="name"        select="properties/*[@name=':Proteus-name']" />
        <xsl:variable name="description" select="properties/*[@name='description']" />
        
        <span id="{@id}">
            <strong>
                <xsl:if test="$code">
                    [<xsl:value-of select="$code"/>]
                </xsl:if>
                <xsl:text> </xsl:text>
                <xsl:value-of select="$name" />
            </strong>
            <xsl:if test="$description">
                <xsl:text>: </xsl:text>
                <!-- <xsl:value-of select="$description"/> -->
                <xsl:apply-templates select="$description"/>
            </xsl:if>
            
            <!-- Does it have children? -->
            <xsl:if test="children/object">
                <ul class="children">
                    <xsl:for-each select="children/object">
                        <li><xsl:call-template name="generate_object_basic_information"/></li>
                    </xsl:for-each>
                </ul>
            </xsl:if>
        </span>
        
    </xsl:template>
    
    <!-- ============================================= -->
    <!-- generate_trace_row template                   -->
    <!-- ============================================= -->
    
    <!-- Check for use, probably unused -->
    
    <xsl:template name="generate_trace_row">
        <xsl:param name="label" />
        <xsl:param name="content" />
        <xsl:param name="mandatory" select="false()"/>
        <xsl:param name="span">1</xsl:param>
        
        <xsl:if test="$content/trace or $mandatory">
            <tr>
                <th><xsl:value-of select="$label"/></th>
                <td colspan="{$span}">
                    <xsl:choose>
                        <xsl:when test="not($content/trace)">
                            <span class="tbd"><xsl:value-of select="$proteus:lang_TBD_expanded"/></span>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select="$content"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </td>
            </tr>
        </xsl:if>
    </xsl:template>
    
    <!-- ============================================= -->
    <!-- generate_header template                      -->
    <!-- ============================================= -->
    
    <!-- current() is the property element being processed -->
    
    <xsl:template name="generate_header">
        <xsl:param name="label"/>
        <xsl:param name="class" select="default"/>
        <xsl:param name="name"  select="properties/*[@name=':Proteus-name']"/>
        <xsl:param name="icon"  select="concat($class,'.png')"/>
        <xsl:param name="postfix"/>
        <xsl:param name="span"  select="1"/>
        
        <thead>
            <tr>
                <th>
                    <img src="{concat($base_url_icons,$icon)}"/>
                    <xsl:text> </xsl:text>
                    <xsl:value-of select="$label"/>
                </th>
                <th class="name_column" colspan="{$span}">
                    <xsl:value-of select="$name"/>
                    <xsl:if test="$postfix"><xsl:text> </xsl:text><xsl:value-of select="$postfix"/></xsl:if>
                </th>
            </tr>
        </thead>
    </xsl:template>
    
    <!-- ================================= -->
    <!-- generate_expanded_header template -->
    <!-- ================================= -->
    
    <!-- Check for use, probably unused -->
    
    <!-- current() is the property element being processed -->
    
    <xsl:template name="generate_expanded_header">
        <xsl:param name="class" select="default"/>
        <xsl:param name="name"  select="properties/*[@name=':Proteus-name']"/>
        <xsl:param name="icon"  select="concat($class,'.png')"/>
        <xsl:param name="postfix"/>
        <xsl:param name="span"  select="1"/>
        
        <xsl:variable name="label">
            <xsl:value-of select="properties/*[@name = ':Proteus-code']/prefix" />
            <xsl:value-of select="properties/*[@name = ':Proteus-code']/number" />
            <xsl:value-of select="properties/*[@name = ':Proteus-code']/suffix" />
        </xsl:variable>
        
        <xsl:call-template name="generate_header">
            <xsl:with-param name="class"   select="$class"/>
            <xsl:with-param name="name"    select="$name"/>
            <xsl:with-param name="icon"    select="$icon"/>
            <xsl:with-param name="label"   select="$label"/>
            <xsl:with-param name="postfix" select="$postfix"/>
            <xsl:with-param name="span"    select="$span"/>
        </xsl:call-template>
        
        <!--
             <xsl:call-template name="generate_version_row">
             <xsl:with-param name="span"    select="$span"/>
             </xsl:call-template>
             
             <xsl:call-template name="generate_trace_row">
             <xsl:with-param name="label"   select="$proteus:lang_authors"/>
             <xsl:with-param name="content" select="properties/traceProperty[@name='authors']"/>
             <xsl:with-param name="span"    select="$span"/>
             </xsl:call-template>
             
             <xsl:call-template name="generate_trace_row">
             <xsl:with-param name="label"   select="$proteus:lang_sources"/>
             <xsl:with-param name="content" select="properties/traceProperty[@name='source']"/>
             <xsl:with-param name="span"    select="$span"/>
             </xsl:call-template>
        -->
    </xsl:template>
    
    
    <!-- =============================================================== -->
    <!-- Special rows templates                                          -->
    <!-- =============================================================== -->
    
    <!-- ============================================= -->
    <!-- generate_version_row template                 -->
    <!-- ============================================= -->
    
    <!-- current() is the object element being processed -->
    
    <xsl:template name="generate_version_row">
        <xsl:param name="label" select="$proteus:lang_version"/>
        <xsl:param name="span"  select="1"/>
        
        <tr>
            <th><xsl:value-of select="$label"/></th>
            <td colspan="{$span}">
                <xsl:value-of select="properties/*[@name='version']" />
                <xsl:text> (</xsl:text>
                <xsl:value-of select="properties/*[@name=':Proteus-date']" />
                <xsl:text>)</xsl:text>
            </td>
        </tr>
        
    </xsl:template>
    
    <!-- ============================================= -->
    <!-- generate_priority_rows template               -->
    <!-- ============================================= -->
    
    <xsl:template name="generate_priority_rows">
        <xsl:param name="span" select="1"/>
        
        <xsl:if test="properties/enumProperty[@name='importance'] != 'nd'">
            <xsl:call-template name="generate_property_row">
                <xsl:with-param name="label"   select="$proteus:lang_importance"/>
                <xsl:with-param name="content" select="properties/enumProperty[@name='importance']"/>
                <xsl:with-param name="span"    select="$span"/>
            </xsl:call-template>
        </xsl:if>
        
        <xsl:if test="properties/enumProperty[@name='urgency'] != 'nd'">
            <xsl:call-template name="generate_property_row">
                <xsl:with-param name="label"   select="$proteus:lang_urgency"/>
                <xsl:with-param name="content" select="properties/enumProperty[@name='urgency']"/>
                <xsl:with-param name="span"    select="$span"/>
            </xsl:call-template>
        </xsl:if>
        
        <xsl:if test="properties/enumProperty[@name='status'] != 'nd'">
            <xsl:call-template name="generate_property_row">
                <xsl:with-param name="label"   select="$proteus:lang_status"/>
                <xsl:with-param name="content" select="properties/enumProperty[@name='status']"/>
                <xsl:with-param name="span"    select="$span"/>
            </xsl:call-template>
        </xsl:if>
        
        <xsl:if test="properties/enumProperty[@name='stability'] != 'nd'">
            <xsl:call-template name="generate_property_row">
                <xsl:with-param name="label"   select="$proteus:lang_stability"/>
                <xsl:with-param name="content" select="properties/enumProperty[@name='stability']"/>
                <xsl:with-param name="span"    select="$span"/>
            </xsl:call-template>
        </xsl:if>
        
    </xsl:template>
    
    <!-- ============================================= -->
    <!-- generate_verification_rows template           -->
    <!-- ============================================= -->
    
    <xsl:template name="generate_ai_verification_row">
        <tr class="ai-verification">
            <th>
                <button type="button" class="ai-verify-button">
                    <xsl:value-of select="$proteus:lang_verify_using_ai"/>
                </button>
                <!-- If there is a previous verification, display its date and time -->
                <xsl:if test="properties/*[@name='ai_verification_date'] or properties/*[@name='ai_verification_time']">
                    <div class="verification-info">
                        <span class="verification-date">
                            <xsl:value-of select="properties/*[@name='ai_verification_date']"/>
                        </span>
                        <xsl:text> </xsl:text>
                        <span class="verification-time">
                            <xsl:value-of select="properties/*[@name='ai_verification_time']"/>
                        </span>
                    </div>
                </xsl:if>
            </th>
            <td>
                <div class="verification-output">
                    <xsl:if test="properties/*[@name='ai_verification_output']">
                        <xsl:call-template name="generate_markdown">
                            <xsl:with-param name="content" select="properties/*[@name='ai_verification_output']"/>
                        </xsl:call-template>
                    </xsl:if>
                </div>
            </td>
        </tr>
    </xsl:template>
    
</xsl:stylesheet>