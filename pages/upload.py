import streamlit as st
import os
import sys

# Add parent directory to path to import ingest_file
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest import ingest_file

st.set_page_config(page_title="Upload Textbook Chapter", layout="wide")
st.title("Upload Textbook Chapter")

st.write("Upload a chapter (PDF, Markdown, or Text) and provide metadata for better organization.")

# File Uploader
uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'md', 'txt'])

# Metadata Inputs
col1, col2 = st.columns(2)

with col1:
    standard = st.text_input("Standard (e.g., 10, 12)", "")
    subject = st.text_input("Subject (e.g., Mathematics, Physics)", "")
    syllabus = st.text_input("Syllabus (e.g., CBSE, ICSE)", "")

with col2:
    chapter_number = st.text_input("Chapter Number", "")
    chapter_name = st.text_input("Chapter Name", "")

if st.button("Upload and Ingest"):
    if uploaded_file and standard and subject and chapter_number and chapter_name and syllabus:
        
        # Save file temporarily
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        file_path = os.path.join(data_dir, uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.info(f"File saved to {file_path}. Starting ingestion...")
        
        # Construct metadata
        metadata = {
            "standard": standard,
            "subject": subject,
            "syllabus": syllabus,
            "chapter_number": chapter_number,
            "chapter_name": chapter_name
        }
        
        with st.spinner("Ingesting into Pinecone... This may take a while for PDFs."):
            success, message = ingest_file(file_path, metadata)
            
            if success:
                st.success(message)
            else:
                st.error(f"Ingestion failed: {message}")
                
    else:
        st.warning("Please upload a file and fill in all metadata fields.")
