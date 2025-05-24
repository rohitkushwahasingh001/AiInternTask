

document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const queryForm = document.getElementById('query-form');
    const uploadedDocumentsList = document.getElementById('uploaded-documents-list');
    const chatContainer = document.getElementById('chat-container');
    const spinner = document.getElementById('spinner');

    // Function to show/hide spinner
    function setLoading(isLoading) {
        if (isLoading) {
            spinner.style.display = 'block';
        } else {
            spinner.style.display = 'none';
        }
    }

    // Function to add a message to the chat display
    function addMessageToChat(sender, message, isHtml = false, citations = []) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', sender === 'user' ? 'user-message' : 'bot-message');

        if (isHtml) {
            messageElement.innerHTML = message;
        } else {
            messageElement.textContent = message;
        }

        if (citations.length > 0) {
            const citationsContainer = document.createElement('div');
            citationsContainer.classList.add('citations-container');
            citationsContainer.innerHTML = '<strong>Citations:</strong>';
            citations.forEach(citation => {
                const citationElement = document.createElement('span');
                citationElement.classList.add('citation-tag');
                citationElement.textContent = `(ID: ${citation.document_id}, File: ${citation.filename}, Page: ${citation.page}, Para: ${citation.paragraph})`;
                citationsContainer.appendChild(citationElement);
            });
            messageElement.appendChild(citationsContainer);
        }

        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight; // Auto-scroll to bottom
    }

    // Function to fetch and display uploaded documents
    async function fetchUploadedDocuments() {
        try {
            setLoading(true);
            const response = await fetch('/api/list-documents/');
            if (!response.ok) {
                throw new Error(`Server responded with status ${response.status}`);
            }
            const documents = await response.json();
            uploadedDocumentsList.innerHTML = ''; // Clear existing list

            if (documents.length === 0) {
                uploadedDocumentsList.innerHTML = '<li>No documents uploaded yet.</li>';
            } else {
                documents.forEach(doc => {
                    const li = document.createElement('li');
                    li.textContent = `ID: ${doc.document_id}, Filename: ${doc.filename}, Chunks: ${doc.num_chunks}`;
                    uploadedDocumentsList.appendChild(li);
                });
            }
        } catch (error) {
            console.error('Error fetching uploaded documents:', error);
            uploadedDocumentsList.innerHTML = `<li class="error-message">Error fetching documents: ${error.message}</li>`;
        } finally {
            setLoading(false);
        }
    }

    // Handle document upload and processing
    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const fileInput = document.getElementById('document-upload');
        const files = fileInput.files;

        if (files.length === 0) {
            alert('Please select files to upload.');
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        const uploadStatusDiv = document.getElementById('upload-status');
        uploadStatusDiv.textContent = 'Uploading and processing...';
        uploadStatusDiv.style.color = 'orange';

        try {
            setLoading(true); // Show spinner
            // IMPORTANT: Use relative path /api/upload-documents/
            const response = await fetch('/api/upload-documents/', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server responded with status ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            uploadStatusDiv.textContent = data.message;
            uploadStatusDiv.style.color = 'green';
            fileInput.value = ''; // Clear file input
            fetchUploadedDocuments(); // Refresh the list of uploaded documents
        } catch (error) {
            console.error('Error during upload:', error);
            uploadStatusDiv.textContent = `Upload failed: ${error.message}`;
            uploadStatusDiv.style.color = 'red';
            alert('Network error or server unreachable: Failed to fetch. Check console for details.');
        } finally {
            setLoading(false); // Hide spinner
        }
    });

    // Handle user query
    queryForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const queryInput = document.getElementById('query-input');
        const query = queryInput.value.trim();

        if (!query) {
            alert('Please enter a query.');
            return;
        }

        addMessageToChat('user', query); // Add user's query to chat
        queryInput.value = ''; // Clear query input

        try {
            setLoading(true); // Show spinner
            // IMPORTANT: Use relative path /api/query-documents/
            const response = await fetch('/api/query-documents/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server responded with status ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            addMessageToChat('bot', data.synthesized_response, false, data.tabular_citations); // Add bot's response
        } catch (error) {
            console.error('Error during query:', error);
            addMessageToChat('bot', 'Failed to get response. Please try again later.');
            alert('Failed to get response. Check console for details.');
        } finally {
            setLoading(false); // Hide spinner
        }
    });

    // Initial fetch of documents when the page loads
    fetchUploadedDocuments();
});
