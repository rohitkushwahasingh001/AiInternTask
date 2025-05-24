# 🚀 Theme identifier AI Document Chatbot

This is an interactive AI Chatbot that allows you to upload various documents (PDF, DOCX, Images, TXT), ask questions about them, and identify common themes within the documents.

## ✨ Features

* **Multi-format Document Upload:** 📄 Upload PDF, 🖼️ PNG, JPG, JPEG, TIFF, 📝 TXT, and ✍️ DOCX files.
* **OCR Capabilities:** 📸 Utilizes Optical Character Recognition (OCR) to extract text from scanned PDFs and image files.
* **Smart Querying:** 💬 Provides accurate and relevant answers to your questions based on the uploaded documents.
* **Cited Responses:** 📚 Bot responses come with clear citations to the source documents (Document ID, Filename, Page, Paragraph).
* **Theme Identification:** 💡 Identifies common and distinct themes across the uploaded documents.
* **Data Management:** 🗑️ Ability to reset the knowledge base and clear all uploaded data.
* **Attractive UI:** 🌑 A clean and modern user interface with a default dark theme and a loading spinner.

## 🛠️ Tech Stack

**Backend:**
* **FastAPI:** ⚡️ A fast (high-performance) web framework.
* **LangChain:** 🔗 Framework for building LLM-powered applications.
* **ChromaDB:** 📊 An embedding database (vector store) used for semantic search of documents.
* **Google Gemini (via `langchain-google-genai`):** 🧠 AI model used for answering questions and identifying themes.
* **`pytesseract`:** 🔡 Python library for OCR.
* **`pdf2image` & Poppler:** 📄 For converting PDFs to images.
* **`python-docx`:** ✍️ For extracting text from DOCX files.
* **`gunicorn` & `uvicorn`:** 🌐 ASGI servers for production.

**Frontend:**
* **HTML5:** 🖥️ Web page structure.
* **CSS3:** 🎨 For styling.
* **JavaScript:** 🚀 For interactivity.

## 📂 Project Structure


chatbot_theme_identifier/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── models/
│   │   │   └── responses.py
│   │   ├── services/
│   │   │   ├── chat_service.py
│   │   │   ├── document_processor.py
│   │   │   ├── theme_identifier.py
│   │   │   └── vector_db_service.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── .env                  # 🔑 Environment variables (e.g., API keys)
├── .gitignore            # 🚫 Files/folders to ignore in Git
└── render.yaml           # 🚀 Render deployment configuration


## ⚙️ Local Setup

