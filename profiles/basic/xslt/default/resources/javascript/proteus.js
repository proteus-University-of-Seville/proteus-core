// =========================================================================
// File        : proteus.js
// Description : Javascript functions for Proteus XSLT                      
// Date        : 16/01/2024            
// Version     : 0.1                    
// Author      : José María Delgado Sánchez
// =========================================================================
// NOTE: console.error is used because logs are not shown in python console,
//       this is for debugging purposes only.
// =========================================================================

// Constants
const PROTEUS_XSLT_VERSION = "0.1";
const PROTEUS_XSLT_NAME = "Proteus XSLT";
const PROTEUS_XSLT_LOG_PREFIX = `${PROTEUS_XSLT_NAME}:${PROTEUS_XSLT_VERSION} - `;

// WebChannel objects
var proteusBasics = null;
var documentInteractions = null;


// -----------------------------------------------------------------------
// Custom log function
// -----------------------------------------------------------------------
function log(message) {
    console.log(PROTEUS_XSLT_LOG_PREFIX + message);
}

// -----------------------------------------------------------------------
// QWebChannel loading
// -----------------------------------------------------------------------

// NOTE: This function is used to interact with Python code, if you are
//       using this script outside PROTEUS application, you can remove
//       this function to prevent errors.
function loadWebChannel() {
    try {
        new QWebChannel(qt.webChannelTransport, function (channel) {
            proteusBasics = channel.objects.proteusBasics;
            documentInteractions = channel.objects.documentInteractions;
            log("QWebChannel loaded.")
        });
    } catch (error) {
        console.error(error.message);
    }
}


// -----------------------------------------------------------------------
// Function    : propertiesDialog
// Description : Open the properties dialog for the element with the given
//               Id. Use documentInteractions object to access python
//               open_properties_dialog method.
// Date        : 16/01/2024
// Version     : 0.1
// Author      : José María Delgado Sánchez
// -----------------------------------------------------------------------
// NOTE: This function is used to interact with Python code, if you are
//       using this script outside PROTEUS application, you can remove
//       this function to prevent errors.
function propertiesDialog(id, event) {
    if (id == "" || id == null) {
        log("Doubleclicked on a symbolic linked object with empty Id, propagating event to parent.");
    } else {
        log("Doubleclicked on element with Id " + id)
        documentInteractions.open_properties_dialog(id);
        event.stopPropagation();
    }
}


// -----------------------------------------------------------------------
// Function    : selectAndNavigate
// Description : Select the object in the document tree and navigate to
//               it. If the object is not in the current document, ask
//               the user to navigate to the document where the object
//               is located. Use documentInteractions object to access
//               python select_and_navigate_to_object method.
// Date        : 16/01/2024
// Version     : 0.1
// Author      : José María Delgado Sánchez
// -----------------------------------------------------------------------
// NOTE: This function is used to interact with Python code, if you are
//       using this script outside PROTEUS application, you can remove
//       this function to prevent errors.
function selectAndNavigate(id, event) {
    if (id == "" || id == null) {
        log("selectAndNavigate received an empty Id, propagating event to parent.");
    } else {
        log("Clicked on anchor element with Id " + id)
        documentInteractions.select_and_navigate_to_object(id);
        event.stopPropagation();
    }
}


// -----------------------------------------------------------------------
// Function    : subscribeProteusId
// Description : Subscribe all the elements with data-proteus-id to the
//               necessary events.
// Date        : 16/01/2024
// Version     : 0.1
// Author      : José María Delgado Sánchez
// -----------------------------------------------------------------------
// NOTE: This function is used to interact with Python code, if you are
//       using this script outside PROTEUS application, you can remove
//       this function to prevent errors.
function suscribeProteusId() {
    const elements = document.querySelectorAll('*[data-proteus-id]');
    elements.forEach(element => {

        // propertiesDialog on double click event
        element.addEventListener('dblclick', function (event) {
            propertiesDialog(element.getAttribute('data-proteus-id'), event);
        });

        // NOTE: Add more events here if needed
    });
}


