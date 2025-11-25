import sys
import json
import os
import argparse
from helper import get_vectorstore, get_question_and_answers

def main():
    parser = argparse.ArgumentParser(description="Generate MCQs from a text file.")
    parser.add_argument("topic", help="The topic to generate questions for.")
    parser.add_argument("--file", help="Path to the source text file.", default=None)
    args = parser.parse_args()

    query = args.topic
    file_path = args.file

    if not file_path:
        # Try to find a default file in data/
        data_dir = "data"
        if os.path.exists(data_dir):
            files = [f for f in os.listdir(data_dir) if f.endswith(('.md', '.txt'))]
            if files:
                file_path = os.path.join(data_dir, files[0])
                print(f"No file specified. Using default: {file_path}")
            else:
                print(f"No files found in {data_dir}. Please specify a file using --file.")
                return
        else:
            print(f"Directory {data_dir} not found. Please specify a file using --file.")
            return

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        vector_store = get_vectorstore()
    except Exception as e:
        print(f"Failed to connect to Pinecone: {e}")
        return

    response, docs = get_question_and_answers(vector_store, query=query, file_path=file_path)

    if response == "NO_RELEVANT_CONTENT":
        print("No relevant content found for your query.")
        return

    try:
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        data = json.loads(content.strip())
        print(json.dumps(data, indent=2))

    except json.JSONDecodeError:
        print("Failed to decode JSON:")
        print(response.content)


if __name__ == "__main__":
    main()
