<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_entity_class.xsl                        -->
<!-- Content : PROTEUS XSLT for subjects at US - objective    -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/08/02                                     -->
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

    <!-- ============================================== -->
    <!-- entity-class template                           -->
    <!-- ============================================== -->

    <xsl:template match="object[@classes='entity-class']">
        <div id="{@id}" data-proteus-id="{@id}" class="entity_class">
            <table class="entity_class remus_table">

                <!-- Header, version, authors and sources -->
                <xsl:call-template name="generate_software_requirement_expanded_header">
                    <xsl:with-param name="class" select="'objectType'" />
                </xsl:call-template>

                <tr>
                    <td colspan="2">
                        <div class="code">
                            <xsl:apply-templates select="." mode="code"/>
                        </div>
                    </td>
                </tr>

                <!-- Comments -->
                <xsl:call-template name="generate_property_row">
                    <xsl:with-param name="label"   select="$proteus:lang_comments"/>
                    <xsl:with-param name="content" select="properties/markdownProperty[@name='comments']"/>
                </xsl:call-template>

            </table>
        </div>
    </xsl:template>

    <!-- ============================================== -->
    <!-- entity-class template (mode code)               -->
    <!-- ============================================== -->

    <xsl:template match="object[@classes='entity-class']" mode="code">

        <!-- Description -->
        <xsl:call-template name="generate-code-description">
            <xsl:with-param name="multiline-comment" select="true()"/>
        </xsl:call-template>

        <!-- Class declaration -->
        <xsl:variable name="class_declaration">
            <xsl:choose>
                <xsl:when test="properties/booleanProperty[@name='is-abstract'] = 'true'">abstract class</xsl:when>
                <xsl:otherwise>class</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="css_class_declaration">
            <xsl:choose>
                <xsl:when test="properties/booleanProperty[@name='is-abstract'] = 'true'">abstract</xsl:when>
                <xsl:otherwise></xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <span class="keyword {$css_class_declaration}">
            <xsl:value-of select="$class_declaration"/>
            <xsl:text> </xsl:text>
        </span>
        <span class="class_name {$css_class_declaration}">
            <xsl:value-of select="properties/stringProperty[@name=':Proteus-name']"/>
        </span>

        <!-- superclass -->
        <xsl:variable name="superclass-trace" select="properties/traceProperty[@name='superclass']/trace"/>
        <xsl:if test="$superclass-trace">
            <span class="keyword {$css_class_declaration}"> specializes </span>
            <span class="class_name {$css_class_declaration}">
            <xsl:for-each select="$superclass-trace">
                <xsl:variable name="targetId" select="@target" />
                <xsl:variable name="targetObject" select="//object[@id = $targetId]" />

                <a href="#{$targetId}" class="rem_ref">
                    <xsl:value-of select="$targetObject/properties/stringProperty[@name = ':Proteus-name']" />
                </a>
            </xsl:for-each>
            </span>
        </xsl:if>



        <!-- Open bracket -->
        <br></br>
        <xsl:text>{</xsl:text>
        <br></br>

        <!-- Attributes -->
        <xsl:if test="children/object[@classes='attribute']">
            <div class="code_comment code_header"><xsl:value-of select="$proteus:lang_code_attributes"/></div>
            <ul class="properties">
                <xsl:apply-templates select="children/object[@classes='attribute']" mode="code"/>
            </ul>
        </xsl:if>

        <br></br>

        <!-- Components -->
        <xsl:if test="children/object[@classes='object-component']">
            <div class="code_comment code_header"><xsl:value-of select="$proteus:lang_code_components"/></div>
            <ul class="properties">
                <xsl:apply-templates select="children/object[@classes='object-component']" mode="code"/>
            </ul>
        </xsl:if>

        <br></br>

        <!-- Invariants -->
        <xsl:if test="children/object[@classes='object-invariant']">
            <div class="code_comment code_header"><xsl:value-of select="$proteus:lang_code_invariants"/></div>
            <ul class="properties">
                <xsl:apply-templates select="children/object[@classes='object-invariant']" mode="code"/>
            </ul>
        </xsl:if>

        <!-- Close bracket -->
        <br></br>
        <xsl:text>}</xsl:text>

    </xsl:template>

    <!-- ============================================== -->
    <!-- Attribute | Component templates                -->
    <!-- ============================================== -->
    <xsl:template match="object[@classes='attribute'] | object[@classes='object-component'] | object[@classes='role']" mode="code">
        <li id="{@id}" data-proteus-id="{@id}" class="property">
            <!-- Description -->
            <xsl:call-template name="generate-code-description"/>

            <!-- Keyword -->
            <xsl:call-template name="generate-code-keyword"/>

            <!-- Name -->
            <xsl:value-of select="properties/stringProperty[@name=':Proteus-name']"/>
            <xsl:text> : </xsl:text>

            <!-- Type -->
            <xsl:apply-templates select="." mode="code-type"/>

            <!-- Lower/Upper bounds -->
            <xsl:call-template name="generate-code-upper-lower-bounds"/>

            <!-- Init value/Expression -->
            <xsl:call-template name="generate-code-init-value"/>
        </li>
    </xsl:template>

    <!-- Template to generate attribute type -->
    <xsl:template match="object[@classes='attribute']" mode="code-type">
        <xsl:variable name="type" select="properties/enumProperty[@name='type']"/>
        <xsl:choose>
            <xsl:when test="$type = 'set'">Set(</xsl:when>
            <xsl:when test="$type = 'sequence'">Sequence(</xsl:when>
            <xsl:when test="$type = 'bag'">Bag(</xsl:when>
        </xsl:choose>

        <xsl:value-of select="properties/enumProperty[@name='type']"/>

        <xsl:if test="$type = 'set' or $type = 'sequence' or $type = 'bag'">)</xsl:if>
    </xsl:template>

    <!-- Template to generate component type -->
    <xsl:template match="object[@classes='object-component'] | object[@classes='role']" mode="code-type">
        <xsl:variable name="type" select="properties/enumProperty[@name='type']"/>
        <xsl:choose>
            <xsl:when test="$type = 'set'">Set(</xsl:when>
            <xsl:when test="$type = 'sequence'">Sequence(</xsl:when>
            <xsl:when test="$type = 'bag'">Bag(</xsl:when>
        </xsl:choose>

        <!-- Trace handling -->
        <xsl:variable name="type-trace" select="properties/traceProperty[@name='type']/trace"/>
        <xsl:if test="$type-trace">
            <xsl:for-each select="$type-trace">
                <xsl:variable name="targetId" select="@target" />
                <xsl:variable name="targetObject" select="//object[@id = $targetId]" />
                <xsl:value-of select="$targetObject/properties/stringProperty[@name = ':Proteus-name']" />
            </xsl:for-each>
        </xsl:if>

        <xsl:if test="$type = 'set' or $type = 'sequence' or $type = 'bag'">)</xsl:if>
    </xsl:template>

    <!-- ============================================== -->
    <!-- Invariant template                             -->
    <!-- ============================================== -->
    <xsl:template match="object[@classes='object-invariant']" mode="code">
        <li id="{@id}" data-proteus-id="{@id}" class="property">

            <!-- Natural language (comment) -->
            <xsl:call-template name="generate-code-description">
                <xsl:with-param name="content" select="properties/markdownProperty[@name='natural-lang']"/>
            </xsl:call-template>

            <!-- Keyword -->
            <span class="keyword">invariant </span>

            <!-- Name -->
            <xsl:value-of select="properties/stringProperty[@name=':Proteus-name']"/>

            <!-- Object constraint language -->
            <xsl:if test="string-length(properties/markdownProperty[@name = 'obj-constraint-lang'])">
                <xsl:text> : </xsl:text>
                <xsl:call-template name="generate_markdown">
                    <xsl:with-param name="content" select="properties/markdownProperty[@name = 'obj-constraint-lang']"/>
                </xsl:call-template>
            </xsl:if>
        </li>
    </xsl:template>

    <!-- ============================================== -->
    <!-- Helper templates                               -->
    <!-- ============================================== -->
    <!-- Description -->
    <xsl:template name="generate-code-description">
        <xsl:param name="multiline-comment" select="false()"/>
        <xsl:param name="content" select="properties/markdownProperty[@name='description']"/>

        <xsl:choose>
            <xsl:when test="string-length($content)">
                <div>
                <span class="code_comment">/**</span>
                <xsl:if test="$multiline-comment">
                    <br></br>
                </xsl:if>
                <span class="code_comment code_description">
                    <xsl:call-template name="generate_markdown">
                        <xsl:with-param name="content" select="$content"/>
                    </xsl:call-template>
                </span>
                <xsl:if test="$multiline-comment">
                    <br></br>
                </xsl:if>
                <span class="code_comment">*/</span>
            </div>
            </xsl:when>
            <xsl:otherwise>
                <br></br>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Keyword -->
    <xsl:template name="generate-code-keyword">
        <xsl:variable name="kind-of-property" select="properties/enumProperty[@name='kind-of-property']"/>
        <span class="keyword">
            <xsl:choose>
                <xsl:when test="$kind-of-property = 'constant'">const </xsl:when>
                <xsl:when test="$kind-of-property = 'variable'">var </xsl:when>
                <xsl:when test="$kind-of-property = 'derived'">derived </xsl:when>
            </xsl:choose>
        </span>
    </xsl:template>

    <!-- Lower/Upper bounds -->
    <xsl:template name="generate-code-upper-lower-bounds">

        <!-- Check if type is simple to skip -->
        <xsl:if test="properties/enumProperty[@name='type'] != 'simple'">
            <xsl:variable name="lower-bound" select="properties/stringProperty[@name='multiplicity-lower-bound']"/>
            <xsl:variable name="upper-bound" select="properties/stringProperty[@name='multiplicity-upper-bound']"/>
            <xsl:if test="string-length($lower-bound) > 0 or string-length($upper-bound) > 0">
                <xsl:text>[</xsl:text>
                <!-- Lower bound -->
                <xsl:choose>
                    <xsl:when test="string-length($lower-bound) > 0">
                        <xsl:value-of select="$lower-bound"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <span class="tbd"><xsl:value-of select="$proteus:lang_TBD"/></span>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>..</xsl:text>
                <!-- Upper bound -->
                <xsl:choose>
                    <xsl:when test="string-length($upper-bound) > 0">
                        <xsl:value-of select="$upper-bound"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <span class="tbd"><xsl:value-of select="$proteus:lang_TBD"/></span>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>]</xsl:text>
            </xsl:if>
        </xsl:if>

    </xsl:template>

    <!-- Init value/Expression -->
    <xsl:template name="generate-code-init-value">
        <xsl:variable name="init-value" select="properties/markdownProperty[@name='init-value']"/>
        <xsl:if test="string-length($init-value) > 0">
            <xsl:text> = </xsl:text>
            <xsl:call-template name="generate_markdown">
                <xsl:with-param name="content" select="$init-value"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>