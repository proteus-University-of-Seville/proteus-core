// LLM requirements verification script
// Version: 1.0
// Date: 27-02-2025
// 
// This script is used to modify the HTML in order to add verification buttons to each requirement type.
// The verification buttons will call the LLM model to verify the requirement text.
// The script will look for tables with class defined in the SPECIFIC_VERIFICATION_CONTEXT_DICT
// A general verification context is provided to the LLM along with the specific context for each requirement type.
// A button is added in a new row at the end of the table to verify all the text in the table.
// When the button is clicked, the script will gather all the text in rows with class 'verifiable-property' and send it to the LLM model.
// XSLT is responsible for setting up the 'verifiable-property' class in the HTML
// The script will display the response from the LLM model in the same row as the button.

// In order to add new verifiable requirements or other elements, make sure it is displayed in a table marking the rows with the
// 'verifiable-property' class and it is added to the SPECIFIC_VERIFICATION_CONTEXT_DICT with the corresponding context.

// This is based on LM Studio server API, the LLM can be changed to a different model by changing the LLM constant.
// The API call can be modified if necessary in the 'createCompletionRequest' function.

// This script works outside PROTEUS when exported as HTML as long as the LLM server is accessible.

// -----------------------------------------------------------------------
// Constants
// -----------------------------------------------------------------------

const LLM = "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF";
const GENERAL_VERIFICATION_CONTEXT = "Please verify the following requirement making sure it is concise and do not lead to misinterpretation. Do not change the meaning of the requirement.";
const SPECIFIC_VERIFICATION_CONTEXT_DICT = {
    "general_requirement": "You are a software engineer (Quality Assurance) verifying a general requirement. The description will be provided.",
    "system_actor": "You are a software engineer (Quality Assurance) verifying a system actor. The description will be provided.",
    "information_requirement": "You are a software engineer (Quality Assurance) verifying an information requirement. The description and the specific data will be provided.",
    "use_case": "You are a software engineer (Quality Assurance) verifying a use case. The precondition, description, use case steps, and postcondition will be provided.",
    "functional_requirement": "You are a software engineer (Quality Assurance) verifying a functional requirement. The description will be provided.",
    "nonfunctional_requirement": "You are a software engineer (Quality Assurance) verifying a non-functional requirement. The description will be provided.",
    "business_rule": "You are a software engineer (Quality Assurance) verifying a business rule. The description will be provided.",
};


// -----------------------------------------------------------------------
// Main functions
// -----------------------------------------------------------------------

// Setup the verification buttons for each requirement type
// listed in the SPECIFIC_VERIFICATION_CONTEXT_DICT
function setupRequirementVerification() {
    for (const [req_class, specific_context] of Object.entries(SPECIFIC_VERIFICATION_CONTEXT_DICT)) {
        const requirementTables = Array.from(document.querySelectorAll("table")).filter(table =>
            table.classList.contains(req_class)
        );
        setupVerifyButton(requirementTables, specific_context + GENERAL_VERIFICATION_CONTEXT);
    }
}


// Setup the verification button for each verifiable property in the given tables.
// It calls the createCompletionRequest function to ask the LLM model to verify the property.
function setupVerifyButton(tables, context) {
    tables.forEach(table => {
        const descriptionCells = table.querySelectorAll('td.verifiable-property');

        // Create a row at the end of the table for the verification output and button
        const outputRow = document.createElement('tr');
        const outputCell = document.createElement('td');
        outputCell.colSpan = descriptionCells.length;
        outputCell.style.cssText = `
            padding: 10px;
            background-color: #f8f9fa;
            border-top: 2px solid #ccc;
            text-align: left;
        `;

        const buttonCell = document.createElement('td');
        buttonCell.style.textAlign = 'center';

        outputRow.appendChild(buttonCell);
        outputRow.appendChild(outputCell);
        table.appendChild(outputRow);

        // Create a button to verify all fields
        const verifyAllButton = document.createElement('button');
        verifyAllButton.textContent = 'Verify using AI';
        verifyAllButton.style.cssText = `
            padding: 8px 15px;
            margin: 10px 0;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        `;

        verifyAllButton.onclick = async () => {
            try {
                verifyAllButton.disabled = true;
                verifyAllButton.textContent = 'Verifying...';

                // Gather all verifiable text
                const allText = Array.from(descriptionCells)
                    .map(td => td.textContent.trim().replace(/\s+/g, ' ')) // Extract all visible text
                    .join(' | ');

                const response = await createCompletionRequest(allText, context);

                // Display the response in the output row
                outputCell.textContent = response;
            } catch (error) {
                console.error('Error:', error);
                outputCell.textContent = 'Error verifying data';
            } finally {
                verifyAllButton.disabled = false;
                verifyAllButton.textContent = 'Verify using AI';
            }
        };

        // Append the button to the same row where the response will be displayed
        buttonCell.appendChild(verifyAllButton);
    });
}

// Ask the LLM model to verify a given prompt. Context is used to
// provide additional instructions to the model.
function createCompletionRequest(prompt, context) {
    return new Promise((resolve, reject) => {
        const url = 'http://localhost:1234/v1/chat/completions';

        const requestData = {
            messages: [
                {
                    role: "system",
                    content: context
                },
                {
                    role: "user",
                    content: prompt
                }
            ],
            model: LLM,
            temperature: 0.7,
            max_tokens: -1,
            stream: true
        };

        const xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');

        let accumulatedResponse = '';

        xhr.onreadystatechange = function () {
            if (xhr.readyState === 3 || xhr.readyState === 4) {
                try {
                    const newText = parseStreamResponse(xhr.responseText);
                    if (newText !== accumulatedResponse) {
                        accumulatedResponse = newText;

                        // Update UI only when we have a complete response
                        if (xhr.resultDiv) {
                            xhr.resultDiv.textContent = accumulatedResponse;
                        }
                    }

                    if (xhr.readyState === 4) {
                        if (xhr.status === 200) {
                            resolve(accumulatedResponse);
                        } else {
                            reject(new Error(`Request failed with status ${xhr.status}`));
                        }
                    }
                } catch (error) {
                    reject(error);
                }
            }
        };

        xhr.onerror = function () {
            reject(new Error("Request failed"));
        };

        // Create a result div and attach it to the xhr object
        const resultDiv = document.createElement('div');
        resultDiv.style.cssText = `
            margin-top: 10px;
            padding: 10px;
            background-color: #f8f9fa;
            border-left: 4px solid #28a745;
            color: #2c5282;
            line-height: 1.5;
        `;
        xhr.resultDiv = resultDiv;

        xhr.send(JSON.stringify(requestData));
        return resultDiv;
    });
}

// -----------------------------------------------------------------------
// Helper functions
// -----------------------------------------------------------------------


// Helper function to parse the response from the stream
// and return the full response when the stream is finished.
// This is necessary because the response is streamed in chunks
// and we need to accumulate the full response and discard the
// incomplete chunks.
function parseStreamResponse(text) {
    let completeResponse = '';
    const lines = text.trim().split('\n');

    for (const line of lines) {
        if (line.startsWith('data: ')) {
            try {
                const jsonData = JSON.parse(line.substring(6));

                if (jsonData.choices && jsonData.choices[0].delta.content) {
                    completeResponse += jsonData.choices[0].delta.content;
                }

                // If the stream is finished, return the full response
                if (jsonData.choices && jsonData.choices[0].finish_reason === 'stop') {
                    return completeResponse;
                }
            } catch {
                continue;
            }
        }
    }

    return completeResponse;
}

// -----------------------------------------------------------------------
// Initial load
// -----------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', function () {
    setupRequirementVerification();
}
);
