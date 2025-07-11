# WallStr.chat

## Installation

1. Install [pnpm](https://pnpm.io/installation#using-npm)
2. Install [poetry](https://python-poetry.org/docs/#installation)
3. Install dependencies
   ```bash
   pnpm install
   poetry install -C packages/backend
   ```

## Running locally

1. Backend, check [backend/README.md](packages/backend/README.md) for more information

   ```bash
   pnpm docker-compose

   pnpm backend:dev
   pnpm backend:worker -p 1
   pnpm backend:worker:heavy -p 1
   ```

2. Frontend (setup `packages/frontend/.env` file first)

   ```bash
   pnpm frontend:dev
   ```

3. Open http://localhost:3000
