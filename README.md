# Requirement Gathering Agent (SRS Agent)

The **Requirement Gathering Agent** is an AI-powered FastAPI application designed to streamline the software requirement gathering process. It uses LLMs to interact with users, understand project needs, generate Software Requirement Specifications (SRS), provide project estimations, and create branding profiles.

## 🚀 Key Features

- **Multi-Phase AI Interaction**: Guided workflow from branding discovery to technical specification.
- **AI-Driven Chat (REST & WebSocket)**: Real-time conversational interface to collect project requirements with context-aware questioning.
- **Branding Agent**: Conducts interviews to build a comprehensive company profile including brand voice, values, and visual inspiration.
- **Visual Reference Support**: Ability to upload images and provide inspiration URLs to guide the design and requirement gathering.
- **Structured SRS Generation**: Automatically generates detailed specifications including User Roles, Functional/Non-Functional Requirements, Budget, and Constraints.
- **Project Estimation**: Provides data-driven estimations for pages/screens, features, and development timelines.
- **Prompt Engineering**: Creates tailored prompts for Developers, Designers, and Copywriters based on the gathered requirements.
- **Export Capabilities**: Export gathered data and generated reports to **XLSX** and **JSON** formats.
- **JWT Authentication**: Secure user management with protected API endpoints and session-based logic.

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Async, WebSockets)
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy](https://www.sqlalchemy.org/)
- **Cache/Session**: [Redis](https://redis.io/) for session state management
- **AI Engine**: [OpenRouter API](https://openrouter.ai/) (GPT-4o, Claude 3.5, etc.)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **File Handling**: Multipart/form-data for image uploads

## 📂 Project Structure

```text
├── app/
│   ├── agent/             # AI Agent logic (Branding, SRS, Estimation, Prompt Gen)
│   ├── api/               # API routes (Chat, Export, Auth, WebSocket)
│   ├── models/            # SQLAlchemy Database models
│   ├── schemas/           # Pydantic data schemas
│   ├── services/          # Business logic and external service integrations
│   ├── utils/             # Helper functions (Merging, String formatting)
│   ├── config.py          # Configuration and Environment settings
│   ├── database.py        # Database connection setup
│   └── main.py            # Application entry point
├── exports_*/             # Directories for generated JSON, XLSX, and Image files
├── requirements.txt       # Project dependencies
└── .env                   # Environment variables
```

## ⚙️ Setup & Installation

### 1. Prerequisites

- Python 3.10+
- PostgreSQL
- Redis
- OpenRouter API Key

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd srs-agent

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory based on the following template:

```env
# App
APP_NAME="Requirement Gathering Agent"
DEBUG=True

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_TTL_SECONDS=3600

# PostgreSQL
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=srs_db

# JWT Auth
SECRET_KEY=your_super_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-4o # or your preferred model
```

### 4. Running the Application

#### Using Docker for Infrastructure

```bash
# Install redis for linux or mac
docker run -d \
  --name redis-ai \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7

# Install redis for windows
docker run -d `
  --name redis-ai `
  -p 6379:6379 `
  -v redis-data:/data `
  redis:7

```

```bash
# Start Redis
docker run -d --name srs-redis -p 6379:6379 redis:7
```

#### Start FastAPI Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
Swagger docs: `http://localhost:8000/docs`.

## 🔄 Workflow

1. **Auth**: Register/Login to get a JWT token.
2. **Step 1 (Branding)**: Start a session via `/branding/chat` or `/ws/branding/{session_id}`. This gathers company info and brand identity.
3. **Step 2 (Requirements)**: transition to `/chat` or `/ws/chat/{session_id}`. This uses branding data as context to gather detailed software requirements.
4. **Step 3 (Estimation)**: Call `/estimation` to get a structured breakdown of the project.
5. **Step 4 (Prompts)**: Call `/gen-prompts` to generate specific instructions for your creative/technical team.

## 🛣️ Key API Endpoints

### Authentication

- `POST /auth/login`: Authenticate user.
- `POST /auth/refresh`: Refresh token
- `POST /users`: Register a new user.

### Phase 1: Branding Discovery

- `POST /branding/chat`: REST endpoint for branding interview.
- `WS /ws/branding/{session_id}`: Real-time branding interview.

### Phase 2: Requirement Gathering

- `POST /chat`: REST endpoint for SRS gathering (Supports image uploads).
- `WS /ws/chat/{session_id}`: Real-time requirement gathering.

### Phase 3: Deliverables

- `POST /estimation`: Generate features, pages, and timelines.
- `POST /gen-prompts`: Generate tailored prompts for roles.

### Phase 4: Export

- `GET /export`: Download session data (JSON/XLSX). Requires superuser privileges.
