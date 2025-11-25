# Project Overview

This project is a web-based application that generates multiple-choice questions from a text file. It uses a Retrieval Augmented Generation (RAG) approach with the LangChain library and provides a simple, interactive user interface built with Streamlit.

## How it Works

1.  **Web UI:** The application is run as a web service using Streamlit, providing a user-friendly interface for generating questions.
2.  **Ingestion & Caching:** On startup, it reads a text file (`output.md`), splits it into chunks, and creates embeddings using a Hugging Face model (`sentence-transformers/all-mpnet-base-v2`). The resulting FAISS vector database is cached in memory for fast access.
3.  **User Query:** The user enters a topic into a text field in the web UI.
4.  **Similarity Search:** When the user submits the topic, the application performs a similarity search in the FAISS database to find relevant text chunks.
5.  **Question Generation:** The relevant chunks are passed to the Google Gemini 1.5 Flash model to generate a list of multiple-choice questions.
6.  **Display Results:** The generated questions are displayed in the UI in a clean JSON format. The user can also view the source text chunks used for generation.

## Key Technologies

*   **Python:** The core language of the project.
*   **Streamlit:** Used to create the web-based user interface for the application.
*   **LangChain:** A framework for developing applications powered by language models.
*   **FAISS:** A library for efficient similarity search and clustering of dense vectors.
*   **Hugging Face Transformers:** Used for text embeddings.
*   **Google Gemini:** The language model used for question generation.

# Building and Running

1.  **Prerequisites:**
    *   Python 3.x
    *   An `.env` file with `GOOGLE_API_KEY` and `HUGGINGFACEHUB_API_TOKEN`

2.  **Installation:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Running the Application:**
    ```bash
    streamlit run app.py
    ```
    After running the command, open your web browser and navigate to the local URL provided by Streamlit.

# Development Conventions

*   All application logic is contained within a single script, `app.py`, for simplicity.
*   Dependencies are managed in `requirements.txt`.
*   API keys and secrets are loaded from an `.env` file for security.
*   Streamlit's caching (`st.cache_resource`) is used to prevent re-loading models and data on every interaction, improving performance.
