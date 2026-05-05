FROM node:22-alpine AS web

WORKDIR /app

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN corepack enable && corepack prepare pnpm@9.12.0 --activate && pnpm install --frozen-lockfile

COPY apps/web apps/web
RUN pnpm --filter @youziloadlab/web build

FROM python:3.12-slim AS api

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV DATA_DIR=/data
ENV RUNNER_WORKDIR=/data/runs
ENV DATABASE_URL=sqlite:////data/youziloadlab.db

COPY pyproject.toml README.md ./
COPY apps/api apps/api
COPY runner runner
RUN pip install --no-cache-dir -e .

COPY --from=web /app/apps/web/dist apps/api/youziloadlab_api/static

EXPOSE 8000

CMD ["uvicorn", "youziloadlab_api.main:app", "--app-dir", "apps/api", "--host", "0.0.0.0", "--port", "8000"]
