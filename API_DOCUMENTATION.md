# MCQ Generator Service API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8000`

## Overview
The MCQ Generator Service provides a RESTful API to ingest educational content (textbooks, chapters) and generate multiple-choice questions (MCQs) based on that content using Retrieval-Augmented Generation (RAG). This service is designed to be consumed by external applications (web frontends, mobile apps, etc.).

## Authentication
Currently, the API is open and does not require authentication. Ensure the service is deployed in a secure environment or behind a gateway if public access is not intended.

## Error Handling
The API uses standard HTTP status codes to indicate the success or failure of a request.

| Status Code | Description |
| :--- | :--- |
| `200 OK` | The request was successful. |
| `400 Bad Request` | The request was invalid (e.g., missing parameters). |
| `422 Unprocessable Entity` | Validation error (e.g., wrong data type). |
| `500 Internal Server Error` | An unexpected error occurred on the server. |
| `503 Service Unavailable` | The vector store or LLM service is unavailable. |

---

## Endpoints

### 1. Ingest Document
Uploads a document (PDF, Markdown, or Text) and indexes it into the vector database. This endpoint also stores metadata associated with the document for filtering during generation.

- **URL**: `/ingest`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`

#### Request Parameters
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `file` | File | Yes | The document file to upload. Supported formats: `.pdf`, `.md`, `.txt`. |
| `standard` | String | Yes | The educational standard or grade level (e.g., "10", "12", "Undergraduate"). |
| `subject` | String | Yes | The subject matter (e.g., "Physics", "History"). |
| `syllabus` | String | Yes | The syllabus or curriculum board (e.g., "CBSE", "ICSE", "Common Core"). |
| `chapter_number` | String | Yes | The chapter number (e.g., "1", "5.2"). |
| `chapter_name` | String | Yes | The title of the chapter (e.g., "Thermodynamics"). |

#### Example Request (cURL)
```bash
curl -X 'POST' \
  'http://localhost:8000/ingest' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@chapter1_forces.pdf;type=application/pdf' \
  -F 'standard=10' \
  -F 'subject=Physics' \
  -F 'syllabus=CBSE' \
  -F 'chapter_number=1' \
  -F 'chapter_name=Forces and Motion'
```

#### Success Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Successfully uploaded and ingested.",
  "file": "chapter1_forces.pdf"
}
```

#### Error Response (`500 Internal Server Error`)
```json
{
  "detail": "Error ingesting file: [Error details]"
}
```

---

### 2. Generate Questions
Generates a set of multiple-choice questions based on a user query and specific metadata filters. The service retrieves relevant context from the ingested documents matching the filters.

- **URL**: `/generate`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### Request Body
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `query` | String | Yes | The topic or concept to generate questions for (e.g., "Newton's Laws"). |
| `standard` | String | No* | Filter by standard. |
| `subject` | String | No* | Filter by subject. |
| `chapter_name` | String | No* | Filter by chapter name. |

*\*Note: At least one metadata filter (`standard`, `subject`, or `chapter_name`) MUST be provided to narrow down the context.*

#### Example Request
```json
{
  "query": "Explain Newton's Second Law",
  "standard": "10",
  "subject": "Physics",
  "chapter_name": "Forces and Motion"
}
```

#### Success Response (`200 OK`)
Returns a JSON object containing a list of generated questions.

```json
{
  "status": "success",
  "questions": [
    {
      "question": "What is the mathematical formulation of Newton's Second Law?",
      "options": [
        "F = m/a",
        "F = ma",
        "F = m + a",
        "F = a/m"
      ],
      "answer": "F = ma",
      "explanation": "Newton's Second Law states that Force equals mass times acceleration.",
      "topic": "Newton's Laws",
      "subject": "Physics"
    },
    {
      "question": "...",
      "options": ["..."],
      "answer": "...",
      "explanation": "...",
      "topic": "...",
      "subject": "..."
    }
  ]
}
```

#### No Content Response (`200 OK`)
Returned when no relevant documents are found matching the query and filters.
```json
{
  "status": "no_content",
  "message": "No relevant content found for your query."
}
```

#### Error Response (`500 Internal Server Error`)
```json
{
  "detail": "Failed to parse model response"
}
```

---

## Interactive Documentation (Swagger UI)
The service provides an auto-generated interactive API documentation page where you can test endpoints directly.

- **URL**: `http://localhost:8000/docs`
