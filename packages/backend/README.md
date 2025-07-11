# WallStr Backend

FastAPI, Dramatiq, PostgreSQL, Redis, Weaviate, RabbitMQ

## Installation

1. Install [poetry](https://python-poetry.org/docs/#installation)
2. Install dependencies
   ```bash
   # MacOS
   brew install libheif qpdf poppler
   # or
   sudo apt-get libheif-dev qpdf poppler-utils
   # or whatever package manager you use
   ```
3. `poetry install`

## Running locally

1. `docker-compose up`
2. Download Ollama models (optional)
   ```bash
   docker exec -it wallstr_ollama /bin/ollama pull llama3.2
   docker exec -it wallstr_ollama /bin/ollama pull nomic-embed-text
   ```
3. Copy `.env.example` to `.env` and set corresponding variables, check comments in `.env.example` for more information
4. Do database migrations
   ```bash
   task migrate
   task migrate_weaviate
   ```
5. `task dev` - api
6. `task worker -p 1` - main worker
7. `task worker:heavy -p 1` - heavy load worker

## Default endpoints

- http://localhost:8000/docs - OpenAPI UI
- http://localhost:8000/redoc - ReDoc
- http://localhost:15672 - RabbitMQ Management UI
- http://localhost:8001 - RedisInsight (Redis Management UI)
- http://localhost:9001 - MinIO UI
