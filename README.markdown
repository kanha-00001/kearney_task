# AI-Powered Chatbot MVP

This project is an AI-powered chatbot developed as part of the AI Engineering Internship application for Kearney. It processes a CSV file (`Sugar_Spend_Data.csv`) containing commodity data and allows users to ask natural language questions about the data, leveraging a Retrieval-Augmented Generation (RAG) pipeline powered by LlamaIndex and GROQ API. The frontend is built with React, Vite, Tailwind CSS, and shadcn/ui, while the backend uses Flask. The chatbot maintains conversation history to handle follow-up questions contextually.

## Features
- **Data Processing**: Loads and processes a CSV file (`Sugar_Spend_Data.csv`) from the `assets/` directory.
- **RAG Pipeline**: Uses LlamaIndex with Chroma vector store and Sentence-BERT embeddings to retrieve relevant data, combined with Grok API for natural language responses.
- **Chat History**: Maintains user-specific conversation history to provide context for related questions.
- **Frontend UI**: Responsive chat interface with Tailwind CSS and shadcn/ui components, featuring message history, loading indicators, and markdown rendering.
- **Backend API**: Flask server with a `/query` endpoint for handling natural language queries.

## Prerequisites
- **Node.js** (v18 or higher) for the frontend.
- **Python** (3.8–3.11) for the backend.
- **GROQ API Key** .
- **CSV File**: `Sugar_Spend_Data.csv` in `assets/` with the format:
  ```csv
  Commodity,Top Supplier,Quantity (KG),Spend (USD)
  Raw Sugar,Tereos,4214,407182.24
  ...
  ```

## Project Structure
```
chatbot-mvp/
├── assets/
│   └── Sugar_Spend_Data.csv        # Input CSV file
├── backend/
│   ├── venv/                       # Python virtual environment
│   ├── .env                        # Environment variables (GROQ_API_KEY)
│   ├── rag_tool.py                 # RAG pipeline logic
│   ├── app.py                      # Flask server
│   └── chroma_db/                  # Chroma vector store (auto-generated)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatComponent.jsx   # Chat UI component
│   │   │   └── ui/                 # shadcn/ui components
│   │   ├── App.jsx                 # Main React component
│   │   ├── index.css               # Tailwind CSS
│   │   └── main.jsx                # Entry point
│   ├── vite.config.js              # Vite configuration
│   ├── package.json                # Frontend dependencies
│   └── tailwind.config.js          # Tailwind configuration
└── README.md                       # This file
```

## Setup Instructions

### Backend Setup
1. **Navigate to Backend**:
   ```bash
   cd backend
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install flask flask-cors llama-index llama-index-embeddings-huggingface llama-index-llms-groq llama-index-vector-stores-chroma chromadb python-dotenv sentence-transformers pandas
   ```

4. **Configure Environment**:
   - Create `.env` in `backend/`:
     ```plaintext
     GROQ_API_KEY=your_grok_api_key_here
     ```
   - Replace `your_grok_api_key_here` with your xAI Grok API key.

5. **Place CSV File**:
   - Ensure `Sugar_Spend_Data.csv` is in `chatbot-mvp/assets/`.

6. **Run Backend**:
   ```bash
   python app.py
   ```
   - Verify logs show: “RAG index built successfully”.
   - Server runs at `http://localhost:5000`.

### Frontend Setup
1. **Navigate to Frontend**:
   ```bash
   cd frontend
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   npm install axios react-markdown lucide-react
   ```

3. **Run Frontend**:
   ```bash
   npm run dev
   ```
   - Open `http://localhost:5173` in a browser.

## Usage
1. **Access the Chatbot**:
   - Visit `http://localhost:5173`.
   - The UI displays a chat interface with a header, message area, and input field.

2. **Ask Questions**:
   - Enter queries about the CSV data, e.g.:
     - “What is the top supplier for Raw Sugar?”
     - “What is their spend?” (follow-up question uses history context).
   - Messages appear in the chat, with user messages (blue) on the right and AI responses (white) on the left with avatars.

3. **Chat History**:
   - The backend stores conversation history per session, enabling contextual follow-up questions.
   - The frontend displays all messages in the session.

## Testing
- **Sample Queries**:
  - “What is the top supplier for Raw Sugar?” → “The top supplier for Raw Sugar is Tereos.”
  - “What is their spend?” → “The spend for Raw Sugar from Tereos is $407,182.24.”
- **Debugging**:
  - Check backend logs (`backend/app.py`) for errors (e.g., CSV not found, API issues).
  - Use browser DevTools (Console/Network) to verify API responses.
  - Test with `backend/test.py` to isolate RAG functionality:
    ```bash
    python test.py
    ```

## Deployment (Optional)
- **Backend (Render)**:
  - Push `backend/` to a Git repository.
  - Deploy on Render, set `PYTHON_VERSION=3.11`, and add `.env`.
  - Update `API_URL` in `ChatComponent.jsx` to the deployed URL.
- **Frontend (Vercel)**:
  - Push `frontend/` to a Git repository.
  - Deploy on Vercel, update `API_URL` in `ChatComponent.jsx`.

## Notes
- **Chat History**: Stored in-memory (session-based). For production, use a database like Redis.
- **CSV Loading**: Automatically loads `../assets/Sugar_Spend_Data.csv` on backend startup.
- **UI**: Uses Tailwind CSS and shadcn/ui for a modern, responsive design with markdown rendering.
- **Dependencies**: Ensure all Python and Node.js packages are installed as listed.
- **TensorFlow Warnings**: Harmless warnings from `sentence-transformers`. Suppress with:
  ```bash
  export TF_ENABLE_ONEDNN_OPTS=0
  ```

## Troubleshooting
- **500 Internal Server Error**: Check backend logs for CSV path or Grok API issues.
- **CORS Errors**: Verify `flask-cors` is installed and `withCredentials: true` is set in frontend API calls.
- **No Context in Follow-ups**: Ensure `session_id` is sent with requests and backend logs show history context.

For further assistance, contact the developer or check the xAI API documentation at [https://x.ai/api](https://x.ai/api).