# AI Retail Analytics Backend

An AI-powered backend for querying retail warehouse data through **natural-language and voice interfaces**.

Built with **FastAPI**, the system combines LLM-based agent orchestration, schema-aware text-to-SQL generation, ClickHouse data access, and speech-to-text processing into a unified analytics workflow.

The project was developed during my AI Engineering internship at **Revest** and focuses on backend architecture, asynchronous AI workflows, database integration, and LLM-powered analytics.

---

## Overview

Traditional retail analytics often requires users to understand database schemas and write SQL queries manually.

This backend allows users to ask questions in natural language, such as:

* What are the best-selling products?
* Which stores generated the highest revenue?
* How did sales perform during a specific period?
* What categories contributed most to total sales?

The backend converts these questions into SQL using an LLM agent, executes the generated queries against **ClickHouse**, and returns the resulting analytics data.

The same workflow also supports **voice input**, where uploaded audio is first transcribed using **Mistral Voxtral** before being processed by the analytics agent.

---

## Key Features

### FastAPI Backend

* RESTful endpoints built with FastAPI
* Typed request and response models using Pydantic
* Automatic OpenAPI/Swagger documentation
* Input validation and structured API responses
* HTTP exception and error handling
* CORS configuration for frontend integration
* Service-status endpoint

### LLM Agent Orchestration

* Agentic workflows built using **Agno**
* Integration with **OpenAI gpt-oss**
* Tool-based SQL execution
* Prompt orchestration for database analytics
* Asynchronous LLM execution using Python `async/await`

### Schema-Aware Text-to-SQL

The agent dynamically receives the current ClickHouse database schema before generating SQL.

This allows the model to understand:

* available tables
* available columns
* database structure
* relevant context for SQL generation

The generated SQL is then executed through an agent tool against ClickHouse.

### Voice Query Support

The backend also accepts audio queries.

Uploaded audio is:

1. Read asynchronously by the FastAPI service.
2. Sent to **Mistral Voxtral** for speech-to-text transcription.
3. Converted into a natural-language query.
4. Passed through the same text-to-SQL agent pipeline.
5. Executed against ClickHouse.
6. Returned as structured analytics results.

### Backend Performance & Reliability

The service includes several backend optimizations:

* asynchronous request handling
* lazy LLM agent initialization
* cached ClickHouse client creation
* cached database schema discovery using `lru_cache`
* environment-based configuration using Pydantic settings
* structured exception handling
* reusable database and agent components

---

## System Architecture

```text
                         ┌──────────────────────┐
                         │        Client        │
                         │  Frontend / Swagger  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │                      │
                         │ Validation           │
                         │ Pydantic Models      │
                         │ Error Handling       │
                         │ CORS                 │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
          ┌──────────────────┐            ┌──────────────────┐
          │    Text Query    │            │   Voice Query    │
          └────────┬─────────┘            └────────┬─────────┘
                   │                               │
                   │                               ▼
                   │                    ┌──────────────────────┐
                   │                    │   Mistral Voxtral    │
                   │                    │   Speech-to-Text     │
                   │                    └──────────┬───────────┘
                   │                               │
                   └───────────────┬───────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │     Agno Agent       │
                         │   OpenAI gpt-oss     │
                         └──────────┬───────────┘
                                    │
                                    │ Schema Context
                                    ▼
                         ┌──────────────────────┐
                         │     Text-to-SQL      │
                         │     Generation       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   SQL Agent Tool     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      ClickHouse      │
                         │  Retail Warehouse    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Analytics Response   │
                         └──────────────────────┘
```

---

## Request Workflows

### Natural-Language Query

```text
User Question
      ↓
FastAPI /text-query
      ↓
Pydantic Validation
      ↓
Load ClickHouse Schema
      ↓
Agno LLM Agent
      ↓
Schema-Aware SQL Generation
      ↓
SQL Execution Tool
      ↓
ClickHouse
      ↓
Structured Analytics Response
```

### Voice Query

```text
Audio Upload
      ↓
FastAPI /voice-query
      ↓
Async File Processing
      ↓
Mistral Voxtral
      ↓
Speech-to-Text
      ↓
Natural-Language Query
      ↓
Agno LLM Agent
      ↓
Text-to-SQL
      ↓
ClickHouse
      ↓
Structured Analytics Response
```

