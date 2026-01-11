# Requirement Gathering Agent (SRS Agent)

The **Requirement Gathering Agent** is an AI-powered FastAPI application designed to streamline the software requirement gathering process. It uses LLMs to interact with users, understand project needs, generate Software Requirement Specifications (SRS), provide project estimations, and create branding profiles.

## 🚀 Key Features

- **AI-Driven Chat**: Conversational interface to collect project requirements.
- **Branding Agent**: Conducts interviews to build a comprehensive company branding profile.
- **SRS Generation**: Automatically generates structured Software Requirement Specifications.
- **Project Estimation**: Provides estimated pages, features, and timelines for projects.
- **Prompt Generation**: Creates tailored prompts for Developers, Designers, and Copywriters based on gathered requirements.
- **Export Capabilities**: Export gathered data and generated reports to **XLSX** and **JSON** formats.
- **JWT Authentication**: Secure user management and protected API endpoints.

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy](https://www.sqlalchemy.org/)
- **Cache/Session**: [Redis](https://redis.io/)
- **AI Engine**: [OpenRouter API](https://openrouter.ai/) (GPT models = openai/gpt-oss-120b:free )
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Async Processing**: Python `asyncio`

## 📂 Project Structure

```text
├── app/
│   ├── agent/             # AI Agent logic (Branding, Estimation, Prompt Gen)
│   ├── api/               # API routes (Chat, Export, Auth, etc.)
│   ├── models/            # SQLAlchemy Database models
│   ├── schemas/           # Pydantic data schemas
│   ├── services/          # Business logic and external service integrations
│   ├── utils/             # Helper functions
│   ├── config.py          # Configuration and Environment settings
│   ├── database.py        # Database connection setup
│   └── main.py            # Application entry point
├── exports_*/             # Directories for generated JSON and XLSX files
├── requirements.txt       # Project dependencies
└── .env                   # Environment variables (not tracked by git)
```

## ⚙️ Setup & Installation

### 1. Prerequisite

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
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the `app/` directory (or root, depending on your setup) based on the following template:

```env
openai/gpt-oss-120b:free# App
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
OPENROUTER_MODEL=openai/gpt-3.5-turbo # or any other model
```

### 4. Running the Application

#### Docker setup

```bash
docker run -d \
  --name redis-ai \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7



docker run -d `
  --name redis-ai `
  -p 6379:6379 `
  -v redis-data:/data `
  redis:7
```

```bash
docker start redis-ai
```

#### App start

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
Documentation can be accessed at `http://localhost:8000/docs`.

## 🛣️ API Endpoints

- **Auth**: `/auth/login`, `/auth/refresh` - JWT management.
- **User Register:** /users - User management
- **Step 1:**
  - **Branding**: `/branding/chat` - Interact with the branding agent.
- **Step 2:**
  - **Chat**: `/chat` - Interact with the requirement gathering agent.
- **Step 3:**
  - **Estimation**: `/estimation` - Generate project estimations.
- **Step 4:**
  - **Prompts**: `/gen-prompts` - Generate developer/designer prompts.
- **Export**: `/export` - Download data in XLSX or JSON.(Need superuser auth)
