# AI For Education - Backend

Building a POC for Students with AI-powered document summarization.

## Project Structure

```
back_end/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # MongoDB configuration
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user_schema.py      # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   └── user_services.py    # FastAPI endpoints
│   └── utils/
│       ├── __init__.py
│       └── helper.py            # Helper functions
├── requirements.txt
└── README.md
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd back_end
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the `back_end` directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
MONGO_URI=mongodb://localhost:27017/
```

### 3. Start MongoDB

Make sure MongoDB is running on your system:

```bash
# On Linux/Mac
sudo systemctl start mongod

# Or using Docker
docker run -d -p 27017:27017 --name mongodb mongo
```

### 4. Run the Application

```bash
# From the back_end directory
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /` - Root endpoint with API info
- `GET /health` - Health check
- `POST /signup` - User registration
- `POST /login` - User login
- `POST /upload` - Upload and summarize documents

## Features

- User authentication (signup/login)
- Document upload (PDF, DOCX, TXT, CSV)
- AI-powered document summarization
- RAG-based summarization for large documents
- Vector embeddings for semantic search

## Technology Stack

- **FastAPI** - Modern web framework
- **MongoDB** - NoSQL database
- **OpenAI** - AI/ML capabilities
- **PyPDF2 & python-docx** - Document processing
- **NumPy** - Vector operations
