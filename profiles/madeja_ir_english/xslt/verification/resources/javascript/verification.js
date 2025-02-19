function createCompletionRequest(prompt) {
    return new Promise((resolve, reject) => {
        const url = 'http://localhost:1234/v1/chat/completions';

        const requestData = {
            messages: [
                {
                    role: "system",
                    content: "You are a software engineer (Quality Assurance) verifying a functional requirement. Please verify the following requirement making sure it is concise and do not lead to misinterpretation. Do not change the meaning of the requirement:"
                },
                {
                    role: "user",
                    content: prompt
                }
            ],
            model: "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
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


function setupRequirementVerification() {
    const requirementTables = Array.from(document.querySelectorAll('table[class*="functional_requirement"]'));

    requirementTables.forEach(table => {
        const descriptionCells = table.querySelectorAll('td.Description-property');

        descriptionCells.forEach(td => {
            const verifyButton = document.createElement('button');
            verifyButton.textContent = 'Verify';
            verifyButton.style.cssText = `
                padding: 5px 10px;
                margin: 5px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                display: inline-block;
            `;

            verifyButton.onclick = async () => {
                try {
                    verifyButton.disabled = true;
                    verifyButton.textContent = 'Verifying...';

                    // Extract only the text content, ignoring buttons or other elements
                    const originalText = Array.from(td.childNodes)
                        .filter(node => node.nodeType === Node.TEXT_NODE) // Only text nodes
                        .map(node => node.textContent.trim())
                        .join(" ")
                        .replace(/\s+/g, ' '); // Clean up spaces

                    const response = await createCompletionRequest(originalText);

                    // Remove any existing response divs
                    td.querySelectorAll('.response-div').forEach(div => div.remove());

                    // Remove any previous status messages
                    td.querySelectorAll('div').forEach(div => {
                        if (div.textContent.includes('Processing...') || div.textContent.includes('Error:')) {
                            td.removeChild(div);
                        }
                    });

                    // Add the new response
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'response-div';
                    resultDiv.style.cssText = `
                        margin-top: 10px;
                        padding: 10px;
                        background-color: #f8f9fa;
                        border-left: 4px solid #28a745;
                        color: #2c5282;
                        line-height: 1.5;
                    `;
                    resultDiv.textContent = response;
                    td.appendChild(resultDiv);

                } catch (error) {
                    console.error('Error:', error);
                } finally {
                    verifyButton.disabled = false;
                    verifyButton.textContent = 'Verify';
                }
            };

            td.appendChild(verifyButton);
        });
    });
}



document.addEventListener('DOMContentLoaded', function () {
    setupRequirementVerification();
}
);
