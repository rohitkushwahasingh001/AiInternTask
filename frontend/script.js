// frontend/script.js
// --- Configuration ---
// For local testing, this will be "http://localhost:8000"
const BACKEND_URL = "http://localhost:8000";

// --- DOM Elements ---
const documentUpload = document.getElementById('documentUpload');
const uploadBtn = document.getElementById('uploadBtn');
const uploadStatus = document.getElementById('uploadStatus');
const docsList = document.getElementById('docsList');

const chatArea = document.getElementById('chatArea');
const queryInput = document.getElementById('queryInput');
const sendQueryBtn = document.getElementById('sendQueryBtn');
const queryStatus = document.getElementById('queryStatus');

// Elements related to themes, table, clear data, and modal are intentionally removed for basic UI
// const clearDataBtn = document.getElementById('clearDataBtn');
// const clearDataStatus = document.getElementById('clearDataStatus');
// const identifyThemesBtn = document.getElementById('identifyThemesBtn');
// const themesStatus = document.getElementById('themesStatus');
// const themesResult = document.getElementById('themesResult');
// const documentResponsesTableContainer = document.getElementById('documentResponsesTableContainer');
// const noRelevantSnippets = document.getElementById('noRelevantSnippets');
// const noThemesFound = document.getElementById('noThemesFound');
// const themeToggle = document.getElementById('themeToggle');
// const openUploadModalBtn = document.getElementById('openUploadModalBtn');
// const uploadModal = document.getElementById('uploadModal');
// const closeUploadModalBtn = document.getElementById('closeUploadModalBtn');
// const uploadStatusModal = document.getElementById('uploadStatusModal');


// --- Helper Functions ---

/**
 * Displays a message in a status div.
 * @param {HTMLElement} element - The status message div element.
 * @param {string} message - The message to display.
 * @param {string} type - 'success' or 'error' for styling.
 */
function showStatus(element, message, type) {
    element.textContent = message;
    element.className = `status-message ${type}`;
    element.style.display = 'block';
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000); // Hide after 5 seconds
}

/**
 * Adds a chat message to the chat area.
 * @param {string} message - The text content of the message.
 * @param {string} sender - 'user' or 'bot'.
 * @param {Array} [citations=[]] - Optional array of citation objects for bot messages.
 */
function addChatMessage(message, sender, citations = []) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message', `${sender}-message`);
    
    const messageParagraph = document.createElement('p');
    messageParagraph.textContent = message;
    messageDiv.appendChild(messageParagraph);

    // Keeping inline citations in chat bubble for basic UI
    if (sender === 'bot' && citations.length > 0) {
        const citationList = document.createElement('ul');
        citationList.classList.add('citation-list');
        const uniqueCitations = new Set(); 

        citations.forEach(citation => {
            const citationKey = `${citation.document_id}-${citation.page}-${citation.paragraph}`;
            if (!uniqueCitations.has(citationKey)) {
                const citationItem = document.createElement('li');
                citationItem.classList.add('citation');
                citationItem.textContent = `(DOC_ID: ${citation.document_id}, File: ${citation.filename}, Page: ${citation.page}, Para: ${citation.paragraph})`;
                citationList.appendChild(citationItem);
                uniqueCitations.add(citationKey);
            }
        });
        if (citationList.children.length > 0) {
            messageDiv.appendChild(citationList);
        }
    }
    chatArea.appendChild(messageDiv);
    chatArea.scrollTop = chatArea.scrollHeight; // Scroll to bottom
}

/**
 * Fetches and displays the list of uploaded documents.
 */
async function fetchAndDisplayDocuments() {
    try {
        const response = await fetch(`${BACKEND_URL}/api/documents/`);
        const data = await response.json();

        docsList.innerHTML = ''; // Clear existing list
        if (data.documents && data.documents.length > 0) {
            data.documents.forEach(doc => {
                const listItem = document.createElement('li');
                listItem.textContent = `ID: ${doc.document_id} - ${doc.filename}`;
                docsList.appendChild(listItem);
            });
        } else {
            const listItem = document.createElement('li');
            listItem.textContent = 'No documents uploaded yet.';
            docsList.appendChild(listItem);
        }
    } catch (error) {
        console.error('Error fetching documents:', error);
        showStatus(uploadStatus, 'Failed to load document list.', 'error');
    }
}


// --- Event Listeners ---

// Document Upload
uploadBtn.addEventListener('click', async () => {
    const files = documentUpload.files;
    if (files.length === 0) {
        showStatus(uploadStatus, 'Please select at least one file to upload.', 'error');
        return;
    }

    showStatus(uploadStatus, 'Uploading and processing documents...', '');
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    try {
        const response = await fetch(`${BACKEND_URL}/api/upload-documents/`, {
            method: 'POST',
            body: formData,
        });
        const result = await response.json();

        if (response.ok) {
            showStatus(uploadStatus, 'Documents uploaded and processed successfully!', 'success');
            documentUpload.value = ''; // Clear the input field
            fetchAndDisplayDocuments(); // Refresh the list of uploaded documents
        } else {
            showStatus(uploadStatus, `Upload failed: ${result.detail || result.message || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error during document upload:', error);
        showStatus(uploadStatus, `Network error or server unreachable: ${error.message}`, 'error');
    }
});

// Send Query
sendQueryBtn.addEventListener('click', async () => {
    const query = queryInput.value.trim();
    if (query === '') {
        showStatus(queryStatus, 'Please enter a query.', 'error');
        return;
    }

    addChatMessage(query, 'user');
    queryInput.value = ''; // Clear input field

    showStatus(queryStatus, 'Getting response...', '');

    const formData = new FormData();
    formData.append('query_text', query);

    try {
        const response = await fetch(`${BACKEND_URL}/api/query/`, {
            method: 'POST',
            body: formData,
        });
        const result = await response.json();

        if (response.ok) {
            // Display the concise synthesized response in chat area
            addChatMessage(result.synthesized_response, 'bot', result.tabular_citations); // Keep citations in chat bubble for basic UI

            showStatus(queryStatus, 'Response received.', 'success');
        } else {
            addChatMessage(`Error: ${result.detail || result.message || 'Unknown error'}`, 'bot');
            showStatus(queryStatus, `Query failed: ${result.detail || result.message || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error during query:', error);
        addChatMessage(`Error: Network error or server unreachable.`, 'bot');
        showStatus(queryStatus, `Network error or server unreachable: ${error.message}`, 'error');
    }
});

// Allow sending query with Enter key
queryInput.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        sendQueryBtn.click();
    }
});

// Removed theme toggle button and its event listener
// Removed clear data button and its event listener
// Removed modal open/close listeners

// --- Initial Load ---
document.addEventListener('DOMContentLoaded', () => {
    fetchAndDisplayDocuments(); // Load documents on page load
});
