<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : property_labels.xsl                            -->
<!-- Content : PROTEUS property labels XSLT file              -->
<!-- Author  : Amador Durán Toro                              -->
<!-- Date    : 2026/05/02                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->

<!-- ======================================================== -->
<!-- exclude-result-prefixes="proteus" must be set in all     -->
<!-- files to avoid xmlsn:proteus="." to appear in HTML tags. -->
<!-- ======================================================== -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:exsl="http://exslt.org/common"
  xmlns:proteus="http://proteus.us.es"
  xmlns:proteus-utils="http://proteus.us.es/utils"
  exclude-result-prefixes="proteus proteus-utils"
  extension-element-prefixes="exsl"
>

<!-- NOTE: that would not be necessary in XSLT 2.0,  -->
<!-- where variable names can be computed in runtime -->

<!-- PROTEUS property labels dictionary -->
<xsl:variable name="property_labels_dictionary">
  <label key=":Proteus-date"><xsl:value-of select="$proteus:lang_date"/></label>
  <label key="address"><xsl:value-of select="$proteus:lang_address"/></label>
  <label key="attenders"><xsl:value-of select="$proteus:lang_attenders"/></label>
  <label key="authors"><xsl:value-of select="$proteus:lang_authors"/></label>
  <label key="category"><xsl:value-of select="$proteus:lang_category"/></label>
  <label key="comments"><xsl:value-of select="$proteus:lang_comments"/></label>
  <label key="created-by"><xsl:value-of select="$proteus:lang_authors"/></label>
  <label key="date"><xsl:value-of select="$proteus:lang_date"/></label>
  <label key="description"><xsl:value-of select="$proteus:lang_description"/></label>
  <label key="diagram"><xsl:value-of select="$proteus:lang_diagram"/></label>
  <label key="email"><xsl:value-of select="$proteus:lang_email"/></label>
  <label key="importance"><xsl:value-of select="$proteus:lang_importance"/></label>
  <label key="inherits-from"><xsl:value-of select="$proteus:lang_inherits_from"/></label>
  <label key="name"><xsl:value-of select="$proteus:lang_name"/></label>
  <label key="ordered"><xsl:value-of select="$proteus:lang_ordered"/></label>
  <label key="phone-number"><xsl:value-of select="$proteus:lang_telephone"/></label>
  <label key="precondition"><xsl:value-of select="$proteus:lang_precondition"/></label>
  <label key="postcondition"><xsl:value-of select="$proteus:lang_postcondition"/></label>
  <label key="role"><xsl:value-of select="$proteus:lang_role"/></label>
  <label key="sources"><xsl:value-of select="$proteus:lang_sources"/></label>
  <label key="stability"><xsl:value-of select="$proteus:lang_stability"/></label>
  <label key="version"><xsl:value-of select="$proteus:lang_version"/></label>
  <label key="web"><xsl:value-of select="$proteus:lang_web"/></label>
  <label key="works-for"><xsl:value-of select="$proteus:lang_organization"/></label>
  <label key="status"><xsl:value-of select="$proteus:lang_status"/></label>
  <label key="time"><xsl:value-of select="$proteus:lang_time"/></label>
  <label key="participates-in"><xsl:value-of select="$proteus:lang_participates_in"/></label>
  <label key="place"><xsl:value-of select="$proteus:lang_place"/></label>
  <label key="priority"><xsl:value-of select="$proteus:lang_priority"/></label>
  <label key="results"><xsl:value-of select="$proteus:lang_results"/></label>
  <label key="directly-affected-objects"><xsl:value-of select="$proteus:lang_directly_affected_objects"/></label>
  <label key="analysis"><xsl:value-of select="$proteus:lang_analysis"/></label>
  <label key="trace-type"><xsl:value-of select="$proteus:lang_trace_type"/></label>
  <label key="solution"><xsl:value-of select="$proteus:lang_solution"/></label>
</xsl:variable>

<!-- This is needed because of limitations of XSLT 1.0 -->
<!-- Note the use of the node-set() extension function -->
<!-- Usage: <xsl:value-of select="$property-labels/label[@key=@name])"/> -->
<xsl:variable name="property_labels" select="exsl:node-set($property_labels_dictionary)"/>

<!-- Define the key for property labels                           -->
<!-- WARINIG: it is useless, always returns nothing               -->
<!-- Using $property_labels/label in key's match is not allowed.  -->
<!-- Usage: <xsl:value-of select="key('property-label', @name)"/> -->
<!-- <xsl:key name="property-label" match="label" use="@key"/>    -->

</xsl:stylesheet>