---

## Tech Stack

| Area                    | Technology                               |
| ----------------------- | ---------------------------------------- |
| Backend                 | Python, FastAPI                          |
| API Models & Validation | Pydantic                                 |
| Async Processing        | Python `async/await`                     |
| Agent Framework         | Agno                                     |
| LLM                     | OpenAI gpt-oss                           |
| Speech-to-Text          | Mistral Voxtral                          |
| Analytics Database      | ClickHouse                               |
| Query Generation        | LLM-based Text-to-SQL                    |
| API Documentation       | OpenAPI / Swagger                        |
| Server                  | Uvicorn                                  |
| Configuration           | Environment variables, Pydantic Settings |
| Integration             | REST APIs, CORS                          |

---

## API Endpoints

### `GET /`

Service-status endpoint used to verify that the backend is running.

### `POST /text-query`

Processes a natural-language retail analytics question.

The backend:

1. validates the request,
2. loads the ClickHouse schema,
3. sends schema context and the question to the LLM agent,
4. generates and executes SQL,
5. returns the analytics result.

### `POST /voice-query`

Processes an uploaded voice query.

The backend:

1. asynchronously reads the audio file,
2. transcribes it using Mistral Voxtral,
3. sends the transcription through the text-to-SQL agent,
4. executes the resulting query,
5. returns the analytics result.

---

## Interactive API Documentation

FastAPI automatically generates interactive API documentation.

After starting the backend, open:

```text
/docs
```

The Swagger interface can be used to inspect the API models and test the available endpoints directly.

---

## Getting Started

### Prerequisites

You will need:

* Python
* access to a ClickHouse database
* credentials for the configured LLM service
* Mistral credentials for voice transcription

---

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AI_Retail_Analytics_Backend
```

### 2. Create a Virtual Environment

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Configure the credentials and connection settings required by the application, including:

* LLM API credentials
* Mistral API credentials
* ClickHouse host and connection information
* ClickHouse database credentials

The backend loads configuration through Pydantic settings rather than hardcoding credentials into the application.

### 5. Start the Backend

```bash
uvicorn main:app --reload
```

The service will start locally through Uvicorn.

Use the generated `/docs` endpoint to explore and test the API.

---

## Backend Design

### Dynamic Schema Discovery

Rather than hardcoding the retail warehouse schema into the LLM prompt, the application retrieves schema information from ClickHouse.

This schema is supplied to the agent as context before SQL generation.

This design makes the text-to-SQL workflow more adaptable to changes in the underlying database structure.

### Tool-Based Database Access

The LLM does not directly access the database.

Instead, database query execution is exposed to the agent through controlled tools.

The workflow separates:

```text
Natural-Language Understanding
        ↓
SQL Generation
        ↓
Tool Invocation
        ↓
Database Execution
```

This provides a clearer separation between model reasoning and application-level database access.

### Cached Database Resources

Database resources that do not need to be rebuilt for every request are cached.

The application uses `lru_cache` for components such as:

* ClickHouse client initialization
* database schema retrieval

This avoids unnecessary repeated initialization during request processing.

### Lazy Agent Initialization

The LLM agent is initialized only when it is needed rather than being recreated for every API request.

This reduces unnecessary initialization overhead and keeps agent configuration centralized.

### Asynchronous AI Workflows

The backend uses Python `async/await` for asynchronous operations, including AI-agent execution and file processing.

This prevents long-running external AI calls from unnecessarily blocking the application workflow.

---

## What This Project Demonstrates

This project focuses on the backend engineering required to integrate LLMs into real applications, including:

* designing RESTful AI services
* building asynchronous Python workflows
* integrating external LLM and speech services
* orchestrating LLM agents and tools
* connecting model inference with databases
* implementing schema-aware text-to-SQL
* designing typed API contracts
* handling API validation and errors
* integrating backend services with frontend applications
* managing application configuration
* optimizing reusable backend resources through caching

---

## Project Context

This project was developed during my **AI Engineering internship at Revest** as part of my work with LLM agents, backend services, model inference, database integrations, and agentic AI workflows.

The repository demonstrates the backend implementation of an AI-powered retail analytics system capable of processing both text and voice requests.

---

## Author

**Tasneem Dweiri**
AI Backend Engineer
B.S. Artificial Intelligence — University of Jordan