Follow these steps to run the project on your system:

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/rohitkushwahasingh001/wasserstoff-AiInternTask.git](https://github.com/rohitkushwahasingh001/wasserstoff-AiInternTask.git)
    cd wasserstoff-AiInternTask
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # .venv\Scripts\activate   # Windows
    ```

3.  **Install Backend Dependencies:**
    ```bash
    cd backend
    pip install -r requirements.txt
    cd .. # Go back to project root
    ```

4.  **Create `.env` File:**
    Create a file named `.env` in your project's **root directory** (`chatbot_theme_identifier/`) and add your Google Gemini API key:
    ```dotenv
    GEMINI_API_KEY="your_google_gemini_api_key_here"
    ```
    * You can obtain your API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

5.  **Install Tesseract and Poppler:**
    * **macOS (Homebrew):**
        ```bash
        brew install tesseract poppler
        ```
    * **Linux (Debian/Ubuntu):**
        ```bash
        sudo apt update
        sudo apt install tesseract-ocr poppler-utils
        ```
    * **Windows:**
        * Download and install [Tesseract installer](https://tesseract-ocr.github.io/tessdoc/Downloads.html). Ensure you add it to your system PATH.
        * Download [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) and add its `bin` folder to your system PATH.
        * **Important:** You might need to set `self.poppler_path` in `backend/app/services/document_processor.py` to the path of Poppler's `bin` directory if `pdf2image` doesn't find it automatically.

6.  **Run Backend:**
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```
    Your FastAPI backend will run on `http://127.0.0.1:8000`.

7.  **Run Frontend:**
    Open a new terminal, navigate to your project's **root directory** (`chatbot_theme_identifier/`), and then go into the `frontend` directory:
    ```bash
    cd frontend
    python3 -m http.server 8001
    ```
    Your Frontend will be available at `http://localhost:8001`.

8.  **Update Frontend `script.js` URL (if testing locally):**
    Open the `frontend/script.js` file and set `BACKEND_URL` to `http://localhost:8000`:
    ```javascript
    const BACKEND_URL = "http://localhost:8000";
    ```
    * If you are preparing for deployment, leave it empty or replace it with the Render URL.

## 🚀 Deployment on Render

We've chosen Render for deployment as it offers a straightforward deployment experience for both FastAPI backends and static frontends.

1.  **Push to GitHub:**
    Ensure all your latest code is pushed to GitHub, including the `render.yaml` file located in your project's root.

2.  **Go to Render Dashboard:**
    Log in to [dashboard.render.com](https://dashboard.render.com/).

3.  **Create Backend Web Service:**
    * Click `New +`, then select `Web Service`.
    * Connect your GitHub repository.
    * **Name:** `chatbot-backend` (or any unique name).
    * **Root Directory:** `backend/`
    * **Runtime:** `Python 3`
    * **Build Command:** `pip install -r requirements.txt && apt-get update -y && apt-get install -y tesseract-ocr libsm6 libxext6 libxrender-dev poppler-utils`
    * **Start Command:** `gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker`
    * **Environment Variables:** Add `GEMINI_API_KEY` and paste the value of your Google Gemini API key.
    * Click `Create Web Service`.

4.  **Create Frontend Static Site:**
    * Click `New +`, then select `Static Site`.
    * Connect your GitHub repository.
    * **Name:** `chatbot-frontend` (or any unique name).
    * **Root Directory:** `frontend/`
    * **Build Command:** `echo "No build command for static HTML/CSS/JS"`
    * **Publish Directory:** `.` (a single dot)
    * Click `Create Static Site`.

5.  **Update Frontend `script.js` with Backend URL:**
    Once your `chatbot-backend` is live on Render, copy its URL from the Render dashboard (it will look something like `https://your-backend-name.onrender.com`).
    Then, open your `frontend/script.js` file and replace `BACKEND_URL` with this URL:
    ```javascript
    const BACKEND_URL = "[https://your-backend-name.onrender.com](https://your-backend-name.onrender.com)"; // <-- Paste your Render Backend URL here
    ```
    Push this change to GitHub. Your frontend will automatically redeploy.

## 🚀 Usage

1.  **Upload Documents:**
    * In the "Upload Documents" section, choose files and click "Upload & Process Documents".
    * Uploaded documents will appear in the "Uploaded Documents" list.

2.  **Chat with Documents:**
    * In the "Chat with Documents" section, type your question and click "Send Query".
    * The chatbot will respond based on your documents, including citations.

3.  **Identify Themes:**
    * In the "Identify Themes" section, click the "Identify Common Themes" button.
    * The chatbot will identify prominent themes across your uploaded documents and display them with relevant document IDs.

4.  **Clear Data:**
    * Click the "Clear All Data" button to reset all uploaded documents and the knowledge base.

## 📺 Demo Video

[Insert your demo video link here]

## 💡 Future Enhancements

* **Persistent Database:** Configure persistent storage for ChromaDB on Render or use a cloud-based vector database like Pinecone/Weaviate.
* **Improved Error Handling:** More user-friendly error messages in the UI.
* **Authentication:** Add authentication for users.
* **Document Preview:** Ability to view previews of uploaded documents.
* **Enhanced Theme Presentation:** More detailed and interactive UI for themes.
