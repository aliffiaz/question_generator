# MCQ Generator API Documentation

Base URL: `http://localhost:8000`

## 1. Ingest Document
Uploads a file (PDF, Markdown, Text) and ingests it into the vector database with metadata.

- **Endpoint**: `/ingest`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`

### Parameters
| Field | Type | Description |
| :--- | :--- | :--- |
| `file` | File | The document file to upload (PDF, .md, .txt). |
| `standard` | String | The standard/grade (e.g., "10"). |
| `subject` | String | The subject (e.g., "Science"). |
| `chapter_number` | String | The chapter number (e.g., "1"). |
| `chapter_name` | String | The name of the chapter (e.g., "Gravitation"). |
| `syllabus` | String | The syllabus (e.g., "CBSE"). |

### Response
```json
{
  "status": "success",
  "message": "Successfully uploaded and ingested.",
  "file": "filename.pdf"
}
```

---

## 2. Generate Questions
Generates multiple-choice questions based on a topic and metadata filters.

- **Endpoint**: `/generate`
- **Method**: `POST`
- **Content-Type**: `application/json`

### Request Body
```json
{
  "query": "Explain Newton's laws",
  "standard": "10",
  "subject": "Science",
  "chapter_name": "Gravitation"
}
```
*Note: At least one metadata filter (`standard`, `subject`, or `chapter_name`) must be provided.*

### Response
```json
{
  "status": "success",
  "questions": [
    {
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "answer": "...",
      "explanation": "...",
      "topic": "...",
      "subject": "..."
    }
  ]
}
```

## Interactive Documentation
Once the server is running, you can access the interactive Swagger UI at:
[http://localhost:8000/docs](http://localhost:8000/docs)
