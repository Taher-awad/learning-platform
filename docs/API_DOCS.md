# API Documentation

Base URL: `http://localhost`

## 1. Document Service

### Upload Document
**Endpoint**: `POST /api/documents/upload`
**Content-Type**: `multipart/form-data`

**Body**:
- `file`: The document file (PDF, DOCX, TXT)

**Example (cURL)**:
```bash
curl -X POST http://localhost/api/documents/upload \
  -F "file=@/path/to/document.pdf"
```

**Response**:
```json
{
  "id": "uuid",
  "message": "Document uploaded and processing started"
}
```

---

## 2. Chat Service

### Send Message
**Endpoint**: `POST /api/chat/message`
**Content-Type**: `application/json`

**Body**:
```json
{
  "user_id": "string",
  "message": "string",
  "context_id": "optional_document_id"
}
```

**Example (cURL)**:
```bash
curl -X POST http://localhost/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "message": "Explain the document"}'
```

**Response**:
```json
{
  "response": "AI generated response..."
}
```

---

## 3. Quiz Service

### Generate Quiz
**Endpoint**: `POST /api/quiz/generate`
**Content-Type**: `application/json`

**Body**:
```json
{
  "document_id": "string",
  "text_content": "string (optional, for direct generation)"
}
```

**Example (cURL)**:
```bash
curl -X POST http://localhost/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"text_content": "Python is a programming language..."}'
```

**Response**:
```json
{
  "quiz": "Generated quiz content..."
}
```

---

## 4. TTS Service (Text-to-Speech)

### Synthesize Audio
**Endpoint**: `POST /api/tts/synthesize`
**Content-Type**: `application/json`

**Body**:
```json
{
  "text": "string"
}
```

**Example (cURL)**:
```bash
curl -X POST http://localhost/api/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'
```

**Response**:
```json
{
  "message": "TTS request submitted",
  "request_id": "uuid"
}
```

---

## 5. STT Service (Speech-to-Text)

### Transcribe Audio
**Endpoint**: `POST /api/stt/transcribe`
**Content-Type**: `multipart/form-data`

**Body**:
- `file`: The audio file (WAV, MP3)

**Example (cURL)**:
```bash
curl -X POST http://localhost/api/stt/transcribe \
  -F "file=@/path/to/audio.wav"
```

**Response**:
```json
{
  "id": "uuid",
  "text": "Transcribed text..."
}
```
