# AI Agent – Life Insurance Support Assistant

## Project Description
The **AI Agent – Life Insurance Support Assistant** is an intelligent conversational AI system designed to provide accurate, context-aware, and user-friendly support for life insurance-related queries. By leveraging Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), vector databases, and agent-based workflows, the system delivers intelligent, document-backed responses. It is built to improve customer support efficiency, maintain multi-turn conversation continuity, and ensure high accuracy by highlighting references from source documents.

## Architecture
This project implements a robust **GenAI Architecture (LLM + RAG + Agents)**.
The workflow is orchestrated as follows:
1. User submits a query via the Frontend UI.
2. The query is received by the FastAPI Backend.
3. The LangGraph agent orchestrates the workflow.
4. Relevant document chunks are retrieved from the Chroma Vector Database.
5. The query and context are combined and sent to the OpenAI API (LLM).
6. The generated response and the exact source references are returned to the user.
7. The conversation is stored in PostgreSQL for persistent chat history.

## Components and their Functionality

- **Frontend (HTML/CSS/JS via FastAPI Templates):**
  - **Left Panel (Chat Management):** Allows users to create new chats, search previous conversations, and load past chat history.
  - **Middle Panel (References Section):** Displays the exact source documents and highlights relevant passages used by the AI to answer the query.
  - **Right Panel (Chat Interface):** The main chat area where the user interacts with the AI.
  - **Ingest Documents Button:** The crucial bridge between raw files (PDFs, TXT, etc.) and the AI's "brain." It reads documents from the `Documents/` folder, chunks them, embeds them using OpenAI, and saves them to ChromaDB. This button ensures the AI's knowledge stays up-to-date whenever new files are added or modified.

- **Backend (FastAPI):** Handles API routing, query processing, and integration with the AI layers.
- **AI Agent Layer (LangGraph):** Orchestrates the retrieval and generation workflow, manages context, and ensures intelligent logic routing.
- **Vector Database (Chroma):** Stores document embeddings and performs semantic similarity searches to retrieve relevant content for RAG.
- **Relational Database (PostgreSQL):** Persistently stores chat history and sessions.
- **LLM (OpenAI API):** Responsible for reasoning, summarizing, and generating the final human-like response.

## Database Table Structure (SQL)
The project uses PostgreSQL to store conversation history. The schema is as follows:

```sql
CREATE DATABASE support_agent;

BEGIN;
CREATE TABLE IF NOT EXISTS public.chat_history
(
    id serial NOT NULL,
    session_id uuid NOT NULL,
    user_message text COLLATE pg_catalog."default" NOT NULL,
    ai_response text COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    references_data text COLLATE pg_catalog."default" DEFAULT '[]'::text,
    CONSTRAINT chat_history_pkey PRIMARY KEY (id)
);
END;

CREATE INDEX idx_chat_session_id ON chat_history(session_id);
```

## Technology Used
- **Programming Language:** Python (3.10+)
- **Backend Framework:** FastAPI
- **AI Orchestration Framework:** LangGraph / LangChain
- **LLM:** OpenAI API
- **Vector DB:** ChromaDB
- **Relational DB:** PostgreSQL
- **Frontend:** HTML, CSS, Vanilla JavaScript (served via FastAPI Jinja2 templates)

## Libraries Used
- `fastapi[standard]`
- `uvicorn`
- `psycopg2`
- `langgraph`
- `langchain` & `langchain-openai` & `langchain-chroma`
- `chromadb`
- `openai`
- `pypdf`, `python-pptx` (Document Loaders)
- `python-dotenv`

---

## How to run the source code from the GitHub Repo

### 1. Prerequisites
- **Python 3.10+** installed
- **PostgreSQL** installed and running
- A valid **OpenAI API Key**

### 2. Clone the Repository
```bash
git clone https://github.com/bdstar/AI-Agent-Chatbot-Support-Assistant.git
cd AI-Agent-Chatbot-Support-Assistant
```

### 3. Setup Virtual Environment & Install Dependencies
```bash
python -m venv env
# Activate the environment
# Windows:
.\env\Scripts\activate
# Mac/Linux:
source env/bin/activate

# Install required libraries
pip install -r requirements.txt
```

### 4. Configure the Database
Create a PostgreSQL database named `support_agent` with password `123` (or update credentials in `.env` to match your local setup). The database tables will be auto-generated upon startup.

### 5. Configure Environment Variables
Create a `.env` file in the root directory (if not present) and add your details:
```env
OPENAI_API_KEY=your-actual-api-key
DB_NAME=support_agent
DB_USER=postgres
DB_PASSWORD=123
DB_HOST=localhost
DB_PORT=5432
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

### 6. Run the Application
Start the FastAPI server using Uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```

### 7. Access the Application
1. Open your web browser and navigate to **http://localhost:8000**
2. **First Step:** Place your life insurance documents inside the `Documents/` folder.
3. Click the **"Ingest Documents"** button located at the bottom of the left sidebar to embed the documents into ChromaDB.
4. Start chatting!
