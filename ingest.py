import os
import time
import nest_asyncio
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from llama_parse import LlamaParse
from langchain_core.documents import Document

# Apply nest_asyncio to allow nested event loops (needed for LlamaParse in some envs)
nest_asyncio.apply()

# Load environment variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

if not PINECONE_API_KEY or not PINECONE_INDEX_NAME:
    print("Error: PINECONE_API_KEY and PINECONE_INDEX_NAME must be set in .env")
    exit(1)

if not LLAMA_CLOUD_API_KEY:
    print("Error: LLAMA_CLOUD_API_KEY must be set in .env for PDF parsing")
    exit(1)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Check if index exists, if not create it (optional, but good for setup)
existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

if PINECONE_INDEX_NAME not in existing_indexes:
    print(f"Index '{PINECONE_INDEX_NAME}' not found. Creating it...")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=768, # Dimension for sentence-transformers/all-mpnet-base-v2
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
    while not pc.describe_index(PINECONE_INDEX_NAME).status['ready']:
        time.sleep(1)
    print(f"Index '{PINECONE_INDEX_NAME}' created.")
else:
    # Check if the existing index has the correct dimension
    index_description = pc.describe_index(PINECONE_INDEX_NAME)
    if index_description.dimension != 768:
        print(f"Index '{PINECONE_INDEX_NAME}' has dimension {index_description.dimension}, but model requires 768. Deleting and recreating...")
        pc.delete_index(PINECONE_INDEX_NAME)
        
        # Wait for deletion to propagate (optional but recommended)
        time.sleep(5)
        
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=768, # Dimension for sentence-transformers/all-mpnet-base-v2
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        while not pc.describe_index(PINECONE_INDEX_NAME).status['ready']:
            time.sleep(1)
        print(f"Index '{PINECONE_INDEX_NAME}' recreated with correct dimension.")

index = pc.Index(PINECONE_INDEX_NAME)

# Load embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

import json

# ... (imports remain the same)

# ... (setup remains the same)

def update_metadata_json(file_path: str, metadata: dict):
    """Updates the metadata.json file with the new file's metadata."""
    data_dir = os.path.dirname(file_path)
    json_path = os.path.join(data_dir, "metadata.json")
    
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    
    # Check if file already exists in metadata list, update if so
    file_name = os.path.basename(file_path)
    entry = {"file_name": file_name, **metadata}
    
    # Remove existing entry for this file if present
    data = [item for item in data if item.get("file_name") != file_name]
    
    data.append(entry)
    
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

def ingest_file(file_path: str, metadata: dict = None):
    """Ingests a single file into Pinecone with optional metadata."""
    if metadata is None:
        metadata = {}

    vector_store = PineconeVectorStore(index=index, embedding=embeddings)
    
    # Check if file already exists in Pinecone (using source filter)
    dummy_vector = [0.0] * 768 
    results = index.query(
        vector=dummy_vector,
        top_k=1,
        filter={"source": file_path},
        include_metadata=False
    )

    if results['matches']:
        print(f"Skipping {file_path}: Already exists in index.")
        # Even if we skip ingestion, we should ensure metadata.json is up to date
        update_metadata_json(file_path, metadata)
        return False, "File already exists in index."

    print(f"Processing {file_path}...")
    documents = []

    try:
        if file_path.endswith('.pdf'):
            print(f"  - Parsing PDF with LlamaParse...")
            parser = LlamaParse(
                result_type="markdown",
                api_key=LLAMA_CLOUD_API_KEY
            )
            parsed_docs = parser.load_data(file_path)
            full_text = "\n\n".join([doc.text for doc in parsed_docs])
            documents = [Document(page_content=full_text, metadata={"source": file_path})]
            
        else:
            loader = TextLoader(file_path, encoding='utf-8', autodetect_encoding=True)
            documents = loader.load()
            for doc in documents:
                doc.metadata["source"] = file_path

        # Merge provided metadata
        for doc in documents:
            doc.metadata.update(metadata)

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = splitter.split_documents(documents)

        print(f"  - Split into {len(docs)} chunks. Uploading...")
        vector_store.add_documents(docs)
        print(f"  - Uploaded {file_path}.")
        
        # Update metadata.json
        update_metadata_json(file_path, metadata)
        
        return True, "Successfully uploaded and ingested."

    except Exception as e:
        print(f"Error ingesting {file_path}: {e}")
        return False, str(e)


def ingest_files(data_dir="data"):
    if not os.path.exists(data_dir):
        print(f"Directory {data_dir} not found.")
        return

    files = [f for f in os.listdir(data_dir) if f.endswith(('.md', '.txt', '.pdf'))]

    if not files:
        print(f"No files found in {data_dir}.")
        return

    # Load existing metadata
    json_path = os.path.join(data_dir, "metadata.json")
    existing_metadata = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                meta_list = json.load(f)
                # Create a lookup dict by filename
                for item in meta_list:
                    if "file_name" in item:
                        existing_metadata[item["file_name"]] = item
        except json.JSONDecodeError:
            print("Warning: Could not decode metadata.json")

    for file in files:
        file_path = os.path.join(data_dir, file)
        
        # Get metadata for this file if it exists
        metadata = existing_metadata.get(file, {})
        # Remove file_name from metadata dict as it's not needed in the vector metadata
        if "file_name" in metadata:
            del metadata["file_name"]
            
        ingest_file(file_path, metadata)

if __name__ == "__main__":
    ingest_files()
