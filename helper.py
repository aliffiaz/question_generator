import os
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import TextLoader
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

def get_vectorstore():
    """Returns a Pinecone vector store connected to the index."""
    if not PINECONE_API_KEY or not PINECONE_INDEX_NAME:
        raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_NAME must be set in .env")
    
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    vector_store = PineconeVectorStore(index=index, embedding=embeddings)
    return vector_store

def get_metadata():
    """Reads the metadata.json file and returns the list of file metadata."""
    data_dir = "data"
    json_path = os.path.join(data_dir, "metadata.json")
    
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def get_question_and_answers(vector_store, query: str, file_path: str = None, metadata_filter: dict = None, k=4):
    """Generates questions and answers based on a user query and selected file or metadata."""
    
    # Construct filter
    filter_dict = {}
    if file_path:
        filter_dict["source"] = file_path
    elif metadata_filter:
        # Add metadata fields to filter
        # Note: Pinecone metadata filtering is exact match for strings
        filter_dict.update(metadata_filter)
    
    # Create a retriever with metadata filter
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": k,
            "filter": filter_dict
        }
    )
    
    docs = retriever.invoke(query)
    combined = " ".join([d.page_content for d in docs]).strip()

    if not combined:
        return "NO_RELEVANT_CONTENT", docs

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    prompt = PromptTemplate(
        input_variables=["text"],
        template="""
Generate 10 multiple-choice questions (4 options) based ONLY on the following text.

IMPORTANT GUIDELINES:
1. Questions must be SELF-CONTAINED. Do not refer to "the text", "Example 1", "Figure 2", "this chapter", etc.
2. If a question is based on a specific scenario in the text, describe the scenario fully in the question instead of referencing it by name/number.
3. Ensure the explanation is also self-contained and does not say "As mentioned in the text...,The texts states..." and should be detailed.
4. **FORMATTING**:
    - Options should NOT have prefixes like "A)", "B)", etc. Just the option text.
    - The "answer" field must contain the FULL TEXT of the correct option, not just the letter.
5. all the fields in the json are required.
6. The questions must have different complexities (easy,medium,hard)
7. The complexity should one of the following - eady , medium ,hard
8. The options should be short and precise not long sentence 
{text}

Return a JSON array like this:
[
  {{
    "question": "...",
    "options": ["Option text 1", "Option text 2", "Option text 3", "Option text 4"],
    "answer": "Option text 2",
    "explanation": "...",
    "topic": "...",
    "subject":"...",
    "complexity":""
  }}
]
"""

    )

    chain = prompt | llm
    response = chain.invoke({"text": combined})

    return response, docs
