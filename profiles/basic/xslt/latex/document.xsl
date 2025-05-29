<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:proteus="http://proteus.us.es"
    xmlns:proteus-utils="http://proteus.us.es/utils"
    exclude-result-prefixes="proteus"
>
    <!-- Match the root object of the document -->
    <xsl:template match="object[@classes=':Proteus-document']">

    <html>
        <head>
            <title><xsl:value-of select="properties/*[@name=':Proteus-name']"/></title>
            <style>
                /* Estilos para la cabecera fija */
                .fixed-header {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    background-color: #333;
                    color: white;
                    text-align: center;
                    padding: 10px 0;
                    z-index: 1000;
                    font-family: Arial, sans-serif;
                }

                /* Agregar margen superior al contenido para evitar que se solape con la cabecera */
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                }

                .content {
                    margin-top: 50px; /* Altura de la cabecera fija */
                    padding: 20px;
                }
            </style>
        </head>
        <body>
            <div class="fixed-header">
                Para exportar a LaTeX, instala un servidor de LaTeX local (comando pdflatex) y selecciona la opción de exportar desde LaTeX.
            </div>
            <pre><code class="language-latex"><latex>

            \documentclass[conference,a4paper]{IEEEtran}
            \usepackage{graphicx}

            \begin{document}

            \title{<xsl:apply-templates select="properties/*[@name=':Proteus-name']"/>}

            \begin{abstract}
            <xsl:apply-templates select="properties/*[@name='description']"/>
            \end{abstract}

            <xsl:apply-templates select="children/object"/>

            \end{document}
            
            </latex></code></pre>
        </body>

        <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet"></link>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-latex.min.js"></script>

        <script>
            document.addEventListener('DOMContentLoaded', (event) => {
                hljs.highlightAll();
            });
        </script>

    </html>

    </xsl:template>

</xsl:stylesheet>