<?xml version="1.0" encoding="utf-8"?>

<!-- ======================================================== -->
<!-- File    : PROTEUS_plantuml.xsl                           -->
<!-- Content : PROTEUS XSLT for subjects at US - plantuml     -->
<!-- Author  : José María Delgado Sánchez                     -->
<!-- Date    : 2023/12/19                                     -->
<!-- Version : 1.0                                            -->
<!-- ======================================================== -->

<!-- WIP, THIS IS NOT BEING USED AT THE MOMENT. iT WILL BE    -->
<!-- INCLUDED IN FUTURE VERSIONS OF THIS TEMPLATE.            -->

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

<!-- ======================================================== -->
<!-- graphic-file template                                    -->
<!-- ======================================================== -->

<xsl:template match="object[@classes='plantuml']">

    <script type="text/javascript" src="https://cdn.jsdelivr.net/gh/johan/js-deflate/rawdeflate.js"></script>

    <div class="figure">
        
        <xsl:variable name="umlCode" select="normalize-space(properties/markdownProperty[@name='plantuml-code'])"/>
        <xsl:variable name="objectId" select="@id" />

        <img class="figure_image proteus-area" id="{@id}"></img>

        <!-- https://plantuml.com/es/code-javascript-synchronous -->
        <script>
        <![CDATA[

            function encode64(data) {
            r = "";
            for (i=0; i<data.length; i+=3) {
            if (i+2==data.length) {
            r +=append3bytes(data.charCodeAt(i), data.charCodeAt(i+1), 0);
            } else if (i+1==data.length) {
            r += append3bytes(data.charCodeAt(i), 0, 0);
            } else {
            r += append3bytes(data.charCodeAt(i), data.charCodeAt(i+1),
            data.charCodeAt(i+2));
            }
            }
            return r;
            }

            function append3bytes(b1, b2, b3) {
            c1 = b1 >> 2;
            c2 = ((b1 & 0x3) << 4) | (b2 >> 4);
            c3 = ((b2 & 0xF) << 2) | (b3 >> 6);
            c4 = b3 & 0x3F;
            r = "";
            r += encode6bit(c1 & 0x3F);
            r += encode6bit(c2 & 0x3F);
            r += encode6bit(c3 & 0x3F);
            r += encode6bit(c4 & 0x3F);
            return r;
            }

            function encode6bit(b) {
            if (b < 10) {
            return String.fromCharCode(48 + b);
            }
            b -= 10;
            if (b < 26) {
            return String.fromCharCode(65 + b);
            }
            b -= 26;
            if (b < 26) {
            return String.fromCharCode(97 + b);
            }
            b -= 26;
            if (b == 0) {
            return '-';
            }
            if (b == 1) {
            return '_';
            }
            return '?';
            }
            ]]>

            async function fetchPlantUMLDiagram(plantUMLCode) {
                const plantUMLServerUrl = 'http://www.plantuml.com/plantuml/png/';

                try {
                    console.error('PlantUML code ' + plantUMLCode)

                    // DEFLATE compression
                    const utf8PlantUMLCode = unescape(encodeURIComponent(plantUMLCode));
                    const deflatedPlantUMLCode = encode64(deflate(utf8PlantUMLCode, 9));

                    console.error('Trying to fetch PlantUML diagram from: ' + plantUMLServerUrl + deflatedPlantUMLCode)
                    const response = await fetch(`${plantUMLServerUrl}${deflatedPlantUMLCode}`);

                    const blob = await response.blob();
                    const base64 = await new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result.split(',')[1]);
                    reader.onerror = reject;
                    reader.readAsDataURL(blob);
                    });

                    return base64;
                } catch (error) {
                    console.error(error);
                    return null;
                }
            }

            async function displayPlantUMLDiagram(plantUMLCode) {
                const base64Diagram = await fetchPlantUMLDiagram(plantUMLCode);
                object_id = '<xsl:value-of select="$objectId" />'
                console.error('Inserting PlantUML diagram into: ' + object_id + '')

                if (base64Diagram) {
                    const imgElement = document.getElementById(object_id);
                    imgElement.src = `data:image/png;base64,${base64Diagram}`;
                } else {
                    console.error('Failed to retrieve PlantUML diagram.');
                }
            }

            console.error(`<xsl:value-of select="$umlCode" />`)
            displayPlantUMLDiagram(`<xsl:value-of select="$umlCode" />`);
        
        </script>


        <p class="figure_caption">
            <span class="figure_caption_label">
                <xsl:value-of select="$proteus:lang_figure"/>
                <xsl:text> </xsl:text>
                <!-- from is needed to restart numbering in each document          -->
                <!-- level is needed to avoid restarting numbering in each section -->
                <xsl:number
                    from="object[@classes=':Proteus-document']"
                    count="object[@classes='external-resource'] | object[@classes='graphic-file']"
                    level="any"/>:
                <xsl:text> </xsl:text>
            </span>

            <xsl:value-of select="$umlCode" />
            
            <!-- applying markdown -->
            <xsl:call-template name="generate_markdown">
                <xsl:with-param name="content" select="properties/markdownProperty[@name='description']"/>
            </xsl:call-template>
        </p>

    </div>

</xsl:template>

</xsl:stylesheet>