// -----------------------------------------------------------------------
// Function    : onTreeObjectSelected
// Description : Scroll the document to the element with the given Id.
// Date        : 16/01/2024
// Version     : 0.1
// Author      : José María Delgado Sánchez
// -----------------------------------------------------------------------
// NOTE: This function is used to interact with Python code, if you are
//       using this script outside PROTEUS application, you can remove
//       this function to prevent errors.
function onTreeObjectSelected(id) {
    if (id == "" || id == null) {
        log("Scroll error, cannot scroll to an empty Id.");
        return;
    }

    const element = document.getElementById(id)

    if (element != null) {
        log("Scrolling to element with Id " + id)
        element.scrollIntoView({ behavior: "smooth" });
    } else {
        log("Scroll error, element with Id " + id + " not found.");
    }
}


// -----------------------------------------------------------------------
// Function    : removeIdsInsideSymbolicLink
// Description : Remove all the Ids of the elements inside a symbolic
//               link. This is necessary because the Ids of the elements
//               inside a symbolic link are going to be duplicated.
// Date        : 16/01/2024
// Version     : 0.1
// Author      : José María Delgado Sánchez
// -----------------------------------------------------------------------
function removeIdsInsideSymbolicLink() {
    const symbolicLinkDivs = document.querySelectorAll('.symbolic-link');
    symbolicLinkDivs.forEach(symbolicLinkDiv => {
        const elementsBelow = symbolicLinkDiv.querySelectorAll('*[id]');
        elementsBelow.forEach(element => {
            element.removeAttribute('id');
        });
    });
}

// -----------------------------------------------------------------------
// Function    : traceabilityMatrixButtonsSetup
// Description : Setup the buttons of the traceability matrix.
// Date        : 08/02/2024
// Version     : 0.1
// Author      : José María Delgado Sánchez
// -----------------------------------------------------------------------
function traceabilityMatrixButtonsSetup() {
    const reduce_font_buttons = document.querySelectorAll('button.reduce_font');
    const increase_font_buttons = document.querySelectorAll('button.increase_font');

    log('Setting up traceability matrix buttons')

    // Subscribe buttons to reduce and increase font size
    reduce_font_buttons.forEach(button => {
        button.addEventListener('click', function (event) {
            const parent_table = button.closest('table.traceability_matrix');
            update_font_size(parent_table, -1);
            event.stopPropagation();
        });

        // Prevent double click event triggering
        button.addEventListener('dblclick', function (event) {
            event.stopPropagation();
        });
    }
    );

    // Subscribe buttons to reduce and increase font size
    increase_font_buttons.forEach(button => {
        button.addEventListener('click', function (event) {
            const parent_table = button.closest('table.traceability_matrix');
            update_font_size(parent_table, 1);
            event.stopPropagation();
        });

        // Prevent double click event triggering
        button.addEventListener('dblclick', function (event) {
            event.stopPropagation();
        });
    }
    );
}

// Helper function to update the font size of the traceability matrix
function update_font_size(parent_table, size) {
    var matrix_columns = parent_table.querySelectorAll("th.matrix_column");
    var font_size = parseInt(getComputedStyle(matrix_columns[0]).fontSize, 10);

    matrix_columns.forEach(column => {
        column.style.fontSize = font_size + size + "px";
    });
}


// =========================================================================
// Execute code on DOMContentLoaded event
// =========================================================================
document.addEventListener('DOMContentLoaded', function () {
    // Remove Ids to fix HTML code
    removeIdsInsideSymbolicLink();

    // Load QWebChannel
    loadWebChannel();

    // Suscribe all the elements with data-proteus-id to the necessary events
    suscribeProteusId();
    
    // Setup the buttons of the traceability matrix
    traceabilityMatrixButtonsSetup();
});

// =========================================================================
// Execute code on load event
// =========================================================================
window.onload = function () {

};
