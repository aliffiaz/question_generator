import streamlit as st
import json
import os
from dotenv import load_dotenv
from helper import get_vectorstore, get_question_and_answers, get_metadata

# Load environment variables
load_dotenv()

# Streamlit App
st.set_page_config(page_title="MCQ Generator", layout="wide")
st.title("Multiple-Choice Question Generator")

st.write("This app generates multiple-choice questions based on a topic you provide. Select the content source using the filters below.")

# Metadata Selection
metadata_list = get_metadata()

if not metadata_list:
    st.warning("No metadata found. Please upload files via the 'Upload Textbook Chapter' page.")
    st.stop()

# Cascading Dropdowns
# 1. Standard
standards = sorted(list(set([item.get("standard", "") for item in metadata_list if item.get("standard")])))
selected_standard = st.selectbox("Select Standard:", [""] + standards)

# 2. Subject (filtered by Standard)
if selected_standard:
    subjects = sorted(list(set([item.get("subject", "") for item in metadata_list if item.get("standard") == selected_standard])))
    selected_subject = st.selectbox("Select Subject:", [""] + subjects)
else:
    selected_subject = st.selectbox("Select Subject:", [""])

# 3. Chapter (filtered by Standard and Subject)
if selected_standard and selected_subject:
    chapters = sorted(list(set([item.get("chapter_name", "") for item in metadata_list if item.get("standard") == selected_standard and item.get("subject") == selected_subject])))
    selected_chapter = st.selectbox("Select Chapter:", [""] + chapters)
else:
    selected_chapter = st.selectbox("Select Chapter:", [""])

# Determine filter
metadata_filter = {}
if selected_standard and selected_subject and selected_chapter:
    metadata_filter = {
        "standard": selected_standard,
        "subject": selected_subject,
        "chapter_name": selected_chapter
    }
    st.success(f"Selected: {selected_standard} > {selected_subject} > {selected_chapter}")
elif selected_standard or selected_subject:
     st.info("Please select all fields to narrow down to a specific chapter.")

# Initialize Vector Store
try:
    vector_store = get_vectorstore()
except Exception as e:
    st.error(f"Failed to connect to Pinecone: {e}")
    st.stop()

# User input
query = st.text_input("Enter your topic:", "")

if st.button("Generate Questions"):
    if query and metadata_filter:
        with st.spinner("Generating questions..."):
            # Pass metadata_filter
            response, docs = get_question_and_answers(vector_store, query=query, metadata_filter=metadata_filter)

            if response == "NO_RELEVANT_CONTENT":
                st.warning("No relevant content found for your query.")
            else:
                try:
                    content = response.content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    
                    data = json.loads(content.strip())
                    st.success("Generated Questions:")
                    st.json(data)

                    with st.expander("Show relevant text chunks"):
                        for doc in docs:
                            st.write(doc.page_content)
                            st.write("---")

                except json.JSONDecodeError:
                    st.error("Failed to decode the response from the model.")
                    st.write("Raw response:")
                    st.code(response.content)
    elif not metadata_filter:
        st.warning("Please select Standard, Subject, and Chapter.")
    else:
        st.warning("Please enter a topic.")